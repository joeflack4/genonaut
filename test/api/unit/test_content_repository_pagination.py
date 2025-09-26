"""Tests for ContentRepository pagination functionality."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
from uuid import uuid4

from genonaut.api.repositories.content_repository import ContentRepository
from genonaut.api.models.requests import PaginationRequest
from genonaut.api.models.responses import PaginatedResponse
from genonaut.api.exceptions import DatabaseError
from genonaut.db.schema import ContentItem


class MockContentItem:
    """Mock ContentItem for testing."""
    __name__ = "ContentItem"

    def __init__(self, id=1, creator_id=None, title="Test Content", content_type="text",
                 quality_score=0.8, created_at=None, is_private=False, tags=None):
        self.id = id
        self.creator_id = creator_id or uuid4()
        self.title = title
        self.content_type = content_type
        self.quality_score = quality_score
        self.created_at = created_at or datetime.utcnow()
        self.is_private = is_private
        self.tags = tags or []
        self.item_metadata = {}


# Add class attributes for hasattr() checks
# Create mock columns that work with SQLAlchemy operations
class MockColumn:
    def __eq__(self, other):
        return Mock()
    def __lt__(self, other):
        return Mock()
    def __gt__(self, other):
        return Mock()
    def ilike(self, pattern):
        return Mock()
    def op(self, operator):
        def operation(value):
            return Mock()
        return operation
    def is_(self, value):
        return Mock()

MockContentItem.id = MockColumn()
MockContentItem.creator_id = MockColumn()
MockContentItem.title = MockColumn()
MockContentItem.content_type = MockColumn()
MockContentItem.quality_score = MockColumn()
MockContentItem.created_at = MockColumn()
MockContentItem.is_private = MockColumn()
MockContentItem.tags = MockColumn()
MockContentItem.item_metadata = MockColumn()


class TestContentRepositoryPagination:
    """Test ContentRepository pagination functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.mock_query = Mock()
        self.mock_db.query.return_value = self.mock_query
        self.repository = ContentRepository(self.mock_db, MockContentItem)

    @patch('genonaut.api.repositories.base.desc')
    @patch('genonaut.api.repositories.base.asc')
    def test_get_by_creator_paginated(self, mock_asc, mock_desc):
        """Test get_by_creator_paginated with new pagination support."""
        # Mock SQLAlchemy functions
        mock_desc.return_value = Mock()
        mock_asc.return_value = Mock()
        # Arrange
        creator_id = uuid4()
        mock_items = [MockContentItem(i, creator_id) for i in range(1, 4)]

        self.mock_query.filter.return_value = self.mock_query
        self.mock_query.order_by.return_value = self.mock_query
        self.mock_query.offset.return_value = self.mock_query
        self.mock_query.limit.return_value = self.mock_query
        self.mock_query.all.return_value = mock_items
        self.mock_query.count.return_value = 25

        pagination_request = PaginationRequest(page=1, page_size=10)

        # Act
        result = self.repository.get_by_creator_paginated(creator_id, pagination_request)

        # Assert
        assert isinstance(result, PaginatedResponse)
        assert result.items == mock_items
        assert result.pagination.total_count == 25
        assert result.pagination.page == 1
        assert result.pagination.page_size == 10
        self.mock_query.filter.assert_called()

    @patch('genonaut.api.repositories.base.desc')
    @patch('genonaut.api.repositories.base.asc')
    def test_get_public_content_paginated(self, mock_asc, mock_desc):
        """Test get_public_content_paginated with pagination support."""
        # Mock SQLAlchemy functions
        mock_desc.return_value = Mock()
        mock_asc.return_value = Mock()
        # Arrange
        mock_items = [MockContentItem(i, is_private=False) for i in range(1, 4)]

        self.mock_query.filter.return_value = self.mock_query
        self.mock_query.order_by.return_value = self.mock_query
        self.mock_query.offset.return_value = self.mock_query
        self.mock_query.limit.return_value = self.mock_query
        self.mock_query.all.return_value = mock_items
        self.mock_query.count.return_value = 100

        pagination_request = PaginationRequest(page=1, page_size=50)

        # Act
        result = self.repository.get_public_content_paginated(pagination_request)

        # Assert
        assert isinstance(result, PaginatedResponse)
        assert result.items == mock_items
        assert result.pagination.total_count == 100
        assert result.pagination.has_next is True
        assert result.pagination.has_previous is False

    @pytest.mark.skip(reason="Data scaling tests - Repository issues (see notes/issues/by_priority/low/data-scaling-tests.md)")
    def test_get_by_content_type_paginated(self):
        """Test get_by_content_type_paginated with pagination support."""
        # Arrange
        content_type = "image"
        mock_items = [MockContentItem(i, content_type=content_type) for i in range(1, 6)]

        self.mock_query.filter.return_value = self.mock_query
        self.mock_query.order_by.return_value = self.mock_query
        self.mock_query.offset.return_value = self.mock_query
        self.mock_query.limit.return_value = self.mock_query
        self.mock_query.all.return_value = mock_items
        self.mock_query.count.return_value = 50

        pagination_request = PaginationRequest(page=1, page_size=10)

        # Act
        result = self.repository.get_by_content_type_paginated(content_type, pagination_request)

        # Assert
        assert isinstance(result, PaginatedResponse)
        assert len(result.items) == 5
        assert result.pagination.total_count == 50

    @pytest.mark.skip(reason="Data scaling tests - Repository issues (see notes/issues/by_priority/low/data-scaling-tests.md)")
    def test_search_by_title_paginated(self):
        """Test search_by_title_paginated with pagination support."""
        # Arrange
        search_term = "test"
        mock_items = [MockContentItem(i, title=f"Test Content {i}") for i in range(1, 4)]

        # Mock ilike method
        mock_title = Mock()
        mock_title.ilike.return_value = Mock()
        MockContentItem.title = mock_title

        self.mock_query.filter.return_value = self.mock_query
        self.mock_query.order_by.return_value = self.mock_query
        self.mock_query.offset.return_value = self.mock_query
        self.mock_query.limit.return_value = self.mock_query
        self.mock_query.all.return_value = mock_items
        self.mock_query.count.return_value = 15

        pagination_request = PaginationRequest(page=1, page_size=20)

        # Act
        result = self.repository.search_by_title_paginated(search_term, pagination_request)

        # Assert
        assert isinstance(result, PaginatedResponse)
        assert result.items == mock_items
        assert result.pagination.total_count == 15
        mock_title.ilike.assert_called_with(f"%{search_term}%")

    @pytest.mark.skip(reason="Data scaling tests - Repository issues (see notes/issues/by_priority/low/data-scaling-tests.md)")
    def test_get_top_rated_paginated(self):
        """Test get_top_rated_paginated with pagination support."""
        # Arrange
        mock_items = [
            MockContentItem(1, quality_score=0.95),
            MockContentItem(2, quality_score=0.88),
            MockContentItem(3, quality_score=0.82)
        ]

        self.mock_query.filter.return_value = self.mock_query
        self.mock_query.order_by.return_value = self.mock_query
        self.mock_query.offset.return_value = self.mock_query
        self.mock_query.limit.return_value = self.mock_query
        self.mock_query.all.return_value = mock_items
        self.mock_query.count.return_value = 200

        pagination_request = PaginationRequest(page=1, page_size=10, sort_field="quality_score", sort_order="desc")

        # Act
        result = self.repository.get_top_rated_paginated(pagination_request)

        # Assert
        assert isinstance(result, PaginatedResponse)
        assert result.items == mock_items
        assert result.pagination.total_count == 200

    @pytest.mark.skip(reason="Data scaling tests - Repository issues (see notes/issues/by_priority/low/data-scaling-tests.md)")
    def test_get_recent_paginated(self):
        """Test get_recent_paginated with pagination support."""
        # Arrange
        recent_date = datetime.utcnow() - timedelta(hours=6)
        mock_items = [MockContentItem(i, created_at=recent_date) for i in range(1, 4)]

        self.mock_query.filter.return_value = self.mock_query
        self.mock_query.order_by.return_value = self.mock_query
        self.mock_query.offset.return_value = self.mock_query
        self.mock_query.limit.return_value = self.mock_query
        self.mock_query.all.return_value = mock_items
        self.mock_query.count.return_value = 30

        pagination_request = PaginationRequest(page=1, page_size=25)

        # Act
        result = self.repository.get_recent_paginated(pagination_request, days=7)

        # Assert
        assert isinstance(result, PaginatedResponse)
        assert result.items == mock_items
        assert result.pagination.total_count == 30

    @pytest.mark.skip(reason="Data scaling tests - Repository issues (see notes/issues/by_priority/low/data-scaling-tests.md)")
    def test_search_by_metadata_paginated(self):
        """Test search_by_metadata_paginated with pagination support."""
        # Arrange
        metadata_filter = {"category": "science", "difficulty": "beginner"}
        mock_items = [MockContentItem(i) for i in range(1, 4)]

        # Mock the metadata op() method
        mock_metadata = Mock()
        mock_op = Mock()
        mock_metadata.op.return_value = mock_op
        mock_op.return_value = Mock()
        MockContentItem.item_metadata = mock_metadata

        self.mock_query.filter.return_value = self.mock_query
        self.mock_query.order_by.return_value = self.mock_query
        self.mock_query.offset.return_value = self.mock_query
        self.mock_query.limit.return_value = self.mock_query
        self.mock_query.all.return_value = mock_items
        self.mock_query.count.return_value = 8

        pagination_request = PaginationRequest(page=1, page_size=10)

        # Act
        result = self.repository.search_by_metadata_paginated(metadata_filter, pagination_request)

        # Assert
        assert isinstance(result, PaginatedResponse)
        assert result.items == mock_items
        assert result.pagination.total_count == 8

    @pytest.mark.skip(reason="Data scaling tests - Repository issues (see notes/issues/by_priority/low/data-scaling-tests.md)")
    def test_search_by_tags_paginated(self):
        """Test search_by_tags_paginated with pagination support."""
        # Arrange
        tags = ["python", "tutorial"]
        mock_items = [MockContentItem(i, tags=tags) for i in range(1, 4)]

        # Mock the tags op() method
        mock_tags = Mock()
        mock_op = Mock()
        mock_tags.op.return_value = mock_op
        mock_op.return_value = Mock()
        MockContentItem.tags = mock_tags

        self.mock_query.filter.return_value = self.mock_query
        self.mock_query.order_by.return_value = self.mock_query
        self.mock_query.offset.return_value = self.mock_query
        self.mock_query.limit.return_value = self.mock_query
        self.mock_query.all.return_value = mock_items
        self.mock_query.count.return_value = 12

        pagination_request = PaginationRequest(page=1, page_size=5)

        # Act
        result = self.repository.search_by_tags_paginated(tags, pagination_request)

        # Assert
        assert isinstance(result, PaginatedResponse)
        assert result.items == mock_items
        assert result.pagination.total_count == 12

    def test_content_repository_inheritance_from_base(self):
        """Test that ContentRepository properly inherits get_paginated from BaseRepository."""
        # Arrange
        mock_items = [MockContentItem(i) for i in range(1, 4)]
        self.mock_query.offset.return_value = self.mock_query
        self.mock_query.limit.return_value = self.mock_query
        self.mock_query.all.return_value = mock_items
        self.mock_query.count.return_value = 100

        pagination_request = PaginationRequest()

        # Act
        result = self.repository.get_paginated(pagination_request)

        # Assert
        assert isinstance(result, PaginatedResponse)
        assert result.items == mock_items
        assert result.pagination.total_count == 100

    @pytest.mark.skip(reason="Data scaling tests - Repository issues (see notes/issues/by_priority/low/data-scaling-tests.md)")
    def test_optimized_content_query_with_composite_index(self):
        """Test that content queries use composite indexes for performance."""
        # This test verifies that we use the right query patterns for performance
        # Arrange
        creator_id = uuid4()
        mock_items = [MockContentItem(i, creator_id) for i in range(1, 4)]

        self.mock_query.filter.return_value = self.mock_query
        self.mock_query.order_by.return_value = self.mock_query
        self.mock_query.offset.return_value = self.mock_query
        self.mock_query.limit.return_value = self.mock_query
        self.mock_query.all.return_value = mock_items
        self.mock_query.count.return_value = 1000

        pagination_request = PaginationRequest(
            page=1,
            page_size=50,
            sort_field="created_at",
            sort_order="desc"
        )

        # Act
        result = self.repository.get_by_creator_paginated(creator_id, pagination_request)

        # Assert - This should use creator_id + created_at composite index
        assert isinstance(result, PaginatedResponse)
        assert result.pagination.total_count == 1000

    @pytest.mark.skip(reason="Data scaling tests - Repository and cursor navigation issues (see notes/issues/by_priority/low/data-scaling-tests.md)")
    def test_cursor_based_pagination_for_large_datasets(self):
        """Test cursor-based pagination for high-performance scenarios."""
        # Arrange
        mock_items = [MockContentItem(i, created_at=datetime.utcnow()) for i in range(1, 4)]

        self.mock_query.filter.return_value = self.mock_query
        self.mock_query.order_by.return_value = self.mock_query
        self.mock_query.limit.return_value = self.mock_query
        self.mock_query.all.return_value = mock_items
        self.mock_query.count.return_value = 1000000  # Large dataset

        # Base64 encoded cursor for high-performance pagination
        cursor = "eyJpZCI6IDEwMDAsICJjcmVhdGVkX2F0IjogIjIwMjMtMTItMDFUMTI6MDA6MDAifQ=="
        pagination_request = PaginationRequest(
            cursor=cursor,
            page_size=50,
            sort_field="created_at",
            sort_order="desc"
        )

        # Act
        result = self.repository.get_paginated(pagination_request)

        # Assert
        assert isinstance(result, PaginatedResponse)
        assert result.pagination.total_count == 1000000

    def test_database_error_handling(self):
        """Test that database errors are properly handled."""
        # Arrange
        from sqlalchemy.exc import SQLAlchemyError
        self.mock_query.filter.side_effect = SQLAlchemyError("Database connection failed")

        pagination_request = PaginationRequest()

        # Act & Assert
        with pytest.raises(DatabaseError):
            self.repository.get_by_creator_paginated(uuid4(), pagination_request)

    def test_efficient_count_optimization(self):
        """Test that efficient counting is used for large result sets."""
        # Arrange
        mock_items = [MockContentItem(i) for i in range(1, 51)]  # Full page

        # Mock window function query
        mock_count_query = Mock()
        self.mock_db.query.side_effect = [self.mock_query, mock_count_query]

        mock_results = [(item, 10000) for item in mock_items]  # Items with total count
        mock_count_query.offset.return_value = mock_count_query
        mock_count_query.limit.return_value = mock_count_query
        mock_count_query.all.return_value = mock_results

        pagination_request = PaginationRequest(page=1, page_size=50)

        # Act
        result = self.repository.get_paginated(pagination_request, use_efficient_count=True)

        # Assert
        assert isinstance(result, PaginatedResponse)
        assert len(result.items) == 50
        assert result.pagination.total_count == 10000
        # Should not call separate count() when using efficient counting
        assert self.mock_query.count.call_count == 0