"""LoRA model API routes."""

from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from genonaut.api.dependencies import get_database_session
from genonaut.api.services.lora_model_service import LoraModelService
from genonaut.api.models.responses import (
    LoraModelResponse,
    LoraModelListResponse,
    LoraModelPaginationMeta
)
from genonaut.api.exceptions import EntityNotFoundError, DatabaseError

router = APIRouter(prefix="/api/v1/lora-models", tags=["lora-models"])


@router.get("/", response_model=LoraModelListResponse)
async def get_lora_models(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    checkpoint_id: Optional[str] = Query(None, description="UUID of checkpoint to check compatibility against"),
    db: Session = Depends(get_database_session)
):
    """Get paginated LoRA models with optional compatibility/optimality checking.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        checkpoint_id: Optional checkpoint UUID to check compatibility against

    Returns:
        Paginated list of LoRA models with compatibility/optimality flags
    """
    service = LoraModelService(db)

    try:
        # If checkpoint_id is provided, use the enhanced method with compatibility checking
        if checkpoint_id:
            enriched_models, total, total_pages = service.get_paginated_with_compatibility(
                page=page,
                page_size=page_size,
                checkpoint_id=checkpoint_id
            )

            # Convert enriched models to responses
            items = []
            for enriched in enriched_models:
                model_response = LoraModelResponse.model_validate(enriched['model'])
                model_response.is_compatible = enriched['is_compatible']
                model_response.is_optimal = enriched['is_optimal']
                items.append(model_response)

            pagination_meta = LoraModelPaginationMeta(
                page=page,
                page_size=page_size,
                total=total,
                total_pages=total_pages
            )

            return LoraModelListResponse(
                items=items,
                total=total,
                pagination=pagination_meta
            )
        else:
            # Simple pagination without compatibility checking
            models, total = service.repository.get_paginated(
                page=page,
                page_size=page_size
            )
            total_pages = (total + page_size - 1) // page_size

            pagination_meta = LoraModelPaginationMeta(
                page=page,
                page_size=page_size,
                total=total,
                total_pages=total_pages
            )

            return LoraModelListResponse(
                items=[LoraModelResponse.model_validate(model) for model in models],
                total=total,
                pagination=pagination_meta
            )

    except DatabaseError as exc:
        if "UndefinedTable" in str(exc):
            # Table doesn't exist yet, return empty list
            return LoraModelListResponse(
                items=[],
                total=0,
                pagination=LoraModelPaginationMeta(page=1, page_size=page_size, total=0, total_pages=0)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(exc)
            )


@router.get("/{id}", response_model=LoraModelResponse)
async def get_lora_model(
    id: UUID,
    db: Session = Depends(get_database_session)
):
    """Get LoRA model by ID.

    Args:
        id: LoRA model UUID

    Returns:
        LoraModel details

    Raises:
        404: If LoRA model not found
    """
    service = LoraModelService(db)

    try:
        model = service.get_by_id(id)
        return LoraModelResponse.model_validate(model)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc)
        )
