"""Tag API routes - database-backed tag management."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional, List, Tuple, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from genonaut.api.dependencies import get_database_session
from genonaut.api.services.tag_service import TagService
from genonaut.api.models.requests import PaginationRequest
from genonaut.api.models.responses import (
    PaginatedResponse,
    SuccessResponse,
    TagDetailResponse,
    TagHierarchyResponse,
    TagListResponse,
    TagRatingResponse,
    TagRatingValueResponse,
    TagRelationResponse,
    TagResponse,
    TagStatisticsResponse,
    TagSummaryResponse,
    TagUserRatingsResponse,
)
from genonaut.api.exceptions import EntityNotFoundError, ValidationError, DatabaseError
from genonaut.db.schema import Tag

router = APIRouter(prefix="/api/v1/tags", tags=["tags"])


def get_tag_service(db: Session = Depends(get_database_session)) -> TagService:
    """Get TagService instance with database session."""
    return TagService(db)


def _build_tag_summary(tag: Tag) -> TagSummaryResponse:
    return TagSummaryResponse(id=tag.id, name=tag.name)


def _calculate_rating_fields(
    rating_map: Dict[UUID, Tuple[float, int]],
    tag_id: UUID
) -> Tuple[Optional[float], Optional[int]]:
    rating_data = rating_map.get(tag_id)
    if not rating_data:
        return None, None

    avg, count = rating_data
    if count <= 0:
        return None, 0
    return round(float(avg), 2), int(count)


def _build_tag_response(
    tag: Tag,
    *,
    average_rating: Optional[float] = None,
    rating_count: Optional[int] = None,
    is_favorite: Optional[bool] = None,
) -> TagResponse:
    metadata = tag.tag_metadata or {}
    avg_value = round(float(average_rating), 2) if average_rating is not None else None
    return TagResponse(
        id=tag.id,
        name=tag.name,
        metadata=metadata,
        created_at=tag.created_at,
        updated_at=tag.updated_at,
        average_rating=avg_value,
        rating_count=rating_count,
        is_favorite=is_favorite,
    )


def _build_tag_list_response(service: TagService, result: PaginatedResponse) -> TagListResponse:
    tags: List[Tag] = list(result.items)
    rating_map: Dict[UUID, Tuple[float, int]] = {}
    if tags:
        rating_map = service.repository.get_tags_with_ratings([tag.id for tag in tags])

    items = []
    for tag in tags:
        avg_rating, rating_count = _calculate_rating_fields(rating_map, tag.id)
        items.append(
            _build_tag_response(
                tag,
                average_rating=avg_rating,
                rating_count=rating_count,
            )
        )

    return TagListResponse(items=items, pagination=result.pagination)


def _build_relation_response(pairs: List[Tuple[Tag, int]]) -> List[TagRelationResponse]:
    return [TagRelationResponse(id=tag.id, name=tag.name, depth=depth) for tag, depth in pairs]


# Hierarchy Endpoints

@router.get("/hierarchy", response_model=TagHierarchyResponse)
async def get_tag_hierarchy(
    include_ratings: bool = Query(False, description="Include average ratings for each tag"),
    service: TagService = Depends(get_tag_service)
):
    """Get the complete tag hierarchy from database.

    Returns the tag ontology in structured format compatible with frontend tree view components.
    Database-backed version (v2.0) replacing the static JSON file approach.

    Args:
        include_ratings: Whether to include average ratings for tags
        service: Tag service instance

    Returns:
        dict: Complete hierarchy with nodes and metadata

    Raises:
        HTTPException: If hierarchy data cannot be loaded
    """
    try:
        hierarchy = service.get_full_hierarchy(include_ratings=include_ratings)
        return hierarchy

    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load tag hierarchy: {str(e)}"
        )


@router.post("/hierarchy/refresh", response_model=SuccessResponse)
async def refresh_tag_hierarchy(service: TagService = Depends(get_tag_service)):
    """Refresh cached hierarchy data (no-op placeholder until caching is added)."""

    try:
        service.get_hierarchy_json()
        return SuccessResponse(success=True, message="Tag hierarchy refreshed")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh hierarchy: {str(e)}"
        )


@router.get("/statistics", response_model=TagStatisticsResponse)
async def get_tag_statistics(service: TagService = Depends(get_tag_service)):
    """Get global tag hierarchy statistics.

    Returns:
        dict: Statistics including totalNodes, totalRelationships, rootCategories
    """
    try:
        stats = service.get_hierarchy_statistics()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )


@router.get("/roots", response_model=List[TagSummaryResponse])
async def get_root_tags(service: TagService = Depends(get_tag_service)):
    """Get all root tags (tags without parents).

    Returns:
        list: List of root tags
    """
    try:
        roots = service.get_root_tags()
        return [{"id": str(t.id), "name": t.name, "metadata": t.tag_metadata} for t in roots]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get root tags: {str(e)}"
        )


# Tag CRUD Endpoints

@router.get("/", response_model=TagListResponse)
async def list_tags(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort: str = Query(
        "name-asc",
        description=(
            "Sort order (name-asc, name-desc, created-asc, created-desc, "
            "updated-asc, updated-desc, rating-asc, rating-desc)"
        ),
    ),
    search: Optional[str] = Query(None, description="Optional search query"),
    min_ratings: int = Query(1, ge=1, description="Minimum ratings when sorting by rating"),
    service: TagService = Depends(get_tag_service)
):
    """Get all tags with pagination.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        sort: Sort field
        service: Tag service instance

    Returns:
        PaginatedResponse: Paginated list of tags
    """
    try:
        pagination = PaginationRequest(page=page, page_size=page_size)

        normalized_sort = (sort or "name-asc").lower()
        if search:
            result = service.search_tags(search, pagination)

            if normalized_sort.startswith("rating") and result.items:
                rating_map = service.repository.get_tags_with_ratings([tag.id for tag in result.items])
                reverse = normalized_sort.endswith("desc")

                def rating_key(tag: Tag) -> Tuple[float, int, str]:
                    avg, count = rating_map.get(tag.id, (0.0, 0))
                    return (float(avg or 0.0), int(count or 0), tag.name.lower())

                sorted_items = sorted(result.items, key=rating_key, reverse=reverse)
                result = PaginatedResponse(items=sorted_items, pagination=result.pagination)
        else:
            result = service.get_tags(pagination, sort=normalized_sort, min_ratings=min_ratings)

        return _build_tag_list_response(service, result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tags: {str(e)}"
        )


@router.get("/search", response_model=TagListResponse)
async def search_tags(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: str = Query(
        "name-asc",
        description=(
            "Sort order (name-asc, name-desc, created-asc, created-desc, "
            "updated-asc, updated-desc, rating-asc, rating-desc)"
        ),
    ),
    min_ratings: int = Query(1, ge=1, description="Minimum ratings when sorting by rating"),
    service: TagService = Depends(get_tag_service)
):
    """Search tags by name.

    Args:
        q: Search query string
        page: Page number
        page_size: Items per page
        service: Tag service instance

    Returns:
        PaginatedResponse: Matching tags
    """
    try:
        return await list_tags(
            page=page,
            page_size=page_size,
            sort=sort,
            search=q,
            min_ratings=min_ratings,
            service=service,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search tags: {str(e)}"
        )


@router.get("/ratings", response_model=TagUserRatingsResponse)
async def get_user_tag_ratings(
    user_id: UUID = Query(..., description="User ID"),
    tag_ids: Optional[List[UUID]] = Query(
        None,
        description="Optional list of tag IDs to filter; when omitted returns an empty mapping",
    ),
    service: TagService = Depends(get_tag_service)
):
    """Get a user's ratings for multiple tags."""

    try:
        if not tag_ids:
            return TagUserRatingsResponse(ratings={})

        ratings = service.get_user_ratings_map(user_id, list(tag_ids))
        return TagUserRatingsResponse(ratings=ratings)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get ratings: {str(e)}"
        )


