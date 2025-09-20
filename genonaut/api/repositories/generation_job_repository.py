"""Generation job repository for database operations."""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, desc, asc
from datetime import datetime, timedelta

from genonaut.db.schema import GenerationJob
from genonaut.api.repositories.base import BaseRepository
from genonaut.api.exceptions import DatabaseError


class GenerationJobRepository(BaseRepository[GenerationJob, Dict[str, Any], Dict[str, Any]]):
    """Repository for GenerationJob entity operations."""
    
    def __init__(self, db: Session):
        super().__init__(db, GenerationJob)
    
    def get_by_user(self, user_id: int, skip: int = 0, limit: int = 100) -> List[GenerationJob]:
        """Get generation jobs for a user.
        
        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of generation jobs for the user
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return (
                self.db.query(GenerationJob)
                .filter(GenerationJob.user_id == user_id)
                .order_by(desc(GenerationJob.created_at))
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get generation jobs for user {user_id}: {str(e)}")

    def get_by_user_id(self, user_id: int, skip: int = 0, limit: int = 100) -> List[GenerationJob]:
        return self.get_by_user(user_id, skip=skip, limit=limit)
    
    def get_by_status(self, status: str, skip: int = 0, limit: int = 100) -> List[GenerationJob]:
        """Get generation jobs by status.
        
        Args:
            status: Job status (pending, running, completed, failed, cancelled)
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of generation jobs with the specified status
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return (
                self.db.query(GenerationJob)
                .filter(GenerationJob.status == status)
                .order_by(desc(GenerationJob.created_at))
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get generation jobs by status {status}: {str(e)}")
    
    def get_by_job_type(self, job_type: str, skip: int = 0, limit: int = 100) -> List[GenerationJob]:
        """Get generation jobs by type.
        
        Args:
            job_type: Job type (text, image, video, audio)
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of generation jobs of the specified type
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return (
                self.db.query(GenerationJob)
                .filter(GenerationJob.job_type == job_type)
                .order_by(desc(GenerationJob.created_at))
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get generation jobs by type {job_type}: {str(e)}")
    
    def get_pending_jobs(self, limit: int = 50) -> List[GenerationJob]:
        """Get pending generation jobs.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of pending generation jobs
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return (
                self.db.query(GenerationJob)
                .filter(GenerationJob.status == 'pending')
                .order_by(asc(GenerationJob.created_at))  # FIFO order
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get pending generation jobs: {str(e)}")
    
    def get_running_jobs(self) -> List[GenerationJob]:
        """Get currently running generation jobs.
        
        Returns:
            List of running generation jobs
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return (
                self.db.query(GenerationJob)
                .filter(GenerationJob.status == 'running')
                .order_by(asc(GenerationJob.started_at))
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get running generation jobs: {str(e)}")
    
    def get_completed_jobs(
        self, 
        user_id: Optional[int] = None, 
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
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            query = (
                self.db.query(GenerationJob)
                .filter(
                    GenerationJob.status == 'completed',
                    GenerationJob.completed_at >= cutoff_date
                )
            )
            
            if user_id:
                query = query.filter(GenerationJob.user_id == user_id)
            
            return query.order_by(desc(GenerationJob.completed_at)).limit(limit).all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get completed generation jobs: {str(e)}")
    
    def get_failed_jobs(
        self, 
        user_id: Optional[int] = None, 
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
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            query = (
                self.db.query(GenerationJob)
                .filter(
                    GenerationJob.status == 'failed',
                    GenerationJob.created_at >= cutoff_date
                )
            )
            
            if user_id:
                query = query.filter(GenerationJob.user_id == user_id)
            
            return query.order_by(desc(GenerationJob.created_at)).limit(limit).all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get failed generation jobs: {str(e)}")
    
    def update_status(
        self, 
        job_id: int, 
        status: str, 
        error_message: Optional[str] = None
    ) -> GenerationJob:
        """Update job status.
        
        Args:
            job_id: Job ID
            status: New status
            error_message: Optional error message for failed jobs
            
        Returns:
            Updated generation job
            
        Raises:
            EntityNotFoundError: If job not found
            DatabaseError: If database operation fails
        """
        try:
            job = self.get_or_404(job_id)
            
            job.status = status
            if error_message:
                job.error_message = error_message
            
            # Update timestamps based on status
            if status == 'running' and not job.started_at:
                job.started_at = datetime.utcnow()
            elif status in ['completed', 'failed'] and not job.completed_at:
                job.completed_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(job)
            return job
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to update status for job {job_id}: {str(e)}")
    
    def set_result_content(self, job_id: int, content_id: int) -> GenerationJob:
        """Set the result content for a generation job.
        
        Args:
            job_id: Job ID
            content_id: Content item ID that was generated
            
        Returns:
            Updated generation job
            
        Raises:
            EntityNotFoundError: If job not found
            DatabaseError: If database operation fails
        """
        try:
            job = self.get_or_404(job_id)
            job.result_content_id = content_id
            
            self.db.commit()
            self.db.refresh(job)
            return job
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to set result content for job {job_id}: {str(e)}")
    
    def get_job_statistics(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Get generation job statistics.
        
        Args:
            user_id: Optional user ID to filter by
            
        Returns:
            Dictionary with job statistics
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            query = self.db.query(GenerationJob)
            if user_id:
                query = query.filter(GenerationJob.user_id == user_id)
            
            # Status breakdown
            status_stats = (
                query.with_entities(
                    GenerationJob.status,
                    func.count(GenerationJob.id).label('count')
                )
                .group_by(GenerationJob.status)
                .all()
            )
            
            status_breakdown = {row.status: row.count for row in status_stats}
            
            # Job type breakdown
            type_stats = (
                query.with_entities(
                    GenerationJob.job_type,
                    func.count(GenerationJob.id).label('count')
                )
                .group_by(GenerationJob.job_type)
                .all()
            )
            
            type_breakdown = {row.job_type: row.count for row in type_stats}
            
            # Total jobs
            total_jobs = query.count()
            
            # Average processing time for completed jobs
            completed_jobs = query.filter(
                GenerationJob.status == 'completed',
                GenerationJob.started_at.isnot(None),
                GenerationJob.completed_at.isnot(None)
            )
            
            avg_processing_time = None
            if completed_jobs.count() > 0:
                # Calculate average processing time in seconds
                processing_times = []
                for job in completed_jobs:
                    if job.started_at and job.completed_at:
                        duration = (job.completed_at - job.started_at).total_seconds()
                        processing_times.append(duration)
                
                if processing_times:
                    avg_processing_time = sum(processing_times) / len(processing_times)
            
            return {
                'total_jobs': total_jobs,
                'status_breakdown': status_breakdown,
                'type_breakdown': type_breakdown,
                'average_processing_time_seconds': avg_processing_time
            }
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get job statistics: {str(e)}")
    
    def create_generation_job(
        self,
        user_id: int,
        job_type: str,
        prompt: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> GenerationJob:
        """Create a new generation job.
        
        Args:
            user_id: User ID
            job_type: Type of generation job
            prompt: Generation prompt
            parameters: Optional generation parameters
            
        Returns:
            Created generation job
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            job_data = {
                'user_id': user_id,
                'job_type': job_type,
                'prompt': prompt,
                'parameters': parameters or {},
                'status': 'pending'
            }
            
            return self.create(job_data)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to create generation job: {str(e)}")
