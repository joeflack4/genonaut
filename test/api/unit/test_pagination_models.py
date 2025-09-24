"""Tests for pagination request/response models."""

import pytest
from pydantic import ValidationError

from genonaut.api.models.requests import PaginationRequest
from genonaut.api.models.responses import PaginatedResponse


class TestPaginationRequest:
    """Test pagination request model."""

    def test_default_values(self):
        """Test default pagination values."""
        req = PaginationRequest()
        assert req.page == 1
        assert req.page_size == 50
        assert req.cursor is None
        assert req.sort_field is None
        assert req.sort_order == "desc"

    def test_valid_page_values(self):
        """Test valid page number values."""
        req = PaginationRequest(page=1)
        assert req.page == 1

        req = PaginationRequest(page=100)
        assert req.page == 100

    def test_invalid_page_values(self):
        """Test invalid page number values."""
        with pytest.raises(ValidationError):
            PaginationRequest(page=0)

        with pytest.raises(ValidationError):
            PaginationRequest(page=-1)

    def test_valid_page_size_values(self):
        """Test valid page size values."""
        req = PaginationRequest(page_size=1)
        assert req.page_size == 1

        req = PaginationRequest(page_size=50)
        assert req.page_size == 50

        req = PaginationRequest(page_size=1000)
        assert req.page_size == 1000

    def test_invalid_page_size_values(self):
        """Test invalid page size values."""
        with pytest.raises(ValidationError):
            PaginationRequest(page_size=0)

        with pytest.raises(ValidationError):
            PaginationRequest(page_size=-1)

        with pytest.raises(ValidationError):
            PaginationRequest(page_size=1001)

    def test_cursor_validation(self):
        """Test cursor validation."""
        # Valid base64 encoded cursor
        req = PaginationRequest(cursor="eyJ0ZXN0IjogdHJ1ZX0=")
        assert req.cursor == "eyJ0ZXN0IjogdHJ1ZX0="

        # Empty cursor should be None
        req = PaginationRequest(cursor="")
        assert req.cursor is None

        # Whitespace cursor should be None
        req = PaginationRequest(cursor="   ")
        assert req.cursor is None

    def test_sort_order_validation(self):
        """Test sort order validation."""
        req = PaginationRequest(sort_order="asc")
        assert req.sort_order == "asc"

        req = PaginationRequest(sort_order="desc")
        assert req.sort_order == "desc"

        with pytest.raises(ValidationError):
            PaginationRequest(sort_order="invalid")

    def test_skip_property(self):
        """Test calculated skip property."""
        req = PaginationRequest(page=1, page_size=50)
        assert req.skip == 0

        req = PaginationRequest(page=2, page_size=50)
        assert req.skip == 50

        req = PaginationRequest(page=3, page_size=25)
        assert req.skip == 50


class TestPaginatedResponse:
    """Test paginated response model."""

    def test_basic_response(self):
        """Test basic paginated response creation."""
        items = [{"id": 1, "name": "test1"}, {"id": 2, "name": "test2"}]
        pagination = {
            "page": 1,
            "page_size": 50,
            "total_count": 100,
            "has_next": True,
            "has_previous": False
        }

        response = PaginatedResponse(items=items, pagination=pagination)

        assert response.items == items
        assert response.pagination.page == 1
        assert response.pagination.page_size == 50
        assert response.pagination.total_count == 100
        assert response.pagination.has_next is True
        assert response.pagination.has_previous is False

    def test_total_pages_calculation(self):
        """Test total pages calculation."""
        pagination = {
            "page": 1,
            "page_size": 50,
            "total_count": 100,
            "has_next": True,
            "has_previous": False
        }

        response = PaginatedResponse(items=[], pagination=pagination)
        assert response.pagination.total_pages == 2

        # Test edge case: total_count = 0
        pagination["total_count"] = 0
        response = PaginatedResponse(items=[], pagination=pagination)
        assert response.pagination.total_pages == 0

        # Test edge case: total_count < page_size
        pagination["total_count"] = 25
        response = PaginatedResponse(items=[], pagination=pagination)
        assert response.pagination.total_pages == 1

    def test_cursor_fields(self):
        """Test cursor-related fields."""
        pagination = {
            "page": 2,
            "page_size": 50,
            "total_count": 200,
            "has_next": True,
            "has_previous": True,
            "next_cursor": "eyJuZXh0IjogdHJ1ZX0=",
            "prev_cursor": "eyJwcmV2IjogdHJ1ZX0="
        }

        response = PaginatedResponse(items=[], pagination=pagination)
        assert response.pagination.next_cursor == "eyJuZXh0IjogdHJ1ZX0="
        assert response.pagination.prev_cursor == "eyJwcmV2IjogdHJ1ZX0="

    def test_optional_cursor_fields(self):
        """Test that cursor fields are optional."""
        pagination = {
            "page": 1,
            "page_size": 50,
            "total_count": 100,
            "has_next": True,
            "has_previous": False
        }

        response = PaginatedResponse(items=[], pagination=pagination)
        assert response.pagination.next_cursor is None
        assert response.pagination.prev_cursor is None

    def test_validation_errors(self):
        """Test validation errors for invalid data."""
        # Missing required fields
        with pytest.raises(ValidationError):
            PaginatedResponse(items=[], pagination={})

        # Invalid page number
        with pytest.raises(ValidationError):
            PaginatedResponse(
                items=[],
                pagination={
                    "page": 0,
                    "page_size": 50,
                    "total_count": 100,
                    "has_next": True,
                    "has_previous": False
                }
            )

        # Invalid page size
        with pytest.raises(ValidationError):
            PaginatedResponse(
                items=[],
                pagination={
                    "page": 1,
                    "page_size": 0,
                    "total_count": 100,
                    "has_next": True,
                    "has_previous": False
                }
            )

        # Negative total count
        with pytest.raises(ValidationError):
            PaginatedResponse(
                items=[],
                pagination={
                    "page": 1,
                    "page_size": 50,
                    "total_count": -1,
                    "has_next": True,
                    "has_previous": False
                }
            )

    def test_items_type_flexibility(self):
        """Test that items can be any list type."""
        # List of dicts
        response = PaginatedResponse(
            items=[{"id": 1}, {"id": 2}],
            pagination={
                "page": 1,
                "page_size": 50,
                "total_count": 2,
                "has_next": False,
                "has_previous": False
            }
        )
        assert len(response.items) == 2

        # List of strings
        response = PaginatedResponse(
            items=["item1", "item2"],
            pagination={
                "page": 1,
                "page_size": 50,
                "total_count": 2,
                "has_next": False,
                "has_previous": False
            }
        )
        assert response.items == ["item1", "item2"]

        # Empty list
        response = PaginatedResponse(
            items=[],
            pagination={
                "page": 1,
                "page_size": 50,
                "total_count": 0,
                "has_next": False,
                "has_previous": False
            }
        )
        assert response.items == []