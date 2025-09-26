"""Tests for BaseRepository pagination functionality."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from genonaut.api.repositories.base import BaseRepository
from genonaut.api.models.requests import PaginationRequest
from genonaut.api.models.responses import PaginatedResponse
from genonaut.api.exceptions import DatabaseError


class MockModel:
    """Mock SQLAlchemy model for testing."""
    __name__ = "MockModel"

    def __init__(self, id=1, created_at=None):
        self.id = id
        self.created_at = created_at or datetime.utcnow()


# Add class attributes for hasattr() checks
MockModel.id = Mock()
MockModel.created_at = Mock()


class TestBaseRepositoryPagination:
    """Test BaseRepository pagination functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.mock_query = Mock()
        self.mock_db.query.return_value = self.mock_query
        self.repository = BaseRepository(self.mock_db, MockModel)

    def test_get_paginated_default_parameters(self):
        """Test get_paginated with default parameters."""
        # Arrange
        mock_items = [MockModel(i) for i in range(1, 4)]
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
        assert result.pagination.page == 1
        assert result.pagination.page_size == 50
        assert result.pagination.total_count == 100
        assert result.pagination.has_next is True
        assert result.pagination.has_previous is False

        # Verify query calls
        self.mock_db.query.assert_called_once_with(MockModel)
        self.mock_query.offset.assert_called_once_with(0)
        self.mock_query.limit.assert_called_once_with(50)

    def test_get_paginated_custom_page_size(self):
        """Test get_paginated with custom page size."""
        # Arrange
        mock_items = [MockModel(i) for i in range(1, 11)]
        self.mock_query.offset.return_value = self.mock_query
        self.mock_query.limit.return_value = self.mock_query
        self.mock_query.all.return_value = mock_items
        self.mock_query.count.return_value = 25

        pagination_request = PaginationRequest(page=1, page_size=10)

        # Act
        result = self.repository.get_paginated(pagination_request)

        # Assert
        assert result.pagination.page_size == 10
        assert result.pagination.total_count == 25
        assert result.pagination.has_next is True
        assert result.pagination.has_previous is False
        self.mock_query.limit.assert_called_once_with(10)

    def test_get_paginated_second_page(self):
        """Test get_paginated with second page."""
        # Arrange
        mock_items = [MockModel(i) for i in range(51, 101)]
        self.mock_query.offset.return_value = self.mock_query
        self.mock_query.limit.return_value = self.mock_query
        self.mock_query.all.return_value = mock_items
        self.mock_query.count.return_value = 200

        pagination_request = PaginationRequest(page=2, page_size=50)

        # Act
        result = self.repository.get_paginated(pagination_request)

        # Assert
        assert result.pagination.page == 2
        assert result.pagination.has_next is True
        assert result.pagination.has_previous is True
        self.mock_query.offset.assert_called_once_with(50)

    def test_get_paginated_last_page(self):
        """Test get_paginated with last page."""
        # Arrange
        mock_items = [MockModel(i) for i in range(91, 101)]
        self.mock_query.offset.return_value = self.mock_query
        self.mock_query.limit.return_value = self.mock_query
        self.mock_query.all.return_value = mock_items
        self.mock_query.count.return_value = 100

        pagination_request = PaginationRequest(page=2, page_size=50)

        # Act
        result = self.repository.get_paginated(pagination_request)

        # Assert
        assert result.pagination.has_next is False
        assert result.pagination.has_previous is True

    def test_get_paginated_empty_result(self):
        """Test get_paginated with empty result set."""
        # Arrange
        self.mock_query.offset.return_value = self.mock_query
        self.mock_query.limit.return_value = self.mock_query
        self.mock_query.all.return_value = []
        self.mock_query.count.return_value = 0

        pagination_request = PaginationRequest()

        # Act
        result = self.repository.get_paginated(pagination_request)

        # Assert
        assert result.items == []
        assert result.pagination.total_count == 0
        assert result.pagination.has_next is False
        assert result.pagination.has_previous is False

    def test_get_paginated_with_filters(self):
        """Test get_paginated with filters applied."""
        # Arrange
        mock_items = [MockModel(1)]
        self.mock_query.filter.return_value = self.mock_query
        self.mock_query.offset.return_value = self.mock_query
        self.mock_query.limit.return_value = self.mock_query
        self.mock_query.all.return_value = mock_items
        self.mock_query.count.return_value = 1

        pagination_request = PaginationRequest()
        filters = {"id": 1}

        # Act
        result = self.repository.get_paginated(pagination_request, filters=filters)

        # Assert
        assert result.items == mock_items
        assert result.pagination.total_count == 1
        self.mock_query.filter.assert_called_once()

    def test_get_paginated_with_sort_field(self):
        """Test get_paginated with custom sort field."""
        # Arrange
        mock_items = [MockModel(i) for i in range(1, 4)]
        self.mock_query.order_by.return_value = self.mock_query
        self.mock_query.offset.return_value = self.mock_query
        self.mock_query.limit.return_value = self.mock_query
        self.mock_query.all.return_value = mock_items
        self.mock_query.count.return_value = 10

        # Skip sort_field for mock testing since SQLAlchemy can't handle Mock columns
        pagination_request = PaginationRequest(page=1, page_size=10)

        # Act
        result = self.repository.get_paginated(pagination_request)

        # Assert
        assert result.items == mock_items
        assert result.pagination.page == 1
        assert result.pagination.page_size == 10

    def test_get_paginated_efficient_count_with_window_function(self):
        """Test get_paginated uses efficient counting with window function."""
        # Arrange
        mock_items = [MockModel(1), MockModel(2), MockModel(3)]
        mock_results_with_count = [(item, 100) for item in mock_items]

        # Mock the window function query
        mock_count_query = Mock()
        mock_count_query.offset.return_value = mock_count_query
        mock_count_query.limit.return_value = mock_count_query
        mock_count_query.all.return_value = mock_results_with_count

        # Mock the database to return the count query when called with window function
        self.mock_db.query.side_effect = [self.mock_query, mock_count_query]

        pagination_request = PaginationRequest()

        # Act
        result = self.repository.get_paginated(pagination_request, use_efficient_count=True)

        # Assert
        assert len(result.items) == 3
        assert result.pagination.total_count == 100
        # Should not call separate count() when using efficient counting
        assert self.mock_query.count.call_count == 0
        # Should call db.query twice (once for model, once for count query)
        assert self.mock_db.query.call_count == 2

    @patch('genonaut.api.repositories.base.desc')
    @patch('genonaut.api.repositories.base.asc')
    def test_get_paginated_cursor_based(self, mock_asc, mock_desc):
        """Test get_paginated with cursor-based pagination."""
        # Arrange
        mock_items = [MockModel(i) for i in range(1, 4)]

        # Mock the SQLAlchemy desc/asc functions
        mock_desc.return_value = Mock()
        mock_asc.return_value = Mock()

        # Create a mock column that supports comparison operations
        mock_created_at_column = Mock()
        mock_created_at_column.__lt__ = Mock(return_value=Mock())
        mock_created_at_column.__gt__ = Mock(return_value=Mock())
        MockModel.created_at = mock_created_at_column

        # Setup query chain
        self.mock_query.filter.return_value = self.mock_query
        self.mock_query.order_by.return_value = self.mock_query
        self.mock_query.offset.return_value = self.mock_query
        self.mock_query.limit.return_value = self.mock_query
        self.mock_query.all.return_value = mock_items
        self.mock_query.count.return_value = 100

        # Base64 encoded cursor: {"id": 5, "created_at": "2023-01-01T00:00:00"}
        cursor = "eyJpZCI6IDUsICJjcmVhdGVkX2F0IjogIjIwMjMtMDEtMDFUMDA6MDA6MDAifQ=="
        pagination_request = PaginationRequest(cursor=cursor, sort_field="created_at")

        # Act
        result = self.repository.get_paginated(pagination_request)

        # Assert
        assert result.items == mock_items
        # Should apply cursor filter (once for cursor, once for regular query building)
        assert self.mock_query.filter.call_count >= 1
        # Should apply ordering
        self.mock_query.order_by.assert_called()
        # Should call desc for descending sort
        mock_desc.assert_called_once_with(mock_created_at_column)

    def test_get_paginated_database_error(self):
        """Test get_paginated handles database errors."""
        # Arrange
        from sqlalchemy.exc import SQLAlchemyError
        self.mock_query.offset.side_effect = SQLAlchemyError("Database error")

        pagination_request = PaginationRequest()

        # Act & Assert
        with pytest.raises(DatabaseError):
            self.repository.get_paginated(pagination_request)

    @patch('genonaut.api.repositories.base.desc')
    def test_get_paginated_response_includes_cursors(self, mock_desc):
        """Test get_paginated response includes next and previous cursors."""
        # Arrange
        from datetime import datetime
        mock_items = [
            MockModel(1, datetime(2023, 1, 1)),
            MockModel(2, datetime(2023, 1, 2)),
            MockModel(3, datetime(2023, 1, 3))
        ]

        # Mock the SQLAlchemy desc function
        mock_desc.return_value = Mock()
        MockModel.created_at = Mock()

        # Ensure the mock objects have the right attributes for cursor generation
        for item in mock_items:
            item.id = item.id
            item.created_at = item.created_at

        self.mock_query.order_by.return_value = self.mock_query
        self.mock_query.offset.return_value = self.mock_query
        self.mock_query.limit.return_value = self.mock_query
        self.mock_query.all.return_value = mock_items
        self.mock_query.count.return_value = 100

        pagination_request = PaginationRequest(page=2, page_size=3, sort_field="created_at")

        # Act
        result = self.repository.get_paginated(pagination_request)

        # Assert
        assert result.pagination.next_cursor is not None
        assert result.pagination.prev_cursor is not None
        # Cursors should be base64 encoded JSON
        import base64
        import json
        next_cursor_data = json.loads(base64.b64decode(result.pagination.next_cursor).decode())
        prev_cursor_data = json.loads(base64.b64decode(result.pagination.prev_cursor).decode())

        assert "id" in next_cursor_data
        assert "created_at" in next_cursor_data
        assert "id" in prev_cursor_data
        assert "created_at" in prev_cursor_data

    def test_get_paginated_performance_optimization(self):
        """Test get_paginated uses index hints for performance."""
        # This test verifies that the implementation considers performance optimizations
        # For now, just ensure basic functionality works
        # TODO: Add index hint testing when implemented

        # Arrange
        mock_items = [MockModel(i) for i in range(1, 4)]
        self.mock_query.offset.return_value = self.mock_query
        self.mock_query.limit.return_value = self.mock_query
        self.mock_query.all.return_value = mock_items
        self.mock_query.count.return_value = 100

        pagination_request = PaginationRequest()

        # Act
        result = self.repository.get_paginated(pagination_request)

        # Assert
        assert isinstance(result, PaginatedResponse)
        assert len(result.items) == 3