@router.get("/favorites", response_model=List[TagSummaryResponse])
async def get_user_favorites_query(
    user_id: UUID = Query(..., description="User ID"),
    service: TagService = Depends(get_tag_service)
):
    """Get user's favorite tags using query parameter."""

    try:
        favorites = service.get_user_favorites(user_id)
        return [_build_tag_summary(t) for t in favorites]
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get favorites: {str(e)}"
        )


def _build_tag_detail_response(
    detail: Dict[str, Any],
    *,
    ancestors: Optional[List[TagRelationResponse]] = None,
    descendants: Optional[List[TagRelationResponse]] = None,
) -> TagDetailResponse:
    rating_count = detail.get("rating_count") or 0
    average_rating = detail.get("average_rating")
    tag_response = _build_tag_response(
        detail["tag"],
        average_rating=average_rating,
        rating_count=rating_count,
        is_favorite=detail.get("is_favorite"),
    )

    parents = [_build_tag_summary(parent) for parent in detail.get("parents", [])]
    children = [_build_tag_summary(child) for child in detail.get("children", [])]

    return TagDetailResponse(
        tag=tag_response,
        parents=parents,
        children=children,
        ancestors=ancestors,
        descendants=descendants,
        average_rating=average_rating,
        rating_count=rating_count,
        user_rating=detail.get("user_rating"),
        is_favorite=detail.get("is_favorite"),
    )


