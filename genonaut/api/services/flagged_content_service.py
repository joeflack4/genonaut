"""Flagged content service for business logic operations."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from genonaut.api.exceptions import EntityNotFoundError, ValidationError, DatabaseError
from genonaut.api.repositories.flagged_content_repository import FlaggedContentRepository
from genonaut.api.repositories.content_repository import ContentRepository
from genonaut.api.models.requests import PaginationRequest
from genonaut.api.models.responses import PaginatedResponse
from genonaut.db.schema import FlaggedContent, ContentItem, ContentItemAuto
from genonaut.utils.flagging import (
    load_flag_words,
    analyze_content,
    get_default_flag_words_path
)


class FlaggedContentService:
    """Service class for flagged content business logic.

    Handles content scanning, flagging, review workflows, and management
    of flagged content records.
    """

    def __init__(self, db: Session, flag_words_path: Optional[str] = None):
        """Initialize the service.

        Args:
            db: SQLAlchemy database session
            flag_words_path: Optional path to flag-words.txt file.
                           If None, uses default path from get_default_flag_words_path()

        Raises:
            ValidationError: If flag words file not found or invalid
        """
        self.db = db
        self.repository = FlaggedContentRepository(db)
        self.content_repository = ContentRepository(db)

        # Load flag words
        if flag_words_path is None:
            flag_words_path = get_default_flag_words_path()

        if flag_words_path is None:
            raise ValidationError(
                "Flag words file not found. Please create flag-words.txt in project root."
            )

        try:
            self.flag_words = load_flag_words(flag_words_path)
        except (FileNotFoundError, ValueError) as exc:
            raise ValidationError(f"Failed to load flag words: {exc}")

    def scan_content_items(
        self,
        content_types: List[str] = None,
        force_rescan: bool = False
    ) -> Dict[str, Any]:
        """Scan existing content items for problematic words.

        Args:
            content_types: List of content types to scan ('regular', 'auto', or both).
                          Defaults to ['regular', 'auto']
            force_rescan: If True, rescan items that are already flagged

        Returns:
            Dictionary with scan results:
            {
                'items_scanned': int,
                'items_flagged': int,
                'processing_time_ms': float
            }
        """
        import time
        start_time = time.time()

        if content_types is None:
            content_types = ['regular', 'auto']

        items_scanned = 0
        items_flagged = 0

        # Scan regular content items
        if 'regular' in content_types:
            regular_items = self.content_repository.get_multi(skip=0, limit=10000)
            for item in regular_items:
                items_scanned += 1

                # Skip if already flagged and not forcing rescan
                if not force_rescan:
                    existing = self.repository.get_by_content_item(content_item_id=item.id)
                    if existing:
                        continue

                # Check if item should be flagged
                text_to_check = self._extract_text_from_content(item)
                if text_to_check:
                    result = self._flag_content_if_needed(
                        text=text_to_check,
                        content_item_id=item.id,
                        content_item_auto_id=None,
                        content_source='regular',
                        creator_id=item.creator_id
                    )
                    if result:
                        items_flagged += 1

        # Scan auto content items
        if 'auto' in content_types:
            from genonaut.db.schema import ContentItemAuto
            auto_repo = ContentRepository(self.db, model=ContentItemAuto)
            auto_items = auto_repo.get_multi(skip=0, limit=10000)
            for item in auto_items:
                items_scanned += 1

                # Skip if already flagged and not forcing rescan
                if not force_rescan:
                    existing = self.repository.get_by_content_item(content_item_auto_id=item.id)
                    if existing:
                        continue

                # Check if item should be flagged
                text_to_check = self._extract_text_from_content(item)
                if text_to_check:
                    result = self._flag_content_if_needed(
                        text=text_to_check,
                        content_item_id=None,
                        content_item_auto_id=item.id,
                        content_source='auto',
                        creator_id=item.creator_id
                    )
                    if result:
                        items_flagged += 1

        end_time = time.time()
        processing_time_ms = (end_time - start_time) * 1000

        return {
            'items_scanned': items_scanned,
            'items_flagged': items_flagged,
            'processing_time_ms': round(processing_time_ms, 2)
        }

    def flag_content_item(
        self,
        text: str,
        content_item_id: Optional[int] = None,
        content_item_auto_id: Optional[int] = None,
        content_source: str = 'regular',
        creator_id: Optional[UUID] = None
    ) -> Optional[FlaggedContent]:
        """Flag a single content item if it contains problematic words.

        Args:
            text: The text to analyze
            content_item_id: ID of regular content item
            content_item_auto_id: ID of auto content item
            content_source: Source type ('regular' or 'auto')
            creator_id: ID of content creator

        Returns:
            FlaggedContent record if flagged, None if clean

        Raises:
            ValidationError: If validation fails
        """
        if content_source not in ('regular', 'auto'):
            raise ValidationError("content_source must be 'regular' or 'auto'")

        if content_item_id is None and content_item_auto_id is None:
            raise ValidationError("Either content_item_id or content_item_auto_id must be provided")

        if creator_id is None:
            raise ValidationError("creator_id is required")

        return self._flag_content_if_needed(
            text=text,
            content_item_id=content_item_id,
            content_item_auto_id=content_item_auto_id,
            content_source=content_source,
            creator_id=creator_id
        )

    def get_flagged_content(
        self,
        pagination: PaginationRequest,
        creator_id: Optional[UUID] = None,
        content_source: Optional[str] = None,
        min_risk_score: Optional[float] = None,
        max_risk_score: Optional[float] = None,
        reviewed: Optional[bool] = None,
        sort_by: str = "flagged_at",
        sort_order: str = "desc"
    ) -> Any:  # Returns PaginatedResponse[FlaggedContent]
        """Get paginated list of flagged content with filters.

        Args:
            pagination: Pagination parameters
            creator_id: Filter by content creator
            content_source: Filter by source ('regular' or 'auto')
            min_risk_score: Minimum risk score
            max_risk_score: Maximum risk score
            reviewed: Filter by review status
            sort_by: Field to sort by
            sort_order: Sort order ('asc' or 'desc')

        Returns:
            PaginatedResponse with flagged content items

        Raises:
            ValidationError: If parameters are invalid
        """
        # Validate sort parameters
        valid_sort_fields = {'risk_score', 'flagged_at', 'problem_count'}
        if sort_by not in valid_sort_fields:
            raise ValidationError(f"sort_by must be one of: {valid_sort_fields}")

        if sort_order not in ('asc', 'desc'):
            raise ValidationError("sort_order must be 'asc' or 'desc'")

        if content_source is not None and content_source not in ('regular', 'auto'):
            raise ValidationError("content_source must be 'regular' or 'auto'")

        return self.repository.get_paginated(
            pagination=pagination,
            creator_id=creator_id,
            content_source=content_source,
            min_risk_score=min_risk_score,
            max_risk_score=max_risk_score,
            reviewed=reviewed,
            sort_by=sort_by,
            sort_order=sort_order
        )

    def get_flagged_content_by_id(self, flagged_content_id: int) -> FlaggedContent:
        """Get single flagged content by ID.

        Args:
            flagged_content_id: ID of flagged content

        Returns:
            FlaggedContent record

        Raises:
            EntityNotFoundError: If not found
        """
        flagged_content = self.repository.get_by_id(flagged_content_id)
        if not flagged_content:
            raise EntityNotFoundError(f"Flagged content {flagged_content_id} not found")
        return flagged_content

    def review_flagged_content(
        self,
        flagged_content_id: int,
        reviewed: bool,
        reviewed_by: UUID,
        notes: Optional[str] = None
    ) -> FlaggedContent:
        """Mark flagged content as reviewed.

        Args:
            flagged_content_id: ID of flagged content
            reviewed: Review status
            reviewed_by: ID of reviewer
            notes: Optional admin notes

        Returns:
            Updated FlaggedContent record

        Raises:
            EntityNotFoundError: If not found
        """
        return self.repository.update_review_status(
            flagged_content_id=flagged_content_id,
            reviewed=reviewed,
            reviewed_by=reviewed_by,
            notes=notes
        )

    def delete_flagged_content(self, flagged_content_id: int) -> bool:
        """Delete flagged content and associated content item.

        Args:
            flagged_content_id: ID of flagged content

        Returns:
            True if deleted successfully

        Raises:
            EntityNotFoundError: If not found
        """
        return self.repository.delete(flagged_content_id)

    def bulk_delete_flagged_content(
        self,
        flagged_content_ids: List[int]
    ) -> Dict[str, Any]:
        """Delete multiple flagged content items.

        Args:
            flagged_content_ids: List of IDs to delete

        Returns:
            Dictionary with results:
            {
                'deleted_count': int,
                'errors': List[Dict[str, Any]]
            }
        """
        deleted_count, errors = self.repository.bulk_delete(flagged_content_ids)
        return {
            'deleted_count': deleted_count,
            'errors': errors
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about flagged content.

        Returns:
            Dictionary with statistics
        """
        return self.repository.get_statistics()

    # Private helper methods

    def _extract_text_from_content(self, content_item) -> str:
        """Extract text to check from content item.

        Checks item_metadata for 'prompt' field, falls back to title.

        Args:
            content_item: ContentItem or ContentItemAuto instance

        Returns:
            Text to analyze
        """
        # Try to get prompt from metadata
        if content_item.item_metadata and isinstance(content_item.item_metadata, dict):
            prompt = content_item.item_metadata.get('prompt')
            if prompt:
                return str(prompt)

        # Fall back to title
        return content_item.title or ""

    def _flag_content_if_needed(
        self,
        text: str,
        content_item_id: Optional[int],
        content_item_auto_id: Optional[int],
        content_source: str,
        creator_id: UUID
    ) -> Optional[FlaggedContent]:
        """Analyze text and create flagged record if needed.

        Args:
            text: Text to analyze
            content_item_id: ID of regular content item
            content_item_auto_id: ID of auto content item
            content_source: Source type
            creator_id: Creator ID

        Returns:
            FlaggedContent if flagged, None if clean
        """
        # Analyze content
        analysis = analyze_content(text, self.flag_words)

        # Only flag if problems found
        if not analysis['should_flag']:
            return None

        # Create flagged content record
        try:
            flagged_content = self.repository.create(
                content_item_id=content_item_id,
                content_item_auto_id=content_item_auto_id,
                content_source=content_source,
                flagged_text=text,
                flagged_words=analysis['flagged_words'],
                total_problem_words=analysis['total_problem_words'],
                total_words=analysis['total_words'],
                problem_percentage=analysis['problem_percentage'],
                risk_score=analysis['risk_score'],
                creator_id=creator_id
            )
            return flagged_content
        except DatabaseError as exc:
            # If already flagged, return None (don't create duplicate)
            return None
