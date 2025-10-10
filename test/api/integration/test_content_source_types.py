"""
Integration tests for content_source_types parameter in unified content API.

Tests the new filtering approach to ensure all parameter combinations work correctly.
Uses the running API server with its existing test database.
"""

import pytest


class TestContentSourceTypesParameter:
    """Test the new content_source_types parameter works correctly."""

    def test_parameter_validation_accepts_valid_types(self, api_client):
        """Test that valid content_source_types are accepted."""
        # Test with all valid types
        response = api_client.get(
            "/api/v1/content/unified",
            params={
                "content_source_types": ["user-regular", "user-auto", "community-regular", "community-auto"],
                "page_size": 10
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "pagination" in data

    def test_parameter_validation_rejects_invalid_types(self, api_client):
        """Test that invalid content_source_types are rejected."""
        response = api_client.get(
            "/api/v1/content/unified",
            params={
                "content_source_types": ["invalid-type"],
                "page_size": 10
            }
        )
        assert response.status_code == 400
        assert "Invalid content_source_type" in response.json()["detail"]

    def test_single_source_type_user_regular(self, api_client):
        """Test filtering by user-regular only."""
        response = api_client.get(
            "/api/v1/content/unified",
            params={
                "content_source_types": ["user-regular"],
                "page_size": 10
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        # Should return some results or empty if no user-regular content exists
        assert isinstance(data["items"], list)

    def test_single_source_type_user_auto(self, api_client):
        """Test filtering by user-auto only."""
        response = api_client.get(
            "/api/v1/content/unified",
            params={
                "content_source_types": ["user-auto"],
                "page_size": 10
            }
        )
        assert response.status_code == 200

    def test_single_source_type_community_regular(self, api_client):
        """Test filtering by community-regular only."""
        response = api_client.get(
            "/api/v1/content/unified",
            params={
                "content_source_types": ["community-regular"],
                "page_size": 10
            }
        )
        assert response.status_code == 200

    def test_single_source_type_community_auto(self, api_client):
        """Test filtering by community-auto only."""
        response = api_client.get(
            "/api/v1/content/unified",
            params={
                "content_source_types": ["community-auto"],
                "page_size": 10
            }
        )
        assert response.status_code == 200

    def test_empty_content_source_types_returns_zero_results(self, api_client):
        """Test that empty content_source_types array returns 0 results.

        Note: HTTP doesn't transmit empty arrays, so we use [""] as a sentinel value
        to explicitly indicate "no content types selected".
        """
        response = api_client.get(
            "/api/v1/content/unified",
            params={
                "content_source_types": [""],  # Sentinel value for explicit empty
                "page_size": 10
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["total_count"] == 0
        assert len(data["items"]) == 0

    def test_multiple_source_types_combination(self, api_client):
        """Test combining multiple source types."""
        response = api_client.get(
            "/api/v1/content/unified",
            params={
                "content_source_types": ["user-regular", "community-auto"],
                "page_size": 10
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "pagination" in data

    def test_backward_compatibility_with_legacy_params(self, api_client):
        """Test that old content_types + creator_filter still works."""
        response = api_client.get(
            "/api/v1/content/unified",
            params={
                "content_types": "regular,auto",
                "creator_filter": "all",
                "page_size": 10
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_content_source_types_takes_precedence_over_legacy(self, api_client):
        """Test that content_source_types overrides legacy params when both provided.

        Note: HTTP doesn't transmit empty arrays, so we use [""] as a sentinel value
        to explicitly indicate "no content types selected".
        """
        # Send both new and legacy params
        # The new param should take precedence
        response = api_client.get(
            "/api/v1/content/unified",
            params={
                "content_source_types": [""],  # Sentinel value for explicit empty - should return 0 results
                "content_types": "regular,auto",  # This should be ignored
                "creator_filter": "all",  # This should be ignored
                "page_size": 10
            }
        )
        assert response.status_code == 200
        data = response.json()
        # Should return 0 results because content_source_types=[""] takes precedence
        assert data["pagination"]["total_count"] == 0

    def test_pagination_works_with_content_source_types(self, api_client):
        """Test that pagination works correctly with the new parameter."""
        response = api_client.get(
            "/api/v1/content/unified",
            params={
                "content_source_types": ["community-regular", "community-auto"],
                "page": 1,
                "page_size": 5
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["page_size"] == 5

    def test_all_four_types_together(self, api_client):
        """Test with all 4 content source types enabled."""
        response = api_client.get(
            "/api/v1/content/unified",
            params={
                "content_source_types": [
                    "user-regular",
                    "user-auto",
                    "community-regular",
                    "community-auto"
                ],
                "page_size": 10
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "stats" in data

    def test_three_types_combination(self, api_client):
        """Test with 3 out of 4 types."""
        response = api_client.get(
            "/api/v1/content/unified",
            params={
                "content_source_types": [
                    "user-regular",
                    "user-auto",
                    "community-regular"
                ],
                "page_size": 10
            }
        )
        assert response.status_code == 200

    def test_works_with_search_term(self, api_client):
        """Test content_source_types works with search filtering."""
        response = api_client.get(
            "/api/v1/content/unified",
            params={
                "content_source_types": ["community-regular"],
                "search_term": "test",
                "page_size": 10
            }
        )
        assert response.status_code == 200

    def test_works_with_sorting(self, api_client):
        """Test content_source_types works with sorting."""
        response = api_client.get(
            "/api/v1/content/unified",
            params={
                "content_source_types": ["user-regular", "user-auto"],
                "sort_field": "created_at",
                "sort_order": "desc",
                "page_size": 10
            }
        )
        assert response.status_code == 200