@router.get("/{tag_id}", response_model=TagDetailResponse)
async def get_tag_detail(
    tag_id: UUID,
    user_id: Optional[UUID] = Query(None, description="User ID for user-specific data"),
    service: TagService = Depends(get_tag_service)
):
    """Get detailed information about a tag.

    Args:
        tag_id: Tag UUID
        user_id: Optional user UUID to include user's rating
        service: Tag service instance

    Returns:
        dict: Tag details including parents, children, ratings

    Raises:
        HTTPException: If tag not found
    """
    try:
        detail = service.get_tag_detail(tag_id, user_id)
        return _build_tag_detail_response(detail)

    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tag detail: {str(e)}"
        )


@router.get("/by-name/{tag_name}", response_model=TagDetailResponse)
async def get_tag_detail_by_name(
    tag_name: str,
    user_id: Optional[UUID] = Query(None, description="User ID for user-specific data"),
    service: TagService = Depends(get_tag_service)
):
    """Get detailed tag information by name."""
    try:
        tag = service.get_tag_by_name(tag_name)
        detail = service.get_tag_detail(tag.id, user_id)
        return _build_tag_detail_response(detail)

    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tag detail by name: {str(e)}"
        )


@router.get("/{tag_id}/children", response_model=List[TagSummaryResponse])
async def get_tag_children(
    tag_id: UUID,
    service: TagService = Depends(get_tag_service)
):
    """Get direct children of a tag.

    Args:
        tag_id: Parent tag UUID
        service: Tag service instance

    Returns:
        list: Child tags
    """
    try:
        children = service.get_children(tag_id)
        return [_build_tag_summary(c) for c in children]

    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get children: {str(e)}"
        )


@router.get("/{tag_id}/parents", response_model=List[TagSummaryResponse])
async def get_tag_parents(
    tag_id: UUID,
    service: TagService = Depends(get_tag_service)
):
    """Get direct parents of a tag.

    Args:
        tag_id: Child tag UUID
        service: Tag service instance

    Returns:
        list: Parent tags
    """
    try:
        parents = service.get_parents(tag_id)
        return [_build_tag_summary(p) for p in parents]

    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get parents: {str(e)}"
        )


@router.get("/{tag_id}/ancestors", response_model=List[TagRelationResponse])
async def get_tag_ancestors(
    tag_id: UUID,
    max_depth: int = Query(10, ge=1, le=50, description="Maximum recursion depth"),
    service: TagService = Depends(get_tag_service)
):
    """Get ancestor tags including traversal depth."""
    try:
        ancestors = service.get_ancestors(tag_id, max_depth=max_depth)
        return _build_relation_response(ancestors)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get ancestors: {str(e)}"
        )


