"""Admin routes for flagged content management."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from genonaut.api.dependencies import get_database_session
from genonaut.api.services.flagged_content_service import FlaggedContentService
from genonaut.api.models.requests import PaginationRequest
from genonaut.api.models.responses import PaginatedResponse, SuccessResponse
from genonaut.api.exceptions import EntityNotFoundError, ValidationError, DatabaseError
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/admin/flagged-content", tags=["admin", "flagged-content"])


# Request/Response Models

class ScanContentRequest(BaseModel):
    """Request model for scanning content."""
    content_types: List[str] = Field(
        default=["regular", "auto"],
        description="Content types to scan"
    )
    force_rescan: bool = Field(
        default=False,
        description="Force rescan of already flagged items"
    )


class ScanContentResponse(BaseModel):
    """Response model for scan results."""
    items_scanned: int = Field(..., description="Number of items scanned")
    items_flagged: int = Field(..., description="Number of items flagged")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")


class FlaggedContentResponse(BaseModel):
    """Response model for flagged content."""
    id: int
    content_item_id: Optional[int]
    content_item_auto_id: Optional[int]
    content_source: str
    flagged_text: str
    flagged_words: List[str]
    total_problem_words: int
    total_words: int
    problem_percentage: float
    risk_score: float
    creator_id: UUID
    flagged_at: str
    reviewed: bool
    reviewed_at: Optional[str]
    reviewed_by: Optional[UUID]
    notes: Optional[str]

    model_config = {"from_attributes": True}


class ReviewFlaggedContentRequest(BaseModel):
    """Request model for reviewing flagged content."""
    reviewed: bool = Field(..., description="Review status")
    reviewed_by: UUID = Field(..., description="ID of reviewer")
    notes: Optional[str] = Field(None, description="Review notes")


class BulkDeleteRequest(BaseModel):
    """Request model for bulk delete."""
    ids: List[int] = Field(..., description="List of flagged content IDs to delete")


class BulkDeleteResponse(BaseModel):
    """Response model for bulk delete."""
    deleted_count: int = Field(..., description="Number of items deleted")
    errors: List[dict] = Field(..., description="List of errors if any")


class StatisticsResponse(BaseModel):
    """Response model for statistics."""
    total_flagged: int
    unreviewed_count: int
    average_risk_score: float
    high_risk_count: int
    by_source: dict


# API Routes

@router.post("/scan", response_model=ScanContentResponse, status_code=status.HTTP_200_OK)
async def scan_for_flags(
    request: ScanContentRequest,
    db: Session = Depends(get_database_session)
):
    """Manually trigger scan of existing content for problematic words."""
    try:
        service = FlaggedContentService(db)
        result = service.scan_content_items(
            content_types=request.content_types,
            force_rescan=request.force_rescan
        )
        return ScanContentResponse(**result)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/", response_model=PaginatedResponse[FlaggedContentResponse])
async def get_flagged_content(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    creator_id: Optional[UUID] = Query(None, description="Filter by creator ID"),
    content_source: Optional[str] = Query(None, description="Filter by source (regular/auto)"),
    min_risk_score: Optional[float] = Query(None, ge=0, le=100, description="Minimum risk score"),
    max_risk_score: Optional[float] = Query(None, ge=0, le=100, description="Maximum risk score"),
    reviewed: Optional[bool] = Query(None, description="Filter by review status"),
    sort_by: str = Query("flagged_at", description="Sort field (risk_score/flagged_at/problem_count)"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    db: Session = Depends(get_database_session)
):
    """Get paginated list of flagged content with optional filters."""
    try:
        service = FlaggedContentService(db)
        pagination = PaginationRequest(page=page, page_size=page_size)

        result = service.get_flagged_content(
            pagination=pagination,
            creator_id=creator_id,
            content_source=content_source,
            min_risk_score=min_risk_score,
            max_risk_score=max_risk_score,
            reviewed=reviewed,
            sort_by=sort_by,
            sort_order=sort_order
        )

        # Convert items to response models
        items = [FlaggedContentResponse.model_validate(item) for item in result.items]
        return PaginatedResponse(items=items, pagination=result.pagination)

    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{flagged_content_id}", response_model=FlaggedContentResponse)
async def get_flagged_content_by_id(
    flagged_content_id: int,
    db: Session = Depends(get_database_session)
):
    """Get single flagged content item by ID."""
    try:
        service = FlaggedContentService(db)
        flagged_content = service.get_flagged_content_by_id(flagged_content_id)
        return FlaggedContentResponse.model_validate(flagged_content)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        # Catch-all for unexpected errors
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error: {str(e)}")


@router.put("/{flagged_content_id}/review", response_model=FlaggedContentResponse)
async def review_flagged_content(
    flagged_content_id: int,
    request: ReviewFlaggedContentRequest,
    db: Session = Depends(get_database_session)
):
    """Mark flagged content as reviewed."""
    try:
        service = FlaggedContentService(db)
        flagged_content = service.review_flagged_content(
            flagged_content_id=flagged_content_id,
            reviewed=request.reviewed,
            reviewed_by=request.reviewed_by,
            notes=request.notes
        )
        return FlaggedContentResponse.model_validate(flagged_content)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{flagged_content_id}", response_model=SuccessResponse)
async def delete_flagged_content(
    flagged_content_id: int,
    db: Session = Depends(get_database_session)
):
    """Delete flagged content and associated content item."""
    try:
        service = FlaggedContentService(db)
        service.delete_flagged_content(flagged_content_id)
        return SuccessResponse(
            success=True,
            message=f"Flagged content {flagged_content_id} deleted successfully"
        )
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/bulk-delete", response_model=BulkDeleteResponse)
async def bulk_delete_flagged_content(
    request: BulkDeleteRequest,
    db: Session = Depends(get_database_session)
):
    """Delete multiple flagged content items."""
    try:
        service = FlaggedContentService(db)
        result = service.bulk_delete_flagged_content(request.ids)
        return BulkDeleteResponse(**result)
    except DatabaseError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/statistics/summary", response_model=StatisticsResponse)
async def get_flagged_content_statistics(
    db: Session = Depends(get_database_session)
):
    """Get statistics about flagged content."""
    try:
        service = FlaggedContentService(db)
        stats = service.get_statistics()
        return StatisticsResponse(**stats)
    except DatabaseError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
