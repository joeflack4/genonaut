"""Tag service for business logic operations.

Handles tag operations including hierarchy navigation, ratings, and favorites.
Replaces functionality from tag_hierarchy_service.py with database-backed implementation.
"""

from typing import List, Optional, Dict, Any, Tuple, Set
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from genonaut.db.schema import Tag, TagRating, User
from genonaut.api.repositories.tag_repository import TagRepository
from genonaut.api.repositories.user_repository import UserRepository
from genonaut.api.models.requests import PaginationRequest
from genonaut.api.models.responses import PaginatedResponse
from genonaut.api.exceptions import EntityNotFoundError, ValidationError, DatabaseError


class TagService:
    """Service class for tag business logic.

    Provides high-level operations for tag management, hierarchy navigation,
    ratings, and user favorites.
    """

    def __init__(self, db: Session):
        """Initialize service with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.repository = TagRepository(db)
        self.user_repository = UserRepository(db)
        self.db = db

    def _get_user_or_raise(self, user_id: UUID) -> User:
        """Fetch a user and raise an error if they do not exist."""

        user = self.user_repository.get_by_id(user_id)
        if user is None:
            raise EntityNotFoundError("User", user_id)
        return user

    # Tag CRUD Operations

    def get_tag_by_id(self, tag_id: UUID) -> Tag:
        """Get tag by ID.

        Args:
            tag_id: Tag UUID

        Returns:
            Tag instance

        Raises:
            EntityNotFoundError: If tag not found
        """
        tag = self.repository.get_by_id(tag_id)
        if tag is None:
            raise EntityNotFoundError("Tag", tag_id)
        return tag

    def get_tag_by_name(self, name: str) -> Tag:
        """Get tag by name.

        Args:
            name: Tag name

        Returns:
            Tag instance

        Raises:
            EntityNotFoundError: If tag not found
        """
        tag = self.repository.get_by_name(name)
        if tag is None:
            raise EntityNotFoundError("Tag", name)
        return tag

    def get_tags(
        self,
        pagination: PaginationRequest,
        sort: str = "name-asc",
        min_ratings: int = 1
    ) -> PaginatedResponse:
        """Get all tags with pagination.

        Args:
            pagination: Pagination parameters
            sort: Sort field (name-asc, name-desc, created-asc, created-desc,
                updated-asc, updated-desc, rating-asc, rating-desc)
            min_ratings: Minimum number of ratings when sorting by rating

        Returns:
            Paginated response with tags
        """
        normalized_sort = (sort or "name-asc").lower()
        if normalized_sort.startswith("rating"):
            order = "asc" if normalized_sort.endswith("asc") else "desc"
            return self.repository.get_tags_sorted_by_rating(
                pagination,
                min_ratings=max(min_ratings, 1),
                order=order
            )

        return self.repository.get_all_paginated(pagination, normalized_sort)

    def search_tags(self, query: str, pagination: PaginationRequest) -> PaginatedResponse:
        """Search tags by name.

        Args:
            query: Search query string
            pagination: Pagination parameters

        Returns:
            Paginated response with matching tags
        """
        return self.repository.search_tags(query, pagination)

    # Hierarchy Navigation

    def get_root_tags(self) -> List[Tag]:
        """Get all root tags (tags with no parents).

        Returns:
            List of root tags sorted by name
        """
        return self.repository.get_root_tags()

    def get_children(self, tag_id: UUID) -> List[Tag]:
        """Get direct children of a tag.

        Args:
            tag_id: Parent tag UUID

        Returns:
            List of child tags

        Raises:
            EntityNotFoundError: If tag not found
        """
        # Verify tag exists
        self.get_tag_by_id(tag_id)
        return self.repository.get_children(tag_id)

    def get_parents(self, tag_id: UUID) -> List[Tag]:
        """Get direct parents of a tag.

        Args:
            tag_id: Child tag UUID

        Returns:
            List of parent tags

        Raises:
            EntityNotFoundError: If tag not found
        """
        # Verify tag exists
        self.get_tag_by_id(tag_id)
        return self.repository.get_parents(tag_id)

    def get_descendants(self, tag_id: UUID, max_depth: int = 10) -> List[Tuple[Tag, int]]:
        """Get all descendants of a tag recursively.

        Args:
            tag_id: Parent tag UUID
            max_depth: Maximum recursion depth

        Returns:
            List of tuples (Tag, depth) ordered by depth and name

        Raises:
            EntityNotFoundError: If tag not found
        """
        # Verify tag exists
        self.get_tag_by_id(tag_id)
        return self.repository.get_descendants(tag_id, max_depth)

    def get_ancestors(self, tag_id: UUID, max_depth: int = 10) -> List[Tuple[Tag, int]]:
        """Get all ancestors of a tag recursively.

        Args:
            tag_id: Child tag UUID
            max_depth: Maximum recursion depth

        Returns:
            List of tuples (Tag, depth) ordered by depth and name

        Raises:
            EntityNotFoundError: If tag not found
        """
        # Verify tag exists
        self.get_tag_by_id(tag_id)
        return self.repository.get_ancestors(tag_id, max_depth)

    def get_full_hierarchy(self, include_ratings: bool = False) -> Dict[str, Any]:
        """Get complete tag hierarchy with metadata.

        Args:
            include_ratings: Whether to include average ratings for each tag

        Returns:
            Dictionary with hierarchy data in format compatible with frontend:
            {
                "nodes": [{"id": str, "name": str, "parent": str | null}, ...],
                "metadata": {"totalNodes": int, "totalRelationships": int, ...}
            }
        """
        # Get all tags
        all_tags = self.repository.get_all()

        # Get all tag parent relationships
        from genonaut.db.schema import TagParent
        relationships = self.db.query(TagParent).all()

        rating_lookup: Dict[UUID, Tuple[float, int]] = {}
        if include_ratings and all_tags:
            rating_lookup = self.repository.get_tags_with_ratings([tag.id for tag in all_tags])

        # Build nodes list
        nodes = []

        for tag in all_tags:
            # Get first parent (for backward compatibility with single-parent JSON format)
            # In the future, we can enhance this to support multiple parents
            parents = [rel.parent_id for rel in relationships if rel.tag_id == tag.id]
            parent_id = parents[0] if parents else None

            # Find parent name if exists
            parent_name = None
            if parent_id:
                for t in all_tags:
                    if t.id == parent_id:
                        parent_name = t.name
                        break

            node = {
                "id": str(tag.id),  # Use UUID as ID
                "name": tag.name,
                "parent": str(parent_id) if parent_id else None
            }

            if include_ratings:
                avg_rating_info = rating_lookup.get(tag.id)
                if avg_rating_info:
                    avg_rating, rating_count = avg_rating_info
                    node["average_rating"] = round(float(avg_rating), 2)
                    node["rating_count"] = int(rating_count)
                else:
                    node["average_rating"] = None
                    node["rating_count"] = 0

            nodes.append(node)

        # Get statistics
        stats = self.repository.get_hierarchy_statistics()

        # Build metadata
        from datetime import datetime, timezone
        metadata = {
            "totalNodes": stats["totalNodes"],
            "totalRelationships": stats["totalRelationships"],
            "rootCategories": stats["rootCategories"],
            "lastUpdated": datetime.now(timezone.utc).isoformat(),
            "format": "flat_array",
            "version": "2.0"  # Version 2.0 to indicate database-backed
        }

        return {
            "nodes": nodes,
            "metadata": metadata
        }

    def get_hierarchy_json(self) -> Dict[str, Any]:
        """Get hierarchy as JSON optimized for frontend.

        This is a cached/optimized version for performance.
        Currently just calls get_full_hierarchy but can be enhanced
        with caching in the future.

        Returns:
            Dictionary with hierarchy data
        """
        return self.get_full_hierarchy(include_ratings=False)

    def get_tag_detail(
        self,
        tag_id: UUID,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get detailed information about a tag.

        Args:
            tag_id: Tag UUID
            user_id: Optional user UUID to include user-specific data

        Returns:
            Dictionary with tag details including:
            - tag: Tag object
            - parents: List of parent tags
            - children: List of child tags
            - average_rating: Average rating (0.0 if no ratings)
            - rating_count: Number of ratings
            - user_rating: User's rating (if user_id provided)

        Raises:
            EntityNotFoundError: If tag not found
        """
        tag = self.get_tag_by_id(tag_id)

        # Get hierarchy info
        parents = self.get_parents(tag_id)
        children = self.get_children(tag_id)

        # Get rating info
        avg_rating, rating_count = self.repository.get_tag_average_rating(tag_id)

        # Get user's rating if user_id provided
        user_rating = None
        is_favorite: Optional[bool] = None
        if user_id:
            user = self._get_user_or_raise(user_id)
            rating_obj = self.repository.get_user_rating(user_id, tag_id)
            user_rating = rating_obj.rating if rating_obj else None
            favorites: Set[str] = {str(fid) for fid in (user.favorite_tag_ids or [])}
            is_favorite = str(tag_id) in favorites

        average_rating_value: Optional[float] = None
        if rating_count > 0:
            average_rating_value = round(float(avg_rating), 2)

        return {
            "tag": tag,
            "parents": parents,
            "children": children,
            "average_rating": average_rating_value,
            "rating_count": rating_count,
            "user_rating": user_rating,
            "is_favorite": is_favorite
        }

    # Rating Operations

    def rate_tag(self, user_id: UUID, tag_id: UUID, rating: float) -> TagRating:
        """Rate a tag.

        Args:
            user_id: User UUID
            tag_id: Tag UUID
            rating: Rating value (1.0-5.0)

        Returns:
            TagRating instance

        Raises:
            EntityNotFoundError: If user or tag not found
            ValidationError: If rating is out of range
        """
        # Validate rating range
        if not (1.0 <= rating <= 5.0):
            raise ValidationError(f"Rating must be between 1.0 and 5.0, got {rating}")

        # Verify user exists
        user = self._get_user_or_raise(user_id)

        # Verify tag exists
        self.get_tag_by_id(tag_id)

        # Upsert rating
        return self.repository.upsert_rating(user_id, tag_id, rating)

    def delete_rating(self, user_id: UUID, tag_id: UUID) -> bool:
        """Delete a tag rating.

        Args:
            user_id: User UUID
            tag_id: Tag UUID

        Returns:
            True if rating was deleted, False if not found
        """
        return self.repository.delete_rating(user_id, tag_id)

    def get_user_rating(self, user_id: UUID, tag_id: UUID) -> Optional[float]:
        """Get user's rating for a tag.

        Args:
            user_id: User UUID
            tag_id: Tag UUID

        Returns:
            Rating value or None if not rated
        """
        rating = self.repository.get_user_rating(user_id, tag_id)
        return rating.rating if rating else None

    def get_tags_sorted_by_rating(
        self,
        pagination: PaginationRequest,
        min_ratings: int = 5
    ) -> PaginatedResponse:
        """Get tags sorted by average rating.

        Args:
            pagination: Pagination parameters
            min_ratings: Minimum number of ratings required

        Returns:
            Paginated response with top-rated tags
        """
        return self.repository.get_tags_sorted_by_rating(pagination, min_ratings)

    # Favorites Operations

    def get_user_favorites(self, user_id: UUID) -> List[Tag]:
        """Get user's favorite tags.

        Args:
            user_id: User UUID

        Returns:
            List of favorite tags

        Raises:
            EntityNotFoundError: If user not found
        """
        user = self._get_user_or_raise(user_id)

        # Get favorite tag IDs from user
        favorite_ids_raw = user.favorite_tag_ids or []

        if not favorite_ids_raw:
            return []

        uuid_ids: List[UUID] = []
        slug_ids: List[str] = []

        for tag_id in favorite_ids_raw:
            try:
                uuid_ids.append(UUID(str(tag_id)))
            except (ValueError, TypeError):
                slug_ids.append(str(tag_id))

        tags: List[Tag] = []

        if uuid_ids:
            tags.extend(self.repository.get_by_ids(uuid_ids))

        if slug_ids:
            tags.extend(self.repository.get_by_names(slug_ids))

        return tags

    def add_favorite(self, user_id: UUID, tag_id: UUID) -> User:
        """Add tag to user's favorites.

        Args:
            user_id: User UUID
            tag_id: Tag UUID

        Returns:
            Updated User instance

        Raises:
            EntityNotFoundError: If user or tag not found
        """
        # Verify user exists
        user = self._get_user_or_raise(user_id)

        # Verify tag exists
        self.get_tag_by_id(tag_id)

        favorite_ids_raw = user.favorite_tag_ids or []
        favorite_ids = [str(existing) for existing in favorite_ids_raw]
        tag_identifier = str(tag_id)

        if tag_identifier not in favorite_ids:
            favorite_ids.append(tag_identifier)
            user.favorite_tag_ids = favorite_ids

            flag_modified(user, 'favorite_tag_ids')

            self.db.commit()
            self.db.refresh(user)

        return user

    def remove_favorite(self, user_id: UUID, tag_id: UUID) -> User:
        """Remove tag from user's favorites.

        Args:
            user_id: User UUID
            tag_id: Tag UUID

        Returns:
            Updated User instance

        Raises:
            EntityNotFoundError: If user not found
        """
        # Verify user exists
        user = self.user_repository.get_by_id(user_id)
        if user is None:
            raise EntityNotFoundError("User", user_id)

        # Get current favorites
        favorite_ids_raw = user.favorite_tag_ids or []
        favorite_ids = [str(existing) for existing in favorite_ids_raw]
        tag_identifier = str(tag_id)

        if tag_identifier in favorite_ids:
            favorite_ids.remove(tag_identifier)
            user.favorite_tag_ids = favorite_ids

            flag_modified(user, 'favorite_tag_ids')

            self.db.commit()
            self.db.refresh(user)

        return user

    def is_favorite(self, user_id: UUID, tag_id: UUID) -> bool:
        """Check if a tag is in user's favorites.

        Args:
            user_id: User UUID
            tag_id: Tag UUID

        Returns:
            True if tag is favorited, False otherwise

        Raises:
            EntityNotFoundError: If user not found
        """
        user = self._get_user_or_raise(user_id)

        favorite_ids = {str(existing) for existing in (user.favorite_tag_ids or [])}
        return str(tag_id) in favorite_ids

    def get_user_ratings_map(self, user_id: UUID, tag_ids: List[UUID]) -> Dict[UUID, float]:
        """Get a mapping of tag IDs to the user's ratings."""

        if not tag_ids:
            return {}

        self._get_user_or_raise(user_id)

        ratings = self.repository.get_user_ratings(user_id, tag_ids)
        return {rating.tag_id: rating.rating for rating in ratings}

    # Statistics

    def get_hierarchy_statistics(self) -> Dict[str, int]:
        """Get global hierarchy statistics.

        Returns:
            Dictionary with statistics:
            - totalNodes: Total number of tags
            - totalRelationships: Total number of parent-child relationships
            - rootCategories: Number of root tags
        """
        return self.repository.get_hierarchy_statistics()
