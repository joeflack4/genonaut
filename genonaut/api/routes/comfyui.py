"""ComfyUI generation API routes."""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from genonaut.api.dependencies import get_database_session
from genonaut.api.services.comfyui_generation_service import ComfyUIGenerationService
from genonaut.api.models.requests import (
    ComfyUIGenerationCreateRequest,
    ComfyUIModelListRequest,
    ComfyUIGenerationListRequest
)
from genonaut.api.models.responses import (
    ComfyUIGenerationResponse,
    ComfyUIGenerationListResponse,
    AvailableModelResponse,
    AvailableModelListResponse,
    SuccessResponse
)
from genonaut.api.exceptions import EntityNotFoundError, ValidationError, DatabaseError

router = APIRouter(prefix="/api/v1/comfyui", tags=["comfyui"])


@router.post("/generate", response_model=ComfyUIGenerationResponse, status_code=status.HTTP_201_CREATED)
async def create_generation(
    generation_data: ComfyUIGenerationCreateRequest,
    db: Session = Depends(get_database_session)
):
    """Create a new ComfyUI generation request."""
    service = ComfyUIGenerationService(db)
    try:
        generation = service.create_generation_request(
            user_id=generation_data.user_id,
            prompt=generation_data.prompt,
            negative_prompt=generation_data.negative_prompt,
            checkpoint_model=generation_data.checkpoint_model,
            lora_models=generation_data.lora_models,
            width=generation_data.width,
            height=generation_data.height,
            batch_size=generation_data.batch_size,
            sampler_params=generation_data.sampler_params
        )
        return ComfyUIGenerationResponse.model_validate(generation)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{generation_id}", response_model=ComfyUIGenerationResponse)
async def get_generation(
    generation_id: int,
    db: Session = Depends(get_database_session)
):
    """Get a specific ComfyUI generation by ID."""
    service = ComfyUIGenerationService(db)
    try:
        generation = service.get_generation_by_id(generation_id)
        return ComfyUIGenerationResponse.model_validate(generation)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/", response_model=ComfyUIGenerationListResponse)
async def list_generations(
    user_id: UUID = None,
    status: str = None,
    created_after: str = None,
    created_before: str = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_database_session)
):
    """List ComfyUI generations with optional filtering."""
    service = ComfyUIGenerationService(db)
    try:
        request = ComfyUIGenerationListRequest(
            user_id=user_id,
            status=status,
            created_after=created_after,
            created_before=created_before,
            page=page,
            page_size=page_size
        )
        result = service.list_generations(request)
        return result
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.delete("/{generation_id}", response_model=SuccessResponse)
async def cancel_generation(
    generation_id: int,
    db: Session = Depends(get_database_session)
):
    """Cancel a ComfyUI generation."""
    service = ComfyUIGenerationService(db)
    try:
        service.cancel_generation(generation_id)
        return SuccessResponse(message="Generation cancelled successfully")
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/models/", response_model=AvailableModelListResponse)
async def list_available_models(
    model_type: str = None,
    is_active: bool = None,
    search: str = None,
    db: Session = Depends(get_database_session)
):
    """List available ComfyUI models."""
    service = ComfyUIGenerationService(db)
    try:
        request = ComfyUIModelListRequest(
            model_type=model_type,
            is_active=is_active,
            search=search
        )
        result = service.list_available_models(request)
        return result
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/models/refresh", response_model=SuccessResponse)
async def refresh_models(
    db: Session = Depends(get_database_session)
):
    """Refresh available models from ComfyUI model directories."""
    service = ComfyUIGenerationService(db)
    try:
        count = service.refresh_available_models()
        return SuccessResponse(message=f"Refreshed {count} models successfully")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))