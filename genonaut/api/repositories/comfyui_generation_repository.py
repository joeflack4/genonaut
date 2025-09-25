"""Repository for ComfyUI generation request operations."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, and_

from genonaut.db.schema import ComfyUIGenerationRequest
from genonaut.api.repositories.base import BaseRepository
from genonaut.api.exceptions import DatabaseError
from genonaut.api.models.requests import PaginationRequest
from genonaut.api.models.responses import PaginatedResponse


class ComfyUIGenerationRepository(BaseRepository[ComfyUIGenerationRequest, Dict[str, Any], Dict[str, Any]]):
    """Repository for ComfyUI generation request data access operations."""

    def __init__(self, db: Session):
        """Initialize repository with database session."""
        super().__init__(db, ComfyUIGenerationRequest)

    def create_generation_request(self, **kwargs) -> ComfyUIGenerationRequest:
        """Create a new ComfyUI generation request.

        Args:
            **kwargs: Generation request fields

        Returns:
            Created generation request

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            request = ComfyUIGenerationRequest(**kwargs)
            self.db.add(request)
            self.db.flush()
            return request
        except Exception as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to create generation request: {str(e)}")

    def get_by_user(
        self,
        user_id: UUID,
        pagination: Optional[PaginationRequest] = None,
        status: Optional[str] = None
    ) -> PaginatedResponse[ComfyUIGenerationRequest]:
        """Get generation requests for a specific user.

        Args:
            user_id: User ID
            pagination: Pagination parameters
            status: Optional status filter

        Returns:
            Paginated list of generation requests

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            query = self.db.query(ComfyUIGenerationRequest).filter(
                ComfyUIGenerationRequest.user_id == user_id
            )

            if status:
                query = query.filter(ComfyUIGenerationRequest.status == status)

            # Apply pagination
            if pagination:
                total_count = query.count()

                # Apply sorting
                if pagination.sort_by:
                    if hasattr(ComfyUIGenerationRequest, pagination.sort_by):
                        column = getattr(ComfyUIGenerationRequest, pagination.sort_by)
                        if pagination.sort_desc:
                            query = query.order_by(desc(column))
                        else:
                            query = query.order_by(asc(column))
                else:
                    # Default sort by created_at desc
                    query = query.order_by(desc(ComfyUIGenerationRequest.created_at))

                items = query.offset(pagination.skip).limit(pagination.limit).all()

                return PaginatedResponse(
                    items=items,
                    pagination_meta=pagination.to_response_meta(total_count)
                )
            else:
                # No pagination, return all (with reasonable limit)
                items = query.order_by(desc(ComfyUIGenerationRequest.created_at)).limit(1000).all()
                return PaginatedResponse(
                    items=items,
                    pagination_meta=None
                )

        except Exception as e:
            raise DatabaseError(f"Failed to get generation requests for user {user_id}: {str(e)}")

    def get_by_comfyui_prompt_id(self, prompt_id: str) -> Optional[ComfyUIGenerationRequest]:
        """Get generation request by ComfyUI prompt ID.

        Args:
            prompt_id: ComfyUI prompt ID

        Returns:
            Generation request or None if not found

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return self.db.query(ComfyUIGenerationRequest).filter(
                ComfyUIGenerationRequest.comfyui_prompt_id == prompt_id
            ).first()
        except Exception as e:
            raise DatabaseError(f"Failed to get generation request by prompt ID {prompt_id}: {str(e)}")

    def get_pending_requests(self, limit: int = 100) -> List[ComfyUIGenerationRequest]:
        """Get pending generation requests for processing.

        Args:
            limit: Maximum number of requests to return

        Returns:
            List of pending generation requests

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return self.db.query(ComfyUIGenerationRequest).filter(
                ComfyUIGenerationRequest.status == 'pending'
            ).order_by(asc(ComfyUIGenerationRequest.created_at)).limit(limit).all()
        except Exception as e:
            raise DatabaseError(f"Failed to get pending generation requests: {str(e)}")

    def get_processing_requests(self, limit: int = 100) -> List[ComfyUIGenerationRequest]:
        """Get currently processing generation requests.

        Args:
            limit: Maximum number of requests to return

        Returns:
            List of processing generation requests

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return self.db.query(ComfyUIGenerationRequest).filter(
                ComfyUIGenerationRequest.status == 'processing'
            ).order_by(asc(ComfyUIGenerationRequest.started_at)).limit(limit).all()
        except Exception as e:
            raise DatabaseError(f"Failed to get processing generation requests: {str(e)}")

    def update_status(
        self,
        request_id: int,
        status: str,
        **kwargs
    ) -> ComfyUIGenerationRequest:
        """Update generation request status and related fields.

        Args:
            request_id: Generation request ID
            status: New status
            **kwargs: Additional fields to update

        Returns:
            Updated generation request

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            request = self.get_or_404(request_id)
            request.status = status

            # Update timestamp fields based on status
            from datetime import datetime
            now = datetime.utcnow()

            if status == 'processing' and not request.started_at:
                request.started_at = now
            elif status in ['completed', 'failed', 'cancelled'] and not request.completed_at:
                request.completed_at = now

            request.updated_at = now

            # Update any additional fields
            for key, value in kwargs.items():
                if hasattr(request, key):
                    setattr(request, key, value)

            self.db.flush()
            return request
        except Exception as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to update generation request status: {str(e)}")

    def search_by_prompt(
        self,
        query_text: str,
        user_id: Optional[UUID] = None,
        pagination: Optional[PaginationRequest] = None
    ) -> PaginatedResponse[ComfyUIGenerationRequest]:
        """Search generation requests by prompt text using full-text search.

        Args:
            query_text: Text to search for in prompts
            user_id: Optional user ID filter
            pagination: Pagination parameters

        Returns:
            Paginated list of matching generation requests

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Use PostgreSQL full-text search
            from sqlalchemy import func, text

            query = self.db.query(ComfyUIGenerationRequest).filter(
                func.to_tsvector('english',
                    func.coalesce(ComfyUIGenerationRequest.prompt, '') + ' ' +
                    func.coalesce(ComfyUIGenerationRequest.negative_prompt, '')
                ).match(query_text)
            )

            if user_id:
                query = query.filter(ComfyUIGenerationRequest.user_id == user_id)

            if pagination:
                total_count = query.count()
                items = query.order_by(
                    desc(ComfyUIGenerationRequest.created_at)
                ).offset(pagination.skip).limit(pagination.limit).all()

                return PaginatedResponse(
                    items=items,
                    pagination_meta=pagination.to_response_meta(total_count)
                )
            else:
                items = query.order_by(desc(ComfyUIGenerationRequest.created_at)).limit(100).all()
                return PaginatedResponse(
                    items=items,
                    pagination_meta=None
                )

        except Exception as e:
            raise DatabaseError(f"Failed to search generation requests: {str(e)}")

    def get_statistics(self, user_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Get generation statistics.

        Args:
            user_id: Optional user ID filter

        Returns:
            Dictionary with generation statistics

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            from sqlalchemy import func

            query = self.db.query(ComfyUIGenerationRequest)
            if user_id:
                query = query.filter(ComfyUIGenerationRequest.user_id == user_id)

            # Get status counts
            status_counts = dict(
                query.with_entities(
                    ComfyUIGenerationRequest.status,
                    func.count(ComfyUIGenerationRequest.id)
                ).group_by(ComfyUIGenerationRequest.status).all()
            )

            # Get total count
            total_count = query.count()

            # Get recent activity (last 24 hours)
            from datetime import datetime, timedelta
            yesterday = datetime.utcnow() - timedelta(days=1)
            recent_count = query.filter(
                ComfyUIGenerationRequest.created_at >= yesterday
            ).count()

            return {
                "total_requests": total_count,
                "status_counts": status_counts,
                "recent_activity": recent_count
            }

        except Exception as e:
            raise DatabaseError(f"Failed to get generation statistics: {str(e)}")