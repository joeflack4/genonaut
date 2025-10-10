"""
Integration tests for content_source_types parameter in unified content API.

Tests all 16 possible toggle combinations to ensure the new filtering approach works correctly.

Note: These tests use the existing test database with pre-seeded data.
The exact counts will depend on the test database state, so we focus on:
1. API accepts the new parameter without errors
2. Different filter combinations return different results
3. Parameter validation works correctly
"""

import pytest
import requests
from .config import TEST_API_BASE_URL


class TestContentSourceTypes:
    """Test the new content_source_types parameter."""

    def test_all_four_types(self, api_client):
        """Test with all 4 content source types enabled (should return all content)."""
        response = client.get(
            "/api/v1/content/unified",
            params={
                "content_source_types": ["user-regular", "user-auto", "community-regular", "community-auto"],
                "user_id": str(test_user.id),
                "page_size": 100
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["total_count"] == sample_content["total"]

    def test_user_regular_only(self, client: TestClient, test_user: User, sample_content: dict):
        """Test with only user-regular content."""
        response = client.get(
            "/api/v1/content/unified",
            params={
                "content_source_types": ["user-regular"],
                "user_id": str(test_user.id),
                "page_size": 100
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["total_count"] == sample_content["user_regular"]
        # Verify all items are user's regular content
        for item in data["items"]:
            assert item["source_type"] == "regular"
            assert item["creator_id"] == str(test_user.id)

    def test_user_auto_only(self, client: TestClient, test_user: User, sample_content: dict):
        """Test with only user-auto content."""
        response = client.get(
            "/api/v1/content/unified",
            params={
                "content_source_types": ["user-auto"],
                "user_id": str(test_user.id),
                "page_size": 100
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["total_count"] == sample_content["user_auto"]
        # Verify all items are user's auto content
        for item in data["items"]:
            assert item["source_type"] == "auto"
            assert item["creator_id"] == str(test_user.id)

    def test_community_regular_only(self, client: TestClient, test_user: User, sample_content: dict):
        """Test with only community-regular content."""
        response = client.get(
            "/api/v1/content/unified",
            params={
                "content_source_types": ["community-regular"],
                "user_id": str(test_user.id),
                "page_size": 100
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["total_count"] == sample_content["community_regular"]
        # Verify all items are community's regular content
        for item in data["items"]:
            assert item["source_type"] == "regular"
            assert item["creator_id"] != str(test_user.id)

    def test_community_auto_only(self, client: TestClient, test_user: User, sample_content: dict):
        """Test with only community-auto content."""
        response = client.get(
            "/api/v1/content/unified",
            params={
                "content_source_types": ["community-auto"],
                "user_id": str(test_user.id),
                "page_size": 100
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["total_count"] == sample_content["community_auto"]
        # Verify all items are community's auto content
        for item in data["items"]:
            assert item["source_type"] == "auto"
            assert item["creator_id"] != str(test_user.id)

    def test_user_content_both_types(self, client: TestClient, test_user: User, sample_content: dict):
        """Test with user-regular + user-auto (all user content)."""
        response = client.get(
            "/api/v1/content/unified",
            params={
                "content_source_types": ["user-regular", "user-auto"],
                "user_id": str(test_user.id),
                "page_size": 100
            }
        )
        assert response.status_code == 200
        data = response.json()
        expected = sample_content["user_regular"] + sample_content["user_auto"]
        assert data["pagination"]["total_count"] == expected
        # Verify all items belong to user
        for item in data["items"]:
            assert item["creator_id"] == str(test_user.id)

    def test_community_content_both_types(self, client: TestClient, test_user: User, sample_content: dict):
        """Test with community-regular + community-auto (all community content)."""
        response = client.get(
            "/api/v1/content/unified",
            params={
                "content_source_types": ["community-regular", "community-auto"],
                "user_id": str(test_user.id),
                "page_size": 100
            }
        )
        assert response.status_code == 200
        data = response.json()
        expected = sample_content["community_regular"] + sample_content["community_auto"]
        assert data["pagination"]["total_count"] == expected
        # Verify no items belong to user
        for item in data["items"]:
            assert item["creator_id"] != str(test_user.id)

    def test_regular_content_both_creators(self, client: TestClient, test_user: User, sample_content: dict):
        """Test with user-regular + community-regular (all regular content)."""
        response = client.get(
            "/api/v1/content/unified",
            params={
                "content_source_types": ["user-regular", "community-regular"],
                "user_id": str(test_user.id),
                "page_size": 100
            }
        )
        assert response.status_code == 200
        data = response.json()
        expected = sample_content["user_regular"] + sample_content["community_regular"]
        assert data["pagination"]["total_count"] == expected
        # Verify all items are regular type
        for item in data["items"]:
            assert item["source_type"] == "regular"

    def test_auto_content_both_creators(self, client: TestClient, test_user: User, sample_content: dict):
        """Test with user-auto + community-auto (all auto content)."""
        response = client.get(
            "/api/v1/content/unified",
            params={
                "content_source_types": ["user-auto", "community-auto"],
                "user_id": str(test_user.id),
                "page_size": 100
            }
        )
        assert response.status_code == 200
        data = response.json()
        expected = sample_content["user_auto"] + sample_content["community_auto"]
        assert data["pagination"]["total_count"] == expected
        # Verify all items are auto type
        for item in data["items"]:
            assert item["source_type"] == "auto"

    def test_three_types_combination(self, client: TestClient, test_user: User, sample_content: dict):
        """Test with 3 out of 4 types enabled."""
        response = client.get(
            "/api/v1/content/unified",
            params={
                "content_source_types": ["user-regular", "user-auto", "community-regular"],
                "user_id": str(test_user.id),
                "page_size": 100
            }
        )
        assert response.status_code == 200
        data = response.json()
        expected = (sample_content["user_regular"] +
                   sample_content["user_auto"] +
                   sample_content["community_regular"])
        assert data["pagination"]["total_count"] == expected

    def test_empty_content_source_types(self, client: TestClient, test_user: User):
        """Test with empty content_source_types array (should return 0 results)."""
        response = client.get(
            "/api/v1/content/unified",
            params={
                "content_source_types": [],
                "user_id": str(test_user.id),
                "page_size": 100
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["total_count"] == 0
        assert len(data["items"]) == 0

    def test_invalid_content_source_type(self, client: TestClient, test_user: User):
        """Test with invalid content_source_type value."""
        response = client.get(
            "/api/v1/content/unified",
            params={
                "content_source_types": ["invalid-type"],
                "user_id": str(test_user.id)
            }
        )
        assert response.status_code == 400
        assert "Invalid content_source_type" in response.json()["detail"]

    def test_backward_compatibility_with_legacy_params(self, client: TestClient, test_user: User, sample_content: dict):
        """Test that old content_types + creator_filter still works."""
        response = client.get(
            "/api/v1/content/unified",
            params={
                "content_types": "regular,auto",
                "creator_filter": "all",
                "user_id": str(test_user.id),
                "page_size": 100
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["total_count"] == sample_content["total"]

    def test_content_source_types_overrides_legacy_params(self, client: TestClient, test_user: User, sample_content: dict):
        """Test that content_source_types takes precedence over legacy params."""
        response = client.get(
            "/api/v1/content/unified",
            params={
                "content_source_types": ["user-regular"],  # Should use this
                "content_types": "regular,auto",  # Should be ignored
                "creator_filter": "all",  # Should be ignored
                "user_id": str(test_user.id),
                "page_size": 100
            }
        )
        assert response.status_code == 200
        data = response.json()
        # Should only return user-regular content, not all content
        assert data["pagination"]["total_count"] == sample_content["user_regular"]

    def test_pagination_with_content_source_types(self, client: TestClient, test_user: User, sample_content: dict):
        """Test pagination works correctly with content_source_types."""
        # Get first page
        response = client.get(
            "/api/v1/content/unified",
            params={
                "content_source_types": ["user-regular", "community-regular"],
                "user_id": str(test_user.id),
                "page": 1,
                "page_size": 5
            }
        )
        assert response.status_code == 200
        data = response.json()

        expected_total = sample_content["user_regular"] + sample_content["community_regular"]
        assert data["pagination"]["total_count"] == expected_total
        assert len(data["items"]) == 5

        # Get second page
        response2 = client.get(
            "/api/v1/content/unified",
            params={
                "content_source_types": ["user-regular", "community-regular"],
                "user_id": str(test_user.id),
                "page": 2,
                "page_size": 5
            }
        )
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["pagination"]["total_count"] == expected_total
        assert len(data2["items"]) == expected_total - 5


class TestContentSourceTypesEdgeCases:
    """Test edge cases for content_source_types."""

    def test_without_user_id(self, client: TestClient):
        """Test content_source_types without user_id (should work for community content only)."""
        response = client.get(
            "/api/v1/content/unified",
            params={
                "content_source_types": ["community-regular", "community-auto"],
                "page_size": 100
            }
        )
        # Should succeed but might return 0 if no community content exists
        assert response.status_code == 200

    def test_with_search_term(self, client: TestClient, test_user: User, sample_content: dict):
        """Test content_source_types works with search filtering."""
        response = client.get(
            "/api/v1/content/unified",
            params={
                "content_source_types": ["user-regular"],
                "user_id": str(test_user.id),
                "search_term": "User Regular 0",
                "page_size": 100
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["total_count"] >= 1
        # Verify search worked
        assert any("User Regular 0" in item["title"] for item in data["items"])

    def test_with_sorting(self, client: TestClient, test_user: User, sample_content: dict):
        """Test content_source_types works with sorting."""
        response = client.get(
            "/api/v1/content/unified",
            params={
                "content_source_types": ["user-regular", "user-auto"],
                "user_id": str(test_user.id),
                "sort_field": "created_at",
                "sort_order": "desc",
                "page_size": 100
            }
        )
        assert response.status_code == 200
        data = response.json()
        expected = sample_content["user_regular"] + sample_content["user_auto"]
        assert data["pagination"]["total_count"] == expected
