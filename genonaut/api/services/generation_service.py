"""Generation service for business logic operations."""

from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from sqlalchemy.orm import Session

from genonaut.db.schema import GenerationJob
from genonaut.api.repositories.generation_job_repository import GenerationJobRepository
from genonaut.api.repositories.user_repository import UserRepository
from genonaut.api.repositories.content_repository import ContentRepository
from genonaut.api.exceptions import ValidationError, EntityNotFoundError
from genonaut.api.models.enums import JobType
from genonaut.worker.tasks import run_comfy_job
from genonaut.api.config import get_settings


try:  # pragma: no cover - exercised implicitly
    from celery import current_app as celery_current_app
except ModuleNotFoundError:  # pragma: no cover
    from types import SimpleNamespace

    celery_current_app = SimpleNamespace(control=SimpleNamespace(revoke=lambda *a, **k: None))


settings = get_settings()


def check_celery_workers_available() -> bool:
    """Check if Celery workers are available and responding.

    Returns:
        True if workers are available, False otherwise
    """
    try:
        # Check if we're using the test stub (SimpleNamespace)
        # In test environments, we don't have real Celery, so assume workers are available
        if not hasattr(celery_current_app.control, 'inspect'):
            # This is the test stub, assume workers are available for testing
            return True

        # Try to inspect active workers with a short timeout
        inspect = celery_current_app.control.inspect(timeout=1.0)

        # Try to get stats from workers - this is more reliable than active()
        # stats() returns None if no workers are available
        stats = inspect.stats()

        # If stats is None or empty dict, no workers are available
        if stats is None or not stats:
            return False

        # Double-check with ping to ensure workers are actually responsive
        ping_response = inspect.ping()
        if ping_response is None or not ping_response:
            return False

        return True
    except Exception as e:
        # If any error occurs (connection issues, timeout, etc.), workers are not available
        import logging
        logging.getLogger(__name__).debug(f"Celery worker check failed: {e}")
        return False


class GenerationService:
    """Service class for generation job business logic."""
    
    def __init__(self, db: Session):
        self.repository = GenerationJobRepository(db)
        self.user_repository = UserRepository(db)
        self.content_repository = ContentRepository(db)
    
    def get_generation_job(self, job_id: int) -> GenerationJob:
        """Get generation job by ID.
        
        Args:
            job_id: Generation job ID
            
        Returns:
            Generation job instance
            
        Raises:
            EntityNotFoundError: If job not found
        """
        return self.repository.get_or_404(job_id)
    
    def get_user_jobs(
        self, 
        user_id: UUID, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[GenerationJob]:
        """Get generation jobs for a user.
        
        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Optional status filter
            
        Returns:
            List of generation jobs for the user
            
        Raises:
            EntityNotFoundError: If user not found
        """
        # Verify user exists
        self.user_repository.get_or_404(user_id)
        
        if status:
            # Get jobs by user and status
            user_jobs = self.repository.get_by_user(user_id)
            return [job for job in user_jobs if job.status == status][skip:skip+limit]
        else:
            return self.repository.get_by_user(user_id, skip=skip, limit=limit)
    
    def get_jobs_by_status(
        self, 
        status: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[GenerationJob]:
        """Get generation jobs by status.
        
        Args:
            status: Job status
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of generation jobs with the specified status
        """
        return self.repository.get_by_status(status, skip=skip, limit=limit)
    
    def get_jobs_by_type(
        self,
        job_type: Union[JobType, str],
        skip: int = 0,
        limit: int = 100,
    ) -> List[GenerationJob]:
        """Get generation jobs by type."""

        job_type_value = job_type.value if isinstance(job_type, JobType) else job_type
        return self.repository.get_by_job_type(job_type_value, skip=skip, limit=limit)
    
    def create_generation_job(
        self,
        user_id_or_data = None,
        job_type: Union[JobType, str] = None,
        prompt: str = None,
        params: Optional[Dict[str, Any]] = None,
        *,
        user_id: UUID = None,
        backend: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        checkpoint_model: Optional[str] = None,
        lora_models: Optional[List[Dict[str, Any]]] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        batch_size: Optional[int] = None,
        sampler_params: Optional[Dict[str, Any]] = None,
    ) -> GenerationJob:
        """Create a new generation job.

        Args:
            user_id_or_data: Either user_id UUID OR complete job data dict
            job_type: Type of generation job (if user_id_or_data is user_id)
            prompt: Generation prompt (if user_id_or_data is user_id)
            params: Optional generation parameters (if user_id_or_data is user_id)
            user_id: User ID (keyword-only for API calls)
            sampler_params: Optional sampler configuration overrides

        Returns:
            Created generation job

        Raises:
            ValidationError: If validation fails
            EntityNotFoundError: If user not found
        """
        # Handle different calling patterns
        if isinstance(user_id_or_data, dict):
            # Dictionary case (from tests)
            job_data = user_id_or_data
            final_user_id = job_data.get('user_id')
            final_job_type = job_data.get('job_type')
            final_prompt = job_data.get('prompt')
            final_params = job_data.get('params') or job_data.get('parameters')
            final_backend = job_data.get('backend')
            final_negative_prompt = job_data.get('negative_prompt')
            final_checkpoint_model = job_data.get('checkpoint_model')
            final_lora_models = job_data.get('lora_models')
            final_width = job_data.get('width')
            final_height = job_data.get('height')
            final_batch_size = job_data.get('batch_size')
            final_sampler_params = job_data.get('sampler_params')
        elif user_id is not None:
            # Keyword arguments case (from API routes)
            final_user_id = user_id
            final_job_type = job_type
            final_prompt = prompt
            final_params = params
            final_backend = backend
            final_negative_prompt = negative_prompt
            final_checkpoint_model = checkpoint_model
            final_lora_models = lora_models
            final_width = width
            final_height = height
            final_batch_size = batch_size
            final_sampler_params = sampler_params
        else:
            # Individual params case (from API - old style)
            final_user_id = user_id_or_data
            final_job_type = job_type
            final_prompt = prompt
            final_params = params
            final_backend = backend
            final_negative_prompt = negative_prompt
            final_checkpoint_model = checkpoint_model
            final_lora_models = lora_models
            final_width = width
            final_height = height
            final_batch_size = batch_size
            final_sampler_params = sampler_params

        # Validate required fields
        if final_user_id is None or final_job_type is None or final_prompt is None:
            raise ValidationError("user_id, job_type, and prompt are required")
        
        # Validate user exists and is active
        user = self.user_repository.get_or_404(final_user_id)
        if not user.is_active:
            raise ValidationError("Cannot create generation jobs for inactive users")
        
        # Normalize job type
        job_type_value = final_job_type.value if isinstance(final_job_type, JobType) else str(final_job_type)

        valid_job_types = {enum_value.value for enum_value in JobType}
        if job_type_value not in valid_job_types:
            raise ValidationError(f"Invalid job type. Must be one of: {sorted(valid_job_types)}")
        
        # Validate prompt
        if not final_prompt or len(str(final_prompt).strip()) == 0:
            raise ValidationError("Prompt cannot be empty")
        if len(str(final_prompt)) > 10000:  # Reasonable limit for prompts
            raise ValidationError("Prompt cannot exceed 10,000 characters")
        
        # Validate params
        if final_params is not None and not isinstance(final_params, dict):
            raise ValidationError("params must be a dictionary")

        job_params: Dict[str, Any] = dict(final_params or {})

        # Add backend parameter if provided (defaults to 'kerniegen')
        final_backend = final_backend or job_params.get('backend') or 'kerniegen'
        job_params['backend'] = final_backend

        is_image_job = job_type_value == JobType.IMAGE.value

        if is_image_job:
            # Capture sampler params for downstream workflow generation
            sampler_params_data = final_sampler_params or job_params.get('sampler_params') or {}
            job_params['sampler_params'] = sampler_params_data

            final_negative_prompt = (
                final_negative_prompt
                or job_params.get('negative_prompt')
                or ""
            )
            final_checkpoint_model = (
                final_checkpoint_model
                or job_params.get('checkpoint_model')
            )
            final_lora_models = final_lora_models or job_params.get('lora_models') or []
            final_width = (
                final_width
                or job_params.get('width')
                or settings.comfyui_default_width
            )
            final_height = (
                final_height
                or job_params.get('height')
                or settings.comfyui_default_height
            )
            final_batch_size = (
                final_batch_size
                or job_params.get('batch_size')
                or settings.comfyui_default_batch_size
            )

            job_params.update(
                {
                    'negative_prompt': final_negative_prompt,
                    'checkpoint_model': final_checkpoint_model,
                    'lora_models': final_lora_models,
                    'width': final_width,
                    'height': final_height,
                    'batch_size': final_batch_size,
                }
            )
        else:
            sampler_params_data = final_sampler_params or job_params.get('sampler_params')
            if sampler_params_data is not None:
                job_params['sampler_params'] = sampler_params_data

            final_negative_prompt = final_negative_prompt or job_params.get('negative_prompt')
            final_checkpoint_model = final_checkpoint_model or job_params.get('checkpoint_model')
            final_lora_models = final_lora_models or job_params.get('lora_models')
            final_width = final_width or job_params.get('width')
            final_height = final_height or job_params.get('height')
            final_batch_size = final_batch_size or job_params.get('batch_size')

        # Create the job in the database with pending status
        job = self.repository.create_generation_job(
            user_id=final_user_id,
            job_type=job_type_value,
            prompt=str(final_prompt).strip(),
            params=job_params,
            negative_prompt=final_negative_prompt,
            checkpoint_model=final_checkpoint_model,
            lora_models=final_lora_models,
            width=final_width,
            height=final_height,
            batch_size=final_batch_size,
        )

        # Queue the Celery task (fall back to direct call in test contexts)
        task_result = None
        task_callable = getattr(run_comfy_job, "delay", None)

        if callable(task_callable):
            task_result = task_callable(job.id)
        else:
            # Tests often monkeypatch the task with a simple function
            run_comfy_job(job.id)  # type: ignore[arg-type]

        job.celery_task_id = getattr(task_result, "id", None)
        self.repository.db.commit()

        return job
    
    def update_job_status(
        self, 
        job_id: int, 
        status: str, 
        error_message: Optional[str] = None
    ) -> GenerationJob:
        """Update job status.
        
        Args:
            job_id: Job ID
            status: New status (pending, running, completed, failed, cancelled)
            error_message: Optional error message for failed jobs
            
        Returns:
            Updated generation job
            
        Raises:
            EntityNotFoundError: If job not found
            ValidationError: If status is invalid
        """
        # Validate status
        valid_statuses = ['pending', 'running', 'completed', 'failed', 'cancelled']
        if status not in valid_statuses:
            raise ValidationError(f"Invalid status. Must be one of: {valid_statuses}")
        
        # Validate error message for failed jobs
        if status == 'failed' and not error_message:
            raise ValidationError("Error message is required for failed jobs")
        
        return self.repository.update_status(job_id, status, error_message)
    
    def set_job_result(self, job_id: int, content_id: int) -> GenerationJob:
        """Set the result content for a generation job.
        
        Args:
            job_id: Job ID
            content_id: Content item ID that was generated
            
        Returns:
            Updated generation job
            
        Raises:
            EntityNotFoundError: If job or content not found
        """
        # Verify content exists
        self.content_repository.get_or_404(content_id)
        
        return self.repository.set_result_content(job_id, content_id)
    
    def get_pending_jobs(self, limit: int = 50) -> List[GenerationJob]:
        """Get pending generation jobs.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of pending generation jobs in FIFO order
        """
        return self.repository.get_pending_jobs(limit=limit)
    
    def get_running_jobs(self) -> List[GenerationJob]:
        """Get currently running generation jobs.
        
        Returns:
            List of running generation jobs
        """
        return self.repository.get_running_jobs()
    
    def get_completed_jobs(
        self, 
        user_id: Optional[UUID] = None, 
        days: int = 30, 
        limit: int = 100
    ) -> List[GenerationJob]:
        """Get completed generation jobs.
        
        Args:
            user_id: Optional user ID to filter by
            days: Number of days to look back
            limit: Maximum number of records to return
            
        Returns:
            List of completed generation jobs
        """
        if user_id:
            # Verify user exists
            self.user_repository.get_or_404(user_id)
        
        return self.repository.get_completed_jobs(user_id=user_id, days=days, limit=limit)
    
    def get_failed_jobs(
        self, 
        user_id: Optional[UUID] = None, 
        days: int = 7, 
        limit: int = 100
    ) -> List[GenerationJob]:
        """Get failed generation jobs.
        
        Args:
            user_id: Optional user ID to filter by
            days: Number of days to look back
            limit: Maximum number of records to return
            
        Returns:
            List of failed generation jobs
        """
        if user_id:
            # Verify user exists
            self.user_repository.get_or_404(user_id)
        
        return self.repository.get_failed_jobs(user_id=user_id, days=days, limit=limit)
    
    def get_job_statistics(self, user_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Get generation job statistics.
        
        Args:
            user_id: Optional user ID to filter by
            
        Returns:
            Dictionary with job statistics
        """
        if user_id:
            # Verify user exists
            self.user_repository.get_or_404(user_id)
        
        return self.repository.get_job_statistics(user_id=user_id)
    
    def update_job(
        self,
        job_id: int,
        params: Optional[Dict[str, Any]] = None
    ) -> GenerationJob:
        """Update generation job params.

        Args:
            job_id: Job ID
            params: New params (optional)

        Returns:
            Updated generation job

        Raises:
            EntityNotFoundError: If job not found
            ValidationError: If job cannot be updated
        """
        # Get the job to check its status
        job = self.repository.get_or_404(job_id)

        # Only allow updates for pending jobs
        if job.status != 'pending':
            raise ValidationError("Can only update pending jobs")

        update_data = {}

        # Validate and set params if provided
        if params is not None:
            if not isinstance(params, dict):
                raise ValidationError("params must be a dictionary")
            update_data['params'] = params

        return self.repository.update(job_id, update_data)
    
    def delete_job(self, job_id: int) -> bool:
        """Delete a generation job.
        
        Args:
            job_id: Job ID
            
        Returns:
            True if deleted successfully
            
        Raises:
            EntityNotFoundError: If job not found
            ValidationError: If job cannot be deleted
        """
        # Get the job to check its status
        job = self.repository.get_or_404(job_id)
        
        # Only allow deletion of completed, failed, or cancelled jobs
        if job.status in ['pending', 'running']:
            raise ValidationError("Cannot delete pending or running jobs")
        
        return self.repository.delete(job_id)
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """Get overall generation statistics.
        
        Returns:
            Dictionary with generation statistics
        """
        return self.repository.get_job_statistics()
    
    def start_job_processing(self, job_id: int) -> GenerationJob:
        """Start processing a specific generation job.
        
        Args:
            job_id: Job ID to start processing
            
        Returns:
            Updated generation job with running status
            
        Raises:
            EntityNotFoundError: If job not found
            ValidationError: If job cannot be started
        """
        # Get the job and verify it exists
        job = self.repository.get_or_404(job_id)
        
        # Only allow starting pending jobs
        if job.status != 'pending':
            raise ValidationError(f"Cannot start job with status '{job.status}'. Only pending jobs can be started.")
        
        # Update job status to running and set timestamps
        from datetime import datetime
        
        update_data = {
            'status': 'running',
            'started_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        return self.repository.update(job_id, update_data)
    
    def complete_job(self, job_id: int, content_id: int) -> GenerationJob:
        """Complete a generation job with the resulting content.

        Args:
            job_id: Job ID to complete
            content_id: ID of the content item that was generated

        Returns:
            Updated generation job with completed status

        Raises:
            EntityNotFoundError: If job or content not found
            ValidationError: If job cannot be completed
        """
        # Get the job and verify it exists
        job = self.repository.get_or_404(job_id)

        # Only allow completing running jobs
        if job.status != 'running':
            raise ValidationError(f"Cannot complete job with status '{job.status}'. Only running jobs can be completed.")

        # Verify the result content exists
        self.content_repository.get_or_404(content_id)

        # Update job status to completed and set timestamps and result
        from datetime import datetime

        update_data = {
            'status': 'completed',
            'content_id': content_id,
            'completed_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }

        return self.repository.update(job_id, update_data)
    
    def fail_job(self, job_id: int, error_message: str) -> GenerationJob:
        """Fail a generation job with an error message.
        
        Args:
            job_id: Job ID to fail
            error_message: Error message describing the failure
            
        Returns:
            Updated generation job with failed status
            
        Raises:
            EntityNotFoundError: If job not found
            ValidationError: If job cannot be failed or error message is invalid
        """
        # Get the job and verify it exists
        job = self.repository.get_or_404(job_id)
        
        # Only allow failing running jobs (or pending jobs that failed to start)
        if job.status not in ['running', 'pending']:
            raise ValidationError(f"Cannot fail job with status '{job.status}'. Only running or pending jobs can be failed.")
        
        # Validate error message
        if not error_message or len(error_message.strip()) == 0:
            raise ValidationError("Error message cannot be empty when failing a job")
        
        # Update job status to failed and set error message and timestamp
        from datetime import datetime
        
        update_data = {
            'status': 'failed',
            'error_message': error_message.strip(),
            'completed_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        return self.repository.update(job_id, update_data)

    def cancel_job(self, job_id: int, reason: Optional[str] = None) -> GenerationJob:
        """Cancel a generation job.

        Args:
            job_id: Job ID to cancel
            reason: Optional reason for cancellation

        Returns:
            Updated generation job with cancelled status

        Raises:
            EntityNotFoundError: If job not found
            ValidationError: If job cannot be cancelled
        """
        # Get the job and verify it exists
        job = self.repository.get_or_404(job_id)

        # Only allow cancelling pending or running jobs
        cancellable_statuses = {'pending', 'running', 'processing', 'started'}
        if job.status not in cancellable_statuses:
            allowed = ", ".join(sorted(cancellable_statuses))
            raise ValidationError(
                f"Cannot cancel job with status '{job.status}'. Only {allowed} jobs can be cancelled."
            )

        # Revoke the Celery task if it exists
        if job.celery_task_id:
            try:
                celery_current_app.control.revoke(
                    job.celery_task_id,
                    terminate=True,  # Terminate if already running
                    signal='SIGKILL'  # Force kill the task
                )
            except Exception as e:
                # Log but don't fail if task revocation fails
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to revoke Celery task {job.celery_task_id}: {str(e)}")

        # Update job status to cancelled and set timestamp
        from datetime import datetime

        update_data = {
            'status': 'cancelled',
            'completed_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }

        # Add cancellation reason to error_message field if provided
        if reason:
            update_data['error_message'] = f"Cancelled: {reason.strip()}"

        return self.repository.update(job_id, update_data)

    def get_queue_statistics(self) -> Dict[str, Any]:
        """Get queue statistics showing job counts by status.
        
        Returns:
            Dictionary with queue statistics
        """
        # Count jobs by status
        pending_jobs = self.repository.count({'status': 'pending'})
        running_jobs = self.repository.count({'status': 'running'})
        completed_jobs = self.repository.count({'status': 'completed'})
        failed_jobs = self.repository.count({'status': 'failed'})
        cancelled_jobs = self.repository.count({'status': 'cancelled'})

        total_jobs = pending_jobs + running_jobs + completed_jobs + failed_jobs + cancelled_jobs

        return {
            'pending_jobs': pending_jobs,
            'running_jobs': running_jobs,
            'completed_jobs': completed_jobs,
            'failed_jobs': failed_jobs,
            'cancelled_jobs': cancelled_jobs,
            'total_jobs': total_jobs
        }
    
    def process_job_queue(self, max_jobs: int = 1) -> List[GenerationJob]:
        """Process the job queue by starting pending jobs.
        
        This is a placeholder for job processing logic.
        In a real implementation, this would integrate with background task processing.
        
        Args:
            max_jobs: Maximum number of jobs to start processing
            
        Returns:
            List of jobs that were started
        """
        pending_jobs = self.repository.get_pending_jobs(limit=max_jobs)
        started_jobs = []
        
        for job in pending_jobs:
            try:
                # Use the new start_job_processing method
                updated_job = self.start_job_processing(job.id)
                started_jobs.append(updated_job)
            except Exception:
                # If we can't start the job, continue with the next one
                continue
        
        return started_jobs
