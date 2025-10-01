"""Flagged content repository for database operations."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import asc, desc, func, and_, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from genonaut.api.exceptions import DatabaseError, EntityNotFoundError
from genonaut.api.repositories.base import BaseRepository
from genonaut.api.models.requests import PaginationRequest
from genonaut.api.models.responses import PaginatedResponse, PaginationMeta
from genonaut.db.schema import FlaggedContent, ContentItem, ContentItemAuto


class FlaggedContentRepository(BaseRepository[FlaggedContent, Dict[str, Any], Dict[str, Any]]):
    """Repository for flagged content operations.

    Provides data access methods for managing flagged content records,
    including filtering, pagination, and bulk operations.
    """

    def __init__(self, db: Session):
        """Initialize the repository.

        Args:
            db: SQLAlchemy database session
        """
        super().__init__(db, FlaggedContent)

    def get_by_id(self, flagged_content_id: int) -> Optional[FlaggedContent]:
        """Get flagged content by ID.

        Args:
            flagged_content_id: ID of the flagged content record

        Returns:
            FlaggedContent record or None if not found
        """
        try:
            return self.db.query(FlaggedContent).filter(
                FlaggedContent.id == flagged_content_id
            ).first()
        except SQLAlchemyError as exc:
            raise DatabaseError(f"Failed to get flagged content {flagged_content_id}: {exc}")

    def get_by_content_item(
        self,
        content_item_id: Optional[int] = None,
        content_item_auto_id: Optional[int] = None
    ) -> Optional[FlaggedContent]:
        """Get flagged content by content item reference.

        Args:
            content_item_id: ID of regular content item
            content_item_auto_id: ID of auto content item

        Returns:
            FlaggedContent record or None if not found
        """
        try:
            query = self.db.query(FlaggedContent)

            if content_item_id is not None:
                query = query.filter(FlaggedContent.content_item_id == content_item_id)
            elif content_item_auto_id is not None:
                query = query.filter(FlaggedContent.content_item_auto_id == content_item_auto_id)
            else:
                return None

            return query.first()
        except SQLAlchemyError as exc:
            raise DatabaseError(f"Failed to get flagged content by item: {exc}")

    def get_paginated(
        self,
        pagination: PaginationRequest,
        creator_id: Optional[UUID] = None,
        content_source: Optional[str] = None,
        min_risk_score: Optional[float] = None,
        max_risk_score: Optional[float] = None,
        reviewed: Optional[bool] = None,
        sort_by: str = "flagged_at",
        sort_order: str = "desc"
    ) -> Any:
        """Get paginated list of flagged content with optional filters.

        Args:
            pagination: Pagination parameters
            creator_id: Filter by content creator
            content_source: Filter by source ('regular' or 'auto')
            min_risk_score: Minimum risk score (inclusive)
            max_risk_score: Maximum risk score (inclusive)
            reviewed: Filter by review status
            sort_by: Field to sort by ('risk_score', 'flagged_at', 'problem_count')
            sort_order: Sort order ('asc' or 'desc')

        Returns:
            PaginatedResponse with flagged content items
        """
        try:
            query = self.db.query(FlaggedContent)

            # Apply filters
            if creator_id is not None:
                query = query.filter(FlaggedContent.creator_id == creator_id)

            if content_source is not None:
                query = query.filter(FlaggedContent.content_source == content_source)

            if min_risk_score is not None:
                query = query.filter(FlaggedContent.risk_score >= min_risk_score)

            if max_risk_score is not None:
                query = query.filter(FlaggedContent.risk_score <= max_risk_score)

            if reviewed is not None:
                query = query.filter(FlaggedContent.reviewed == reviewed)

            # Get total count
            total = query.count()

            # Apply sorting
            sort_column = FlaggedContent.flagged_at  # default
            if sort_by == "risk_score":
                sort_column = FlaggedContent.risk_score
            elif sort_by == "problem_count":
                sort_column = FlaggedContent.total_problem_words
            elif sort_by == "flagged_at":
                sort_column = FlaggedContent.flagged_at

            if sort_order == "asc":
                query = query.order_by(asc(sort_column))
            else:
                query = query.order_by(desc(sort_column))

            # Apply pagination
            offset = (pagination.page - 1) * pagination.page_size
            items = query.offset(offset).limit(pagination.page_size).all()

            # Calculate pagination metadata
            has_next = pagination.page < ((total + pagination.page_size - 1) // pagination.page_size)
            has_previous = pagination.page > 1

            pagination_meta = PaginationMeta(
                page=pagination.page,
                page_size=pagination.page_size,
                total_count=total,
                has_next=has_next,
                has_previous=has_previous,
                next_cursor=None,
                prev_cursor=None
            )

            return PaginatedResponse(
                items=items,
                pagination=pagination_meta
            )
        except SQLAlchemyError as exc:
            raise DatabaseError(f"Failed to get paginated flagged content: {exc}")

    def create(
        self,
        content_item_id: Optional[int],
        content_item_auto_id: Optional[int],
        content_source: str,
        flagged_text: str,
        flagged_words: List[str],
        total_problem_words: int,
        total_words: int,
        problem_percentage: float,
        risk_score: float,
        creator_id: UUID
    ) -> FlaggedContent:
        """Create a new flagged content record.

        Args:
            content_item_id: ID of regular content item (or None)
            content_item_auto_id: ID of auto content item (or None)
            content_source: Source type ('regular' or 'auto')
            flagged_text: The text that was flagged
            flagged_words: List of problem words found
            total_problem_words: Count of problem word occurrences
            total_words: Total word count
            problem_percentage: Percentage of problematic words
            risk_score: Calculated risk score
            creator_id: ID of the content creator

        Returns:
            Created FlaggedContent record
        """
        try:
            flagged_content = FlaggedContent(
                content_item_id=content_item_id,
                content_item_auto_id=content_item_auto_id,
                content_source=content_source,
                flagged_text=flagged_text,
                flagged_words=flagged_words,
                total_problem_words=total_problem_words,
                total_words=total_words,
                problem_percentage=problem_percentage,
                risk_score=risk_score,
                creator_id=creator_id,
                flagged_at=datetime.utcnow(),
                reviewed=False
            )

            self.db.add(flagged_content)
            self.db.commit()
            self.db.refresh(flagged_content)

            return flagged_content
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise DatabaseError(f"Failed to create flagged content: {exc}")

    def update_review_status(
        self,
        flagged_content_id: int,
        reviewed: bool,
        reviewed_by: UUID,
        notes: Optional[str] = None
    ) -> FlaggedContent:
        """Update review status of flagged content.

        Args:
            flagged_content_id: ID of the flagged content record
            reviewed: Whether content has been reviewed
            reviewed_by: ID of the reviewer
            notes: Optional admin notes

        Returns:
            Updated FlaggedContent record

        Raises:
            EntityNotFoundError: If flagged content not found
        """
        try:
            flagged_content = self.get_by_id(flagged_content_id)
            if not flagged_content:
                raise EntityNotFoundError("FlaggedContent", flagged_content_id)

            flagged_content.reviewed = reviewed
            flagged_content.reviewed_by = reviewed_by
            flagged_content.reviewed_at = datetime.utcnow()

            if notes is not None:
                flagged_content.notes = notes

            self.db.commit()
            self.db.refresh(flagged_content)

            return flagged_content
        except EntityNotFoundError:
            raise
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise DatabaseError(f"Failed to update review status: {exc}")

    def delete(self, flagged_content_id: int) -> bool:
        """Delete flagged content record and associated content item.

        Args:
            flagged_content_id: ID of the flagged content record

        Returns:
            True if deleted successfully

        Raises:
            EntityNotFoundError: If flagged content not found
        """
        try:
            flagged_content = self.get_by_id(flagged_content_id)
            if not flagged_content:
                raise EntityNotFoundError("FlaggedContent", flagged_content_id)

            # Delete the original content item (will cascade to flagged_content)
            if flagged_content.content_item_id:
                content_item = self.db.query(ContentItem).filter(
                    ContentItem.id == flagged_content.content_item_id
                ).first()
                if content_item:
                    self.db.delete(content_item)
            elif flagged_content.content_item_auto_id:
                content_item_auto = self.db.query(ContentItemAuto).filter(
                    ContentItemAuto.id == flagged_content.content_item_auto_id
                ).first()
                if content_item_auto:
                    self.db.delete(content_item_auto)

            self.db.commit()
            return True
        except EntityNotFoundError:
            raise
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise DatabaseError(f"Failed to delete flagged content: {exc}")

    def bulk_delete(self, flagged_content_ids: List[int]) -> Tuple[int, List[Dict[str, Any]]]:
        """Delete multiple flagged content records and their content items.

        Args:
            flagged_content_ids: List of flagged content IDs to delete

        Returns:
            Tuple of (successful_count, errors_list)
            errors_list contains dicts with 'id' and 'error' keys
        """
        deleted_count = 0
        errors = []

        for flagged_id in flagged_content_ids:
            try:
                self.delete(flagged_id)
                deleted_count += 1
            except (EntityNotFoundError, DatabaseError) as exc:
                errors.append({
                    'id': flagged_id,
                    'error': str(exc)
                })

        return (deleted_count, errors)

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about flagged content.

        Returns:
            Dictionary with statistics:
            - total_flagged: Total number of flagged items
            - unreviewed_count: Number of unreviewed items
            - average_risk_score: Average risk score across all items
            - high_risk_count: Number of items with risk_score >= 75
            - by_source: Breakdown by content source
        """
        try:
            total_flagged = self.db.query(func.count(FlaggedContent.id)).scalar()
            unreviewed_count = self.db.query(func.count(FlaggedContent.id)).filter(
                FlaggedContent.reviewed == False
            ).scalar()
            average_risk = self.db.query(func.avg(FlaggedContent.risk_score)).scalar()
            high_risk_count = self.db.query(func.count(FlaggedContent.id)).filter(
                FlaggedContent.risk_score >= 75
            ).scalar()

            # Count by source
            source_counts = self.db.query(
                FlaggedContent.content_source,
                func.count(FlaggedContent.id)
            ).group_by(FlaggedContent.content_source).all()

            by_source = {source: count for source, count in source_counts}

            return {
                'total_flagged': total_flagged or 0,
                'unreviewed_count': unreviewed_count or 0,
                'average_risk_score': round(float(average_risk or 0), 2),
                'high_risk_count': high_risk_count or 0,
                'by_source': by_source
            }
        except SQLAlchemyError as exc:
            raise DatabaseError(f"Failed to get flagged content statistics: {exc}")
