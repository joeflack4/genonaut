"""Checkpoint model API routes."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from genonaut.api.dependencies import get_database_session
from genonaut.api.services.checkpoint_model_service import CheckpointModelService
from genonaut.api.models.responses import (
    CheckpointModelResponse,
    CheckpointModelListResponse
)
from genonaut.api.exceptions import EntityNotFoundError, DatabaseError

router = APIRouter(prefix="/api/v1/checkpoint-models", tags=["checkpoint-models"])


@router.get("/", response_model=CheckpointModelListResponse)
async def get_checkpoint_models(
    show_unresolved: bool = Query(False, description="Show models with unresolved paths (default: False)"),
    db: Session = Depends(get_database_session)
):
    """Get all checkpoint models sorted by rating descending.

    Args:
        show_unresolved: Show models with unresolved paths (default: False)

    Returns:
        List of all checkpoint models sorted by rating (highest first)
    """
    service = CheckpointModelService(db)

    try:
        models = service.get_all(show_unresolved=show_unresolved)
        return CheckpointModelListResponse(
            items=[CheckpointModelResponse.model_validate(model) for model in models],
            total=len(models)
        )
    except DatabaseError as exc:
        if "UndefinedTable" in str(exc):
            # Table doesn't exist yet, return empty list
            return CheckpointModelListResponse(items=[], total=0)
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(exc)
            )


@router.get("/{id}", response_model=CheckpointModelResponse)
async def get_checkpoint_model(
    id: UUID,
    db: Session = Depends(get_database_session)
):
    """Get checkpoint model by ID.

    Args:
        id: Checkpoint model UUID

    Returns:
        CheckpointModel details

    Raises:
        404: If checkpoint model not found
    """
    service = CheckpointModelService(db)

    try:
        model = service.get_by_id(id)
        return CheckpointModelResponse.model_validate(model)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc)
        )