@router.get("/{tag_id}/descendants", response_model=List[TagRelationResponse])
async def get_tag_descendants(
    tag_id: UUID,
    max_depth: int = Query(10, ge=1, le=50, description="Maximum recursion depth"),
    service: TagService = Depends(get_tag_service)
):
    """Get descendant tags including traversal depth."""
    try:
        descendants = service.get_descendants(tag_id, max_depth=max_depth)
        return _build_relation_response(descendants)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get descendants: {str(e)}"
        )


# Rating Endpoints

@router.post("/{tag_id}/rate", response_model=TagRatingResponse)
async def rate_tag(
    tag_id: UUID,
    user_id: UUID = Query(..., description="User ID"),
    rating: float = Query(..., ge=1.0, le=5.0, description="Rating (1.0-5.0)"),
    service: TagService = Depends(get_tag_service)
):
    """Rate a tag.

    Args:
        tag_id: Tag UUID
        user_id: User UUID
        rating: Rating value (1.0-5.0)
        service: Tag service instance

    Returns:
        dict: Created/updated rating

    Raises:
        HTTPException: If validation fails or entities not found
    """
    try:
        rating_obj = service.rate_tag(user_id, tag_id, rating)
        return TagRatingResponse.model_validate(rating_obj)

    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rate tag: {str(e)}"
        )


@router.delete("/{tag_id}/rate", response_model=SuccessResponse)
async def delete_tag_rating(
    tag_id: UUID,
    user_id: UUID = Query(..., description="User ID"),
    service: TagService = Depends(get_tag_service)
):
    """Delete a tag rating.

    Args:
        tag_id: Tag UUID
        user_id: User UUID
        service: Tag service instance

    Returns:
        dict: Success message
    """
    try:
        deleted = service.delete_rating(user_id, tag_id)
        if deleted:
            return SuccessResponse(success=True, message="Rating deleted successfully")

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rating not found"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete rating: {str(e)}"
        )


@router.get("/{tag_id}/rating", response_model=TagRatingValueResponse)
async def get_user_tag_rating(
    tag_id: UUID,
    user_id: UUID = Query(..., description="User ID"),
    service: TagService = Depends(get_tag_service)
):
    """Get user's rating for a tag.

    Args:
        tag_id: Tag UUID
        user_id: User UUID
        service: Tag service instance

    Returns:
        dict: User's rating or null
    """
    try:
        rating = service.get_user_rating(user_id, tag_id)
        return TagRatingValueResponse(rating=rating)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rating: {str(e)}"
        )


# Favorites Endpoints

@router.get("/favorites/{user_id}", response_model=List[TagSummaryResponse])
async def get_user_favorites(
    user_id: UUID,
    service: TagService = Depends(get_tag_service)
):
    """Get user's favorite tags.

    Args:
        user_id: User UUID
        service: Tag service instance

    Returns:
        list: User's favorite tags
    """
    try:
        favorites = service.get_user_favorites(user_id)
        return [_build_tag_summary(t) for t in favorites]

    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get favorites: {str(e)}"
        )


@router.post("/{tag_id}/favorite", response_model=SuccessResponse)
async def add_tag_to_favorites(
    tag_id: UUID,
    user_id: UUID = Query(..., description="User ID"),
    service: TagService = Depends(get_tag_service)
):
    """Add tag to user's favorites.

    Args:
        tag_id: Tag UUID
        user_id: User UUID
        service: Tag service instance

    Returns:
        dict: Success message
    """
    try:
        service.add_favorite(user_id, tag_id)
        return SuccessResponse(success=True, message="Tag added to favorites")

    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add favorite: {str(e)}"
        )


@router.delete("/{tag_id}/favorite", response_model=SuccessResponse)
async def remove_tag_from_favorites(
    tag_id: UUID,
    user_id: UUID = Query(..., description="User ID"),
    service: TagService = Depends(get_tag_service)
):
    """Remove tag from user's favorites.

    Args:
        tag_id: Tag UUID
        user_id: User UUID
        service: Tag service instance

    Returns:
        dict: Success message
    """
    try:
        service.remove_favorite(user_id, tag_id)
        return SuccessResponse(success=True, message="Tag removed from favorites")

    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove favorite: {str(e)}"
        )
