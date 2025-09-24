"""Integration tests for content endpoint pagination functionality."""

import pytest
from unittest.mock import Mock, patch
from uuid import uuid4
from fastapi.testclient import TestClient
from fastapi import FastAPI

from genonaut.api.routes.content import router as content_router
from genonaut.api.models.requests import PaginationRequest
from genonaut.api.models.responses import PaginatedResponse, PaginationMeta


class MockContentItem:
    """Mock content item for testing."""
    def __init__(self, id=1, title="Test Content", content_type="text", creator_id=None, is_private=False):
        self.id = id
        self.title = title
        self.content_type = content_type
        self.creator_id = creator_id or uuid4()
        self.is_private = is_private
        self.quality_score = 0.8
        self.tags = ["test"]
        self.item_metadata = {}
        self.content_data = "Test content data"
        self.created_at = "2023-12-01T12:00:00Z"


class TestContentEndpointsPagination:
    """Test content endpoints with new pagination functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.app = FastAPI()
        self.app.include_router(content_router)
        self.client = TestClient(self.app)

    @pytest.mark.skip(reason="Data scaling tests - Mock architecture issues (see scratchpads/issues/by_priority/low/data-scaling-tests.md)")
    @patch('genonaut.api.dependencies.get_database_session')
    @patch('genonaut.api.services.content_service.ContentService')
    def test_get_content_list_with_pagination(self, mock_service_class, mock_db_session):
        """Test GET /api/v1/content/ with pagination parameters."""
        # Arrange
        mock_db_session.return_value = Mock()
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        # Mock paginated response
        mock_items = [MockContentItem(i) for i in range(1, 11)]
        pagination_meta = PaginationMeta(
            page=1,
            page_size=10,
            total_count=100,
            has_next=True,
            has_previous=False
        )
        mock_paginated_response = PaginatedResponse(
            items=mock_items,
            pagination=pagination_meta
        )

        mock_service.get_content_list_paginated.return_value = mock_paginated_response

        # Act
        response = self.client.get(
            "/api/v1/content/enhanced?page=1&page_size=10"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "pagination" in data
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["page_size"] == 10
        assert data["pagination"]["total_count"] == 100
        assert data["pagination"]["has_next"] is True
        assert data["pagination"]["has_previous"] is False
        assert len(data["items"]) == 10

    @pytest.mark.skip(reason="Data scaling tests - Mock architecture issues (see scratchpads/issues/by_priority/low/data-scaling-tests.md)")
    @patch('genonaut.api.dependencies.get_database_session')
    @patch('genonaut.api.services.content_service.ContentService')
    def test_get_content_by_creator_paginated(self, mock_service_class, mock_db_session):
        """Test GET /api/v1/content/creator/{creator_id} with pagination."""
        # Arrange
        mock_db_session.return_value = Mock()
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        creator_id = str(uuid4())
        mock_items = [MockContentItem(i, creator_id=creator_id) for i in range(1, 6)]
        pagination_meta = PaginationMeta(
            page=1,
            page_size=5,
            total_count=25,
            has_next=True,
            has_previous=False
        )
        mock_paginated_response = PaginatedResponse(
            items=mock_items,
            pagination=pagination_meta
        )

        mock_service.get_content_by_creator_paginated.return_value = mock_paginated_response

        # Act
        response = self.client.get(
            f"/api/v1/content/creator/{creator_id}?page=1&page_size=5"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["total_count"] == 25
        assert len(data["items"]) == 5
        mock_service.get_content_by_creator_paginated.assert_called_once()

    @pytest.mark.skip(reason="Data scaling tests - Mock architecture issues (see scratchpads/issues/by_priority/low/data-scaling-tests.md)")
    @patch('genonaut.api.dependencies.get_database_session')
    @patch('genonaut.api.services.content_service.ContentService')
    def test_get_content_by_type_paginated(self, mock_service_class, mock_db_session):
        """Test GET /api/v1/content/type/{content_type} with pagination."""
        # Arrange
        mock_db_session.return_value = Mock()
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        content_type = "image"
        mock_items = [MockContentItem(i, content_type=content_type) for i in range(1, 4)]
        pagination_meta = PaginationMeta(
            page=2,
            page_size=50,
            total_count=150,
            has_next=True,
            has_previous=True
        )
        mock_paginated_response = PaginatedResponse(
            items=mock_items,
            pagination=pagination_meta
        )

        mock_service.get_content_by_type_paginated.return_value = mock_paginated_response

        # Act
        response = self.client.get(
            f"/api/v1/content/type/{content_type}?page=2&page_size=50"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["page"] == 2
        assert data["pagination"]["has_previous"] is True
        assert data["pagination"]["has_next"] is True

    @pytest.mark.skip(reason="Data scaling tests - Mock architecture issues (see scratchpads/issues/by_priority/low/data-scaling-tests.md)")
    @patch('genonaut.api.dependencies.get_database_session')
    @patch('genonaut.api.services.content_service.ContentService')
    def test_get_public_content_paginated(self, mock_service_class, mock_db_session):
        """Test GET /api/v1/content/public/all with pagination."""
        # Arrange
        mock_db_session.return_value = Mock()
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        mock_items = [MockContentItem(i, is_private=False) for i in range(1, 4)]
        pagination_meta = PaginationMeta(
            page=1,
            page_size=20,
            total_count=60,
            has_next=True,
            has_previous=False
        )
        mock_paginated_response = PaginatedResponse(
            items=mock_items,
            pagination=pagination_meta
        )

        mock_service.get_public_content_paginated.return_value = mock_paginated_response

        # Act
        response = self.client.get(
            "/api/v1/content/public/all?page=1&page_size=20"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["total_count"] == 60
        assert len(data["items"]) == 3

    @pytest.mark.skip(reason="Data scaling tests - Mock architecture issues (see scratchpads/issues/by_priority/low/data-scaling-tests.md)")
    @patch('genonaut.api.dependencies.get_database_session')
    @patch('genonaut.api.services.content_service.ContentService')
    def test_get_top_rated_content_paginated(self, mock_service_class, mock_db_session):
        """Test GET /api/v1/content/top-rated/all with pagination."""
        # Arrange
        mock_db_session.return_value = Mock()
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        mock_items = [
            MockContentItem(1, quality_score=0.95),
            MockContentItem(2, quality_score=0.88),
            MockContentItem(3, quality_score=0.82)
        ]
        pagination_meta = PaginationMeta(
            page=1,
            page_size=10,
            total_count=50,
            has_next=True,
            has_previous=False
        )
        mock_paginated_response = PaginatedResponse(
            items=mock_items,
            pagination=pagination_meta
        )

        mock_service.get_top_rated_content_paginated.return_value = mock_paginated_response

        # Act
        response = self.client.get(
            "/api/v1/content/top-rated/all?page=1&page_size=10"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["total_count"] == 50
        assert len(data["items"]) == 3

    @pytest.mark.skip(reason="Data scaling tests - Mock architecture issues (see scratchpads/issues/by_priority/low/data-scaling-tests.md)")
    @patch('genonaut.api.dependencies.get_database_session')
    @patch('genonaut.api.services.content_service.ContentService')
    def test_get_recent_content_paginated(self, mock_service_class, mock_db_session):
        """Test GET /api/v1/content/recent/all with pagination."""
        # Arrange
        mock_db_session.return_value = Mock()
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        mock_items = [MockContentItem(i) for i in range(1, 6)]
        pagination_meta = PaginationMeta(
            page=1,
            page_size=25,
            total_count=75,
            has_next=True,
            has_previous=False
        )
        mock_paginated_response = PaginatedResponse(
            items=mock_items,
            pagination=pagination_meta
        )

        mock_service.get_recent_content_paginated.return_value = mock_paginated_response

        # Act
        response = self.client.get(
            "/api/v1/content/recent/all?page=1&page_size=25&days=7"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["page_size"] == 25

    @pytest.mark.skip(reason="Data scaling tests - Mock architecture issues (see scratchpads/issues/by_priority/low/data-scaling-tests.md)")
    @patch('genonaut.api.dependencies.get_database_session')
    @patch('genonaut.api.services.content_service.ContentService')
    def test_search_content_paginated(self, mock_service_class, mock_db_session):
        """Test POST /api/v1/content/search with pagination."""
        # Arrange
        mock_db_session.return_value = Mock()
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        mock_items = [MockContentItem(i, title=f"Search Result {i}") for i in range(1, 4)]
        pagination_meta = PaginationMeta(
            page=1,
            page_size=10,
            total_count=30,
            has_next=True,
            has_previous=False
        )
        mock_paginated_response = PaginatedResponse(
            items=mock_items,
            pagination=pagination_meta
        )

        mock_service.search_content_paginated.return_value = mock_paginated_response

        # Act
        response = self.client.post(
            "/api/v1/content/search",
            json={
                "search_term": "test",
                "page": 1,
                "page_size": 10
            }
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["total_count"] == 30
        assert len(data["items"]) == 3

    @pytest.mark.skip(reason="Data scaling tests - Mock architecture and cursor navigation issues (see scratchpads/issues/by_priority/low/data-scaling-tests.md)")
    @patch('genonaut.api.dependencies.get_database_session')
    @patch('genonaut.api.services.content_service.ContentService')
    def test_pagination_with_cursor_support(self, mock_service_class, mock_db_session):
        """Test cursor-based pagination for large datasets."""
        # Arrange
        mock_db_session.return_value = Mock()
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        mock_items = [MockContentItem(i) for i in range(1001, 1051)]  # Items from middle of large dataset
        pagination_meta = PaginationMeta(
            page=21,
            page_size=50,
            total_count=1000000,  # Large dataset
            has_next=True,
            has_previous=True,
            next_cursor="eyJpZCI6IDEwNTAsICJjcmVhdGVkX2F0IjogIjIwMjMtMTItMDFUMTI6MDA6MDBaIn0=",
            prev_cursor="eyJpZCI6IDEwMDAsICJjcmVhdGVkX2F0IjogIjIwMjMtMTItMDFUMTE6NTk6MDBaIn0="
        )
        mock_paginated_response = PaginatedResponse(
            items=mock_items,
            pagination=pagination_meta
        )

        mock_service.get_content_list_paginated.return_value = mock_paginated_response

        # Act
        response = self.client.get(
            "/api/v1/content/?cursor=eyJpZCI6IDEwMDAsICJjcmVhdGVkX2F0IjogIjIwMjMtMTItMDFUMTE6NTk6MDBaIn0=&page_size=50"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["next_cursor"] is not None
        assert data["pagination"]["prev_cursor"] is not None
        assert data["pagination"]["total_count"] == 1000000

    @pytest.mark.skip(reason="Data scaling tests - Mock architecture issues (see scratchpads/issues/by_priority/low/data-scaling-tests.md)")
    @patch('genonaut.api.dependencies.get_database_session')
    @patch('genonaut.api.services.content_service.ContentService')
    def test_pagination_default_values(self, mock_service_class, mock_db_session):
        """Test that endpoints use proper default pagination values."""
        # Arrange
        mock_db_session.return_value = Mock()
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        mock_items = [MockContentItem(i) for i in range(1, 51)]  # Default page size
        pagination_meta = PaginationMeta(
            page=1,
            page_size=50,  # Default page size
            total_count=200,
            has_next=True,
            has_previous=False
        )
        mock_paginated_response = PaginatedResponse(
            items=mock_items,
            pagination=pagination_meta
        )

        mock_service.get_content_list_paginated.return_value = mock_paginated_response

        # Act - Request without pagination parameters
        response = self.client.get("/api/v1/content/")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["page_size"] == 50

    @pytest.mark.skip(reason="Data scaling tests - Mock architecture issues (see scratchpads/issues/by_priority/low/data-scaling-tests.md)")
    @patch('genonaut.api.dependencies.get_database_session')
    @patch('genonaut.api.services.content_service.ContentService')
    def test_pagination_max_page_size_limit(self, mock_service_class, mock_db_session):
        """Test that endpoints enforce maximum page size limit."""
        # Arrange
        mock_db_session.return_value = Mock()
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        # Act - Request with page size exceeding limit
        response = self.client.get("/api/v1/content/?page_size=2000")

        # Assert - Should be limited to max allowed (1000)
        assert response.status_code == 422  # Validation error

    @pytest.mark.skip(reason="Data scaling tests - Mock architecture issues (see scratchpads/issues/by_priority/low/data-scaling-tests.md)")
    @patch('genonaut.api.dependencies.get_database_session')
    @patch('genonaut.api.services.content_service.ContentService')
    def test_pagination_error_handling(self, mock_service_class, mock_db_session):
        """Test error handling in paginated endpoints."""
        # Arrange
        mock_db_session.return_value = Mock()
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        # Mock service to raise database error
        from genonaut.api.exceptions import DatabaseError
        mock_service.get_content_list_paginated.side_effect = DatabaseError("Database connection failed")

        # Act
        response = self.client.get("/api/v1/content/")

        # Assert
        assert response.status_code == 500

    @pytest.mark.skip(reason="Data scaling tests - Mock architecture issues (see scratchpads/issues/by_priority/low/data-scaling-tests.md)")
    @patch('genonaut.api.dependencies.get_database_session')
    @patch('genonaut.api.services.content_service.ContentService')
    def test_sorting_parameters_in_pagination(self, mock_service_class, mock_db_session):
        """Test sorting parameters work with pagination."""
        # Arrange
        mock_db_session.return_value = Mock()
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        mock_items = [
            MockContentItem(3, quality_score=0.95),  # Highest rated first
            MockContentItem(1, quality_score=0.88),
            MockContentItem(2, quality_score=0.82)
        ]
        pagination_meta = PaginationMeta(
            page=1,
            page_size=10,
            total_count=30,
            has_next=True,
            has_previous=False
        )
        mock_paginated_response = PaginatedResponse(
            items=mock_items,
            pagination=pagination_meta
        )

        mock_service.get_content_list_paginated.return_value = mock_paginated_response

        # Act
        response = self.client.get(
            "/api/v1/content/?sort_field=quality_score&sort_order=desc&page=1&page_size=10"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        # Verify items are in expected order (highest quality first)
        assert len(data["items"]) == 3

    @pytest.mark.skip(reason="Data scaling tests - Mock architecture issues (see scratchpads/issues/by_priority/low/data-scaling-tests.md)")
    @patch('genonaut.api.dependencies.get_database_session')
    @patch('genonaut.api.services.content_service.ContentService')
    def test_backward_compatibility_with_old_parameters(self, mock_service_class, mock_db_session):
        """Test that endpoints maintain backward compatibility with skip/limit parameters."""
        # Arrange
        mock_db_session.return_value = Mock()
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        mock_items = [MockContentItem(i) for i in range(101, 151)]  # Skip=100, limit=50
        pagination_meta = PaginationMeta(
            page=3,  # page 3 with page_size 50 = skip 100
            page_size=50,
            total_count=500,
            has_next=True,
            has_previous=True
        )
        mock_paginated_response = PaginatedResponse(
            items=mock_items,
            pagination=pagination_meta
        )

        mock_service.get_content_list_paginated.return_value = mock_paginated_response

        # Act - Use old skip/limit parameters
        response = self.client.get("/api/v1/content/?skip=100&limit=50")

        # Assert
        assert response.status_code == 200
        data = response.json()
        # Should convert skip/limit to page/page_size internally
        assert data["pagination"]["page"] == 3
        assert data["pagination"]["page_size"] == 50