"""ComfyUI generation orchestration service."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from genonaut.db.schema import ComfyUIGenerationRequest
from genonaut.api.repositories.comfyui_generation_repository import ComfyUIGenerationRepository
from genonaut.api.repositories.user_repository import UserRepository
from genonaut.api.services.comfyui_client import (
    ComfyUIClient, ComfyUIConnectionError, ComfyUIWorkflowError
)
from genonaut.api.services.workflow_builder import WorkflowBuilder, GenerationRequest
from genonaut.api.services.thumbnail_service import ThumbnailService
from genonaut.api.services.file_storage_service import FileStorageService
from genonaut.api.services.model_discovery_service import ModelDiscoveryService
from genonaut.api.exceptions import ValidationError, EntityNotFoundError, DatabaseError
from genonaut.api.models.requests import PaginationRequest, ComfyUIModelListRequest
from genonaut.api.models.responses import PaginatedResponse, AvailableModelListResponse, AvailableModelResponse


logger = logging.getLogger(__name__)


class ComfyUIGenerationService:
    """Service for orchestrating ComfyUI generation workflows."""

    def __init__(self, db: Session):
        """Initialize generation service.

        Args:
            db: Database session
        """
        self.db = db
        self.repository = ComfyUIGenerationRepository(db)
        self.user_repository = UserRepository(db)
        self.comfyui_client = ComfyUIClient()
        self.workflow_builder = WorkflowBuilder()
        self.thumbnail_service = ThumbnailService()
        self.file_storage_service = FileStorageService()
        self.model_discovery_service = ModelDiscoveryService(db)

    def create_generation_request(
        self,
        user_id: UUID,
        prompt: str,
        negative_prompt: str = "",
        checkpoint_model: str = "base_model.safetensors",
        lora_models: Optional[List[Dict[str, Any]]] = None,
        width: int = 832,
        height: int = 1216,
        batch_size: int = 1,
        sampler_params: Optional[Dict[str, Any]] = None
    ) -> ComfyUIGenerationRequest:
        """Create a new generation request.

        Args:
            user_id: ID of the requesting user
            prompt: Positive prompt text
            negative_prompt: Negative prompt text
            checkpoint_model: Name of checkpoint model to use
            lora_models: List of LoRA models with strengths
            width: Image width
            height: Image height
            batch_size: Number of images to generate
            sampler_params: KSampler parameters

        Returns:
            Created generation request

        Raises:
            ValidationError: If parameters are invalid
            EntityNotFoundError: If user doesn't exist
            DatabaseError: If database operation fails
        """
        # Validate user exists
        user = self.user_repository.get_or_404(user_id)

        # Set defaults
        if lora_models is None:
            lora_models = []
        if sampler_params is None:
            sampler_params = {}

        # Create generation request record
        try:
            generation_request = self.repository.create_generation_request(
                user_id=user_id,
                prompt=prompt,
                negative_prompt=negative_prompt,
                checkpoint_model=checkpoint_model,
                lora_models=lora_models,
                width=width,
                height=height,
                batch_size=batch_size,
                sampler_params=sampler_params,
                status='pending'
            )
            self.db.commit()
            logger.info(f"Created generation request {generation_request.id} for user {user_id}")
            return generation_request

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create generation request for user {user_id}: {str(e)}")
            raise

    def submit_to_comfyui(self, generation_request: ComfyUIGenerationRequest) -> str:
        """Submit generation request to ComfyUI.

        Args:
            generation_request: Generation request to submit

        Returns:
            ComfyUI prompt ID

        Raises:
            ComfyUIConnectionError: If ComfyUI connection fails
            ComfyUIWorkflowError: If workflow submission fails
            ValidationError: If request parameters are invalid
        """
        try:
            # Build workflow from request parameters
            workflow_params = {
                "prompt": generation_request.prompt,
                "negative_prompt": generation_request.negative_prompt,
                "checkpoint_model": generation_request.checkpoint_model,
                "lora_models": generation_request.lora_models,
                "width": generation_request.width,
                "height": generation_request.height,
                "batch_size": generation_request.batch_size,
                "sampler_params": generation_request.sampler_params,
                "filename_prefix": f"gen_{generation_request.id}"
            }

            workflow = self.workflow_builder.build_workflow_from_dict(workflow_params)

            # Submit to ComfyUI
            prompt_id = self.comfyui_client.submit_workflow(workflow)

            # Update request with ComfyUI prompt ID and processing status
            self.repository.update_status(
                generation_request.id,
                'processing',
                comfyui_prompt_id=prompt_id,
                started_at=datetime.utcnow()
            )
            self.db.commit()

            logger.info(
                f"Submitted generation request {generation_request.id} to ComfyUI with prompt ID {prompt_id}"
            )
            return prompt_id

        except Exception as e:
            # Update request status to failed
            try:
                self.repository.update_status(
                    generation_request.id,
                    'failed',
                    error_message=str(e)
                )
                self.db.commit()
            except Exception as db_error:
                logger.error(f"Failed to update request status after ComfyUI error: {str(db_error)}")

            logger.error(f"Failed to submit generation request {generation_request.id}: {str(e)}")
            raise

    def check_generation_status(self, generation_request: ComfyUIGenerationRequest) -> Dict[str, Any]:
        """Check the status of a generation request in ComfyUI.

        Args:
            generation_request: Generation request to check

        Returns:
            Status information dictionary

        Raises:
            ComfyUIConnectionError: If ComfyUI connection fails
        """
        if not generation_request.comfyui_prompt_id:
            return {"status": generation_request.status, "message": "No ComfyUI prompt ID"}

        try:
            # Get status from ComfyUI
            comfyui_status = self.comfyui_client.get_workflow_status(
                generation_request.comfyui_prompt_id
            )

            # Update database status if changed
            current_status = generation_request.status
            new_status = None

            if comfyui_status["status"] == "completed":
                new_status = "completed"
                # Extract output file paths
                outputs = comfyui_status.get("outputs", {})
                output_paths = self.comfyui_client.get_output_files(outputs)

                # Organize files into user directory structure
                organized_paths = output_paths
                if output_paths:
                    try:
                        organized_paths = self.file_storage_service.organize_generation_files(
                            generation_request.id, generation_request.user_id, output_paths
                        )
                        logger.info(f"Organized {len(organized_paths)} files for generation {generation_request.id}")
                    except Exception as e:
                        logger.error(f"Failed to organize files for generation {generation_request.id}: {e}")
                        # Use original paths if organization fails

                # Generate thumbnails for completed images
                thumbnail_results = {}
                if organized_paths:
                    try:
                        thumbnail_results = self.thumbnail_service.generate_thumbnail_for_generation(
                            organized_paths, generation_request.id
                        )
                        logger.info(f"Generated thumbnails for generation {generation_request.id}: {len(thumbnail_results)} images")
                    except Exception as e:
                        logger.error(f"Failed to generate thumbnails for generation {generation_request.id}: {e}")
                        # Don't fail the entire generation if thumbnails fail

                self.repository.update_status(
                    generation_request.id,
                    new_status,
                    output_paths=organized_paths,
                    completed_at=datetime.utcnow()
                )

            elif comfyui_status["status"] == "failed":
                new_status = "failed"
                error_messages = comfyui_status.get("messages", [])
                error_message = "; ".join([str(msg) for msg in error_messages]) if error_messages else "ComfyUI generation failed"

                self.repository.update_status(
                    generation_request.id,
                    new_status,
                    error_message=error_message,
                    completed_at=datetime.utcnow()
                )

            elif comfyui_status["status"] in ["queued", "running"]:
                if current_status != "processing":
                    new_status = "processing"
                    self.repository.update_status(
                        generation_request.id,
                        new_status
                    )

            if new_status and new_status != current_status:
                self.db.commit()
                logger.info(
                    f"Updated generation request {generation_request.id} status: {current_status} -> {new_status}"
                )

            return comfyui_status

        except Exception as e:
            logger.error(f"Failed to check generation status for request {generation_request.id}: {str(e)}")
            raise

    def cancel_generation(self, generation_request: ComfyUIGenerationRequest) -> bool:
        """Cancel a generation request.

        Args:
            generation_request: Generation request to cancel

        Returns:
            True if cancellation was successful

        Raises:
            ValidationError: If request cannot be cancelled
        """
        if generation_request.status in ['completed', 'failed', 'cancelled']:
            raise ValidationError(f"Cannot cancel generation with status: {generation_request.status}")

        try:
            # Cancel in ComfyUI if it has a prompt ID
            cancelled_in_comfyui = True
            if generation_request.comfyui_prompt_id:
                try:
                    cancelled_in_comfyui = self.comfyui_client.cancel_workflow(
                        generation_request.comfyui_prompt_id
                    )
                except ComfyUIConnectionError as e:
                    logger.warning(f"Failed to cancel in ComfyUI: {str(e)}")
                    cancelled_in_comfyui = False

            # Update status in database regardless of ComfyUI cancellation result
            self.repository.update_status(
                generation_request.id,
                'cancelled',
                completed_at=datetime.utcnow()
            )
            self.db.commit()

            logger.info(f"Cancelled generation request {generation_request.id}")
            return cancelled_in_comfyui

        except Exception as e:
            logger.error(f"Failed to cancel generation request {generation_request.id}: {str(e)}")
            self.db.rollback()
            raise

    def get_generation_request(self, request_id: int) -> ComfyUIGenerationRequest:
        """Get generation request by ID.

        Args:
            request_id: Generation request ID

        Returns:
            Generation request

        Raises:
            EntityNotFoundError: If request not found
        """
        return self.repository.get_or_404(request_id)

    def delete_generation(self, generation_request: ComfyUIGenerationRequest) -> bool:
        """Delete a generation request and its associated files.

        Args:
            generation_request: Generation request to delete

        Returns:
            True if deletion was successful

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Clean up files first
            deleted_files = self.file_storage_service.cleanup_generation_files(generation_request.id)

            # Delete from database
            self.repository.delete(generation_request.id)
            self.db.commit()

            logger.info(f"Deleted generation request {generation_request.id} and {deleted_files} associated files")
            return True

        except Exception as e:
            logger.error(f"Failed to delete generation request {generation_request.id}: {str(e)}")
            self.db.rollback()
            raise DatabaseError(f"Failed to delete generation: {str(e)}")

    def get_user_generations(
        self,
        user_id: UUID,
        pagination: Optional[PaginationRequest] = None,
        status: Optional[str] = None
    ) -> PaginatedResponse:
        """Get generation requests for a user.

        Args:
            user_id: User ID
            pagination: Pagination parameters
            status: Optional status filter

        Returns:
            Paginated list of generation requests
        """
        return self.repository.get_by_user(user_id, pagination, status)

    def process_pending_requests(self, max_concurrent: int = 5) -> int:
        """Process pending generation requests.

        Args:
            max_concurrent: Maximum number of concurrent generations

        Returns:
            Number of requests processed

        Raises:
            ComfyUIConnectionError: If ComfyUI connection fails
        """
        # Check ComfyUI health first
        if not self.comfyui_client.health_check():
            logger.warning("ComfyUI health check failed, skipping pending request processing")
            raise ComfyUIConnectionError("ComfyUI server is not accessible")

        # Get currently processing requests
        processing_requests = self.repository.get_processing_requests()
        current_count = len(processing_requests)

        if current_count >= max_concurrent:
            logger.info(f"Already at max concurrent generations ({current_count}/{max_concurrent})")
            return 0

        # Get pending requests
        available_slots = max_concurrent - current_count
        pending_requests = self.repository.get_pending_requests(available_slots)

        processed_count = 0
        for request in pending_requests:
            try:
                self.submit_to_comfyui(request)
                processed_count += 1
                logger.info(f"Started processing generation request {request.id}")
            except Exception as e:
                logger.error(f"Failed to process generation request {request.id}: {str(e)}")
                continue

        logger.info(f"Processed {processed_count} pending generation requests")
        return processed_count

    def update_processing_requests(self) -> int:
        """Update status of currently processing requests.

        Returns:
            Number of requests updated

        Raises:
            ComfyUIConnectionError: If ComfyUI connection fails
        """
        processing_requests = self.repository.get_processing_requests()
        updated_count = 0

        for request in processing_requests:
            try:
                self.check_generation_status(request)
                updated_count += 1
            except Exception as e:
                logger.error(f"Failed to update status for request {request.id}: {str(e)}")
                continue

        logger.info(f"Updated status for {updated_count} processing requests")
        return updated_count

    def get_available_models(self) -> Dict[str, List[str]]:
        """Get available models from ComfyUI.

        Returns:
            Dictionary with model types and available models

        Raises:
            ComfyUIConnectionError: If ComfyUI connection fails
        """
        return self.comfyui_client.get_available_models()

    def list_available_models(self, request: ComfyUIModelListRequest) -> AvailableModelListResponse:
        """List available models with filtering.

        Args:
            request: Model list request with filters

        Returns:
            Response with filtered models
        """
        try:
            # Get models from database
            if request.search:
                models = self.model_discovery_service.repository.search_models(
                    request.search,
                    request.model_type,
                    request.is_active if request.is_active is not None else True
                )
            elif request.model_type:
                models = self.model_discovery_service.repository.get_models_by_type(
                    request.model_type,
                    request.is_active if request.is_active is not None else True
                )
            else:
                models = self.model_discovery_service.repository.get_all_models(
                    request.is_active if request.is_active is not None else True
                )

            # Convert to response format
            model_responses = []
            for model in models:
                model_responses.append(AvailableModelResponse(
                    id=model.id,
                    name=model.name,
                    model_type=model.model_type,
                    file_path=model.file_path,
                    relative_path=model.relative_path,
                    file_size=model.file_size,
                    file_hash=model.file_hash,
                    format=model.format,
                    is_active=model.is_active,
                    metadata=model.metadata or {},
                    created_at=model.created_at,
                    updated_at=model.updated_at
                ))

            return AvailableModelListResponse(
                models=model_responses,
                total=len(model_responses)
            )

        except Exception as e:
            logger.error(f"Failed to list available models: {str(e)}")
            raise

    def refresh_available_models(self) -> int:
        """Refresh available models from ComfyUI model directories.

        Returns:
            Number of models updated/added
        """
        try:
            logger.info("Starting model discovery and refresh")
            stats = self.model_discovery_service.update_model_database()

            total_updated = stats['added'] + stats['updated']
            logger.info(f"Model refresh completed: {stats}")

            return total_updated

        except Exception as e:
            logger.error(f"Failed to refresh available models: {str(e)}")
            raise