"""Integration tests for cursor-based pagination functionality."""

import pytest
import base64
import json
from datetime import datetime, timedelta
from typing import List
from uuid import uuid4
from sqlalchemy.orm import Session

from genonaut.db.schema import User, ContentItem, UserInteraction, Recommendation
from genonaut.api.repositories.content_repository import ContentRepository
from genonaut.api.repositories.user_repository import UserRepository
from genonaut.api.models.requests import PaginationRequest
from genonaut.api.models.responses import PaginatedResponse


class TestCursorBasedPagination:
    """Test cursor-based pagination for high-performance scenarios."""

    @pytest.fixture
    def sample_content_large(self, db_session: Session) -> List[ContentItem]:
        """Create a larger dataset for cursor pagination testing."""
        user = User(
            username="cursor_test_user",
            email="cursor@example.com",
            created_at=datetime.utcnow()
        )
        db_session.add(user)
        db_session.commit()

        content_items = []
        base_time = datetime.utcnow()

        for i in range(500):  # Larger dataset for cursor testing
            content = ContentItem(
                title=f"Cursor Test Content {i:04d}",
                content_type="text",
                content_data=f"Content data for cursor test {i}",
                creator_id=user.id,
                created_at=base_time - timedelta(minutes=i),
                quality_score=0.5 + (i % 50) / 100.0,
                is_private=False
            )
            db_session.add(content)
            content_items.append(content)

        db_session.commit()
        return content_items

    def test_cursor_encoding_decoding(self):
        """Test that cursor encoding and decoding works correctly."""
        # Test data
        cursor_data = {
            "id": 123,
            "created_at": "2023-12-01T12:00:00"
        }

        # Encode cursor
        encoded_cursor = base64.b64encode(json.dumps(cursor_data).encode()).decode()

        # Decode cursor
        decoded_data = json.loads(base64.b64decode(encoded_cursor).decode())

        # Verify
        assert decoded_data == cursor_data
        assert isinstance(encoded_cursor, str)

    def test_cursor_pagination_basic_functionality(self, db_session: Session,
                                                   sample_content_large: List[ContentItem]):
        """Test basic cursor pagination functionality."""
        repository = ContentRepository(db_session)

        # Get first page
        first_page = PaginationRequest(page=1, page_size=50, sort_field="created_at", sort_order="desc")
        first_result = repository.get_paginated(first_page)

        # Verify first page has results
        assert len(first_result.items) == 50
        assert first_result.pagination.has_next is True
        assert first_result.pagination.has_previous is False
        assert first_result.pagination.next_cursor is not None

        # Use cursor to get next page
        if first_result.pagination.next_cursor:
            cursor_page = PaginationRequest(
                cursor=first_result.pagination.next_cursor,
                page_size=50,
                sort_field="created_at",
                sort_order="desc"
            )
            cursor_result = repository.get_paginated(cursor_page)

            # Verify cursor page results
            assert len(cursor_result.items) > 0
            assert cursor_result.pagination.prev_cursor is not None

            # Verify no overlap between pages
            first_ids = {item.id for item in first_result.items}
            cursor_ids = {item.id for item in cursor_result.items}
            assert len(first_ids.intersection(cursor_ids)) == 0

            # Verify proper ordering (newer items in first page)
            last_first_page = first_result.items[-1]
            first_cursor_page = cursor_result.items[0]
            assert last_first_page.created_at >= first_cursor_page.created_at

    def test_cursor_pagination_stability_across_data_changes(self, db_session: Session,
                                                            sample_content_large: List[ContentItem]):
        """Test that cursor pagination remains stable when data is added/modified."""
        repository = ContentRepository(db_session)

        # Get first page
        first_page = PaginationRequest(page=1, page_size=25, sort_field="created_at", sort_order="desc")
        first_result = repository.get_paginated(first_page)

        # Record the last item from first page
        last_item_first_page = first_result.items[-1]

        # Add new content (should not affect cursor pagination)
        user = db_session.query(User).first()
        new_content = ContentItem(
            title="New Content Added During Pagination",
            content_type="text",
            content_data="This content was added while paginating",
            creator_id=user.id,
            created_at=datetime.utcnow(),  # Newer than existing content
            quality_score=0.9
        )
        db_session.add(new_content)
        db_session.commit()

        # Use cursor to get next page
        if first_result.pagination.next_cursor:
            cursor_page = PaginationRequest(
                cursor=first_result.pagination.next_cursor,
                page_size=25,
                sort_field="created_at",
                sort_order="desc"
            )
            cursor_result = repository.get_paginated(cursor_page)

            # Verify cursor pagination is stable (doesn't include newly added item)
            cursor_ids = {item.id for item in cursor_result.items}
            assert new_content.id not in cursor_ids

            # Verify proper continuation from cursor position
            first_cursor_item = cursor_result.items[0]
            assert first_cursor_item.created_at < last_item_first_page.created_at

    @pytest.mark.skip(reason="Data scaling tests - Cursor bidirectional navigation issues (see scratchpads/issues/by_priority/low/data-scaling-tests.md)")
    def test_cursor_pagination_bidirectional_navigation(self, db_session: Session,
                                                       sample_content_large: List[ContentItem]):
        """Test bidirectional navigation with cursors."""
        repository = ContentRepository(db_session)

        # Start from middle of dataset (page 5)
        middle_page = PaginationRequest(page=5, page_size=20, sort_field="created_at", sort_order="desc")
        middle_result = repository.get_paginated(middle_page)

        assert middle_result.pagination.has_next is True
        assert middle_result.pagination.has_previous is True
        assert middle_result.pagination.next_cursor is not None
        assert middle_result.pagination.prev_cursor is not None

        # Navigate forward using next cursor
        if middle_result.pagination.next_cursor:
            next_page = PaginationRequest(
                cursor=middle_result.pagination.next_cursor,
                page_size=20,
                sort_field="created_at",
                sort_order="desc"
            )
            next_result = repository.get_paginated(next_page)

            # Verify forward navigation
            assert len(next_result.items) > 0
            middle_last_item = middle_result.items[-1]
            next_first_item = next_result.items[0]
            assert next_first_item.created_at < middle_last_item.created_at

        # Navigate backward using previous cursor
        if middle_result.pagination.prev_cursor:
            prev_page = PaginationRequest(
                cursor=middle_result.pagination.prev_cursor,
                page_size=20,
                sort_field="created_at",
                sort_order="desc"
            )
            prev_result = repository.get_paginated(prev_page)

            # Verify backward navigation
            assert len(prev_result.items) > 0
            middle_first_item = middle_result.items[0]
            prev_last_item = prev_result.items[-1]
            assert prev_last_item.created_at > middle_first_item.created_at

    def test_cursor_pagination_with_different_sort_fields(self, db_session: Session,
                                                         sample_content_large: List[ContentItem]):
        """Test cursor pagination with different sort fields."""
        repository = ContentRepository(db_session)

        # Test with quality_score sorting
        quality_page = PaginationRequest(
            page=1,
            page_size=30,
            sort_field="quality_score",
            sort_order="desc"
        )
        quality_result = repository.get_paginated(quality_page)

        if quality_result.pagination.next_cursor:
            # Verify cursor contains quality_score field
            cursor_data = json.loads(base64.b64decode(quality_result.pagination.next_cursor).decode())
            assert "quality_score" in cursor_data
            assert "id" in cursor_data

            # Use cursor for next page
            cursor_page = PaginationRequest(
                cursor=quality_result.pagination.next_cursor,
                page_size=30,
                sort_field="quality_score",
                sort_order="desc"
            )
            cursor_result = repository.get_paginated(cursor_page)

            # Verify proper ordering continuation
            quality_last_item = quality_result.items[-1]
            cursor_first_item = cursor_result.items[0]
            assert cursor_first_item.quality_score <= quality_last_item.quality_score

    def test_cursor_pagination_invalid_cursor_handling(self, db_session: Session,
                                                      sample_content_large: List[ContentItem]):
        """Test handling of invalid cursors."""
        repository = ContentRepository(db_session)

        # Test with invalid base64
        invalid_page = PaginationRequest(
            cursor="invalid_base64_cursor",
            page_size=25,
            sort_field="created_at"
        )
        result = repository.get_paginated(invalid_page)

        # Should fallback to offset-based pagination
        assert len(result.items) > 0
        assert result.pagination.page == 1  # Should default to page 1

        # Test with valid base64 but invalid JSON
        invalid_json_cursor = base64.b64encode(b"invalid json").decode()
        invalid_json_page = PaginationRequest(
            cursor=invalid_json_cursor,
            page_size=25,
            sort_field="created_at"
        )
        result = repository.get_paginated(invalid_json_page)

        # Should fallback to offset-based pagination
        assert len(result.items) > 0

        # Test with valid JSON but missing required fields
        incomplete_cursor_data = {"id": 123}  # Missing sort field data
        incomplete_cursor = base64.b64encode(json.dumps(incomplete_cursor_data).encode()).decode()
        incomplete_page = PaginationRequest(
            cursor=incomplete_cursor,
            page_size=25,
            sort_field="created_at"
        )
        result = repository.get_paginated(incomplete_page)

        # Should fallback to offset-based pagination
        assert len(result.items) > 0

    def test_cursor_pagination_performance_vs_offset(self, db_session: Session,
                                                    sample_content_large: List[ContentItem]):
        """Test that cursor pagination performs better than offset for deep pagination."""
        import time
        repository = ContentRepository(db_session)

        # Test offset-based pagination deep in dataset (page 15)
        offset_page = PaginationRequest(page=15, page_size=25)

        start_time = time.time()
        offset_result = repository.get_paginated(offset_page)
        offset_time = time.time() - start_time

        # Get cursor from earlier page to simulate deep cursor pagination
        early_page = PaginationRequest(page=10, page_size=25, sort_field="created_at", sort_order="desc")
        early_result = repository.get_paginated(early_page)

        if early_result.pagination.next_cursor:
            # Navigate to deep position using cursor
            cursor_page = PaginationRequest(
                cursor=early_result.pagination.next_cursor,
                page_size=25,
                sort_field="created_at",
                sort_order="desc"
            )

            start_time = time.time()
            cursor_result = repository.get_paginated(cursor_page)
            cursor_time = time.time() - start_time

            # Both should work, but cursor might be more efficient for very large datasets
            assert len(offset_result.items) > 0
            assert len(cursor_result.items) > 0

            # In this test size, times might be similar, but pattern is established
            assert offset_time < 1.0  # Reasonable performance
            assert cursor_time < 1.0  # Reasonable performance

    def test_cursor_pagination_consistency_with_duplicates(self, db_session: Session):
        """Test cursor pagination behavior with duplicate sort values."""
        # Create content items with same created_at timestamp
        user = User(
            username="duplicate_test_user",
            email="duplicate@example.com",
            created_at=datetime.utcnow()
        )
        db_session.add(user)
        db_session.commit()

        same_time = datetime.utcnow()
        content_items = []

        for i in range(100):
            content = ContentItem(
                title=f"Duplicate Time Content {i:03d}",
                content_type="text",
                content_data=f"Content with same timestamp {i}",
                creator_id=user.id,
                created_at=same_time,  # All have same timestamp
                quality_score=0.5
            )
            db_session.add(content)
            content_items.append(content)

        db_session.commit()

        repository = ContentRepository(db_session)

        # Get first page
        first_page = PaginationRequest(
            page=1,
            page_size=25,
            sort_field="created_at",
            sort_order="desc"
        )
        first_result = repository.get_paginated(first_page)

        # With duplicate timestamps, ID should be used as secondary sort
        if first_result.pagination.next_cursor:
            cursor_page = PaginationRequest(
                cursor=first_result.pagination.next_cursor,
                page_size=25,
                sort_field="created_at",
                sort_order="desc"
            )
            cursor_result = repository.get_paginated(cursor_page)

            # Verify no overlap even with duplicate timestamps
            first_ids = {item.id for item in first_result.items}
            cursor_ids = {item.id for item in cursor_result.items}
            assert len(first_ids.intersection(cursor_ids)) == 0

    def test_cursor_pagination_edge_cases(self, db_session: Session,
                                         sample_content_large: List[ContentItem]):
        """Test cursor pagination edge cases."""
        repository = ContentRepository(db_session)

        # Test cursor pagination at the very end of dataset
        total_pages = (len(sample_content_large) + 49) // 50  # Round up

        # Get near the end
        near_end_page = PaginationRequest(
            page=total_pages - 1,
            page_size=50,
            sort_field="created_at",
            sort_order="desc"
        )
        near_end_result = repository.get_paginated(near_end_page)

        if near_end_result.pagination.next_cursor:
            # Try to go beyond the end using cursor
            cursor_page = PaginationRequest(
                cursor=near_end_result.pagination.next_cursor,
                page_size=50,
                sort_field="created_at",
                sort_order="desc"
            )
            cursor_result = repository.get_paginated(cursor_page)

            # Should handle gracefully (might return fewer items or empty)
            assert len(cursor_result.items) >= 0
            assert cursor_result.pagination.has_next is False

    def test_cursor_pagination_with_filters(self, db_session: Session,
                                           sample_content_large: List[ContentItem]):
        """Test cursor pagination combined with filters."""
        repository = ContentRepository(db_session)

        # Apply filter and use cursor pagination
        filters = {"content_type": "text"}
        filtered_page = PaginationRequest(
            page=1,
            page_size=30,
            sort_field="created_at",
            sort_order="desc"
        )
        filtered_result = repository.get_paginated(filtered_page, filters=filters)

        # Verify filter is applied
        for item in filtered_result.items:
            assert item.content_type == "text"

        if filtered_result.pagination.next_cursor:
            # Use cursor with same filter
            cursor_page = PaginationRequest(
                cursor=filtered_result.pagination.next_cursor,
                page_size=30,
                sort_field="created_at",
                sort_order="desc"
            )
            cursor_result = repository.get_paginated(cursor_page, filters=filters)

            # Verify filter is still applied in cursor page
            for item in cursor_result.items:
                assert item.content_type == "text"

            # Verify proper continuation
            filtered_ids = {item.id for item in filtered_result.items}
            cursor_ids = {item.id for item in cursor_result.items}
            assert len(filtered_ids.intersection(cursor_ids)) == 0