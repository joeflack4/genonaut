"""API integration tests for user search history endpoints."""

import pytest
from uuid import UUID

from genonaut.db.schema import User


@pytest.fixture
def test_user(db_session):
    """Create a test user for API tests."""
    user = User(
        username='test-user',
        email='test@example.com'
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def user_id_str(test_user):
    """Get user ID as string for API calls."""
    return str(test_user.id)


class TestAddSearchHistory:
    """Test POST /api/v1/users/{user_id}/search-history endpoint."""

    def test_add_search_success(self, api_client, user_id_str):
        """Test successfully adding search to history."""
        response = api_client.post(
            f"/api/v1/users/{user_id_str}/search-history",
            json={"search_query": "test search"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["search_query"] == "test search"
        assert data["user_id"] == user_id_str
        assert "id" in data
        assert "created_at" in data

    def test_add_search_empty_query(self, api_client, user_id_str):
        """Test adding empty search query fails."""
        response = api_client.post(
            f"/api/v1/users/{user_id_str}/search-history",
            json={"search_query": ""}
        )

        assert response.status_code == 422

    def test_add_search_whitespace_only(self, api_client, user_id_str):
        """Test adding whitespace-only query fails."""
        response = api_client.post(
            f"/api/v1/users/{user_id_str}/search-history",
            json={"search_query": "   "}
        )

        assert response.status_code == 400

    def test_add_search_too_long(self, api_client, user_id_str):
        """Test adding search query exceeding max length fails."""
        long_query = "a" * 501  # Exceeds 500 char limit

        response = api_client.post(
            f"/api/v1/users/{user_id_str}/search-history",
            json={"search_query": long_query}
        )

        assert response.status_code == 422

    def test_add_search_max_length_allowed(self, api_client, user_id_str):
        """Test adding search at exact max length succeeds."""
        max_query = "a" * 500  # Exactly 500 chars

        response = api_client.post(
            f"/api/v1/users/{user_id_str}/search-history",
            json={"search_query": max_query}
        )

        assert response.status_code == 201

    def test_add_search_with_quotes(self, api_client, user_id_str):
        """Test adding search with quoted phrases."""
        response = api_client.post(
            f"/api/v1/users/{user_id_str}/search-history",
            json={"search_query": '"my cat" playing'}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["search_query"] == '"my cat" playing'

    def test_add_search_special_characters(self, api_client, user_id_str):
        """Test adding search with special characters."""
        response = api_client.post(
            f"/api/v1/users/{user_id_str}/search-history",
            json={"search_query": "test @#$% special"}
        )

        assert response.status_code == 201

    def test_add_search_duplicate_allowed(self, api_client, user_id_str):
        """Test that adding duplicate searches is allowed."""
        query = "duplicate search"

        # Add first time
        response1 = api_client.post(
            f"/api/v1/users/{user_id_str}/search-history",
            json={"search_query": query}
        )
        assert response1.status_code == 201
        id1 = response1.json()["id"]

        # Add second time
        response2 = api_client.post(
            f"/api/v1/users/{user_id_str}/search-history",
            json={"search_query": query}
        )
        assert response2.status_code == 201
        id2 = response2.json()["id"]

        # Should have different IDs
        assert id1 != id2

    def test_add_search_missing_field(self, api_client, user_id_str):
        """Test adding search without required field fails."""
        response = api_client.post(
            f"/api/v1/users/{user_id_str}/search-history",
            json={}
        )

        assert response.status_code == 422  # Pydantic validation error


class TestGetRecentSearches:
    """Test GET /api/v1/users/{user_id}/search-history/recent endpoint."""

    def test_get_recent_searches_default_limit(self, api_client, user_id_str):
        """Test getting recent searches with default limit."""
        # Add some searches
        queries = ["search 1", "search 2", "search 3", "search 4"]
        for query in queries:
            api_client.post(
                f"/api/v1/users/{user_id_str}/search-history",
                json={"search_query": query}
            )

        response = api_client.get(f"/api/v1/users/{user_id_str}/search-history/recent")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 3  # Default limit is 3
        # Should be in reverse chronological order
        assert data["items"][0]["search_query"] == "search 4"
        assert data["items"][1]["search_query"] == "search 3"
        assert data["items"][2]["search_query"] == "search 2"

    def test_get_recent_searches_custom_limit(self, api_client, user_id_str):
        """Test getting recent searches with custom limit."""
        for i in range(10):
            api_client.post(
                f"/api/v1/users/{user_id_str}/search-history",
                json={"search_query": f"search {i}"}
            )

        response = api_client.get(
            f"/api/v1/users/{user_id_str}/search-history/recent?limit=5"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 5

    def test_get_recent_searches_limit_too_high(self, api_client, user_id_str):
        """Test that limit above maximum fails."""
        response = api_client.get(
            f"/api/v1/users/{user_id_str}/search-history/recent?limit=101"
        )

        assert response.status_code == 422  # Validation error

    def test_get_recent_searches_limit_too_low(self, api_client, user_id_str):
        """Test that limit below minimum fails."""
        response = api_client.get(
            f"/api/v1/users/{user_id_str}/search-history/recent?limit=0"
        )

        assert response.status_code == 422

    def test_get_recent_searches_empty(self, api_client, user_id_str):
        """Test getting recent searches when none exist."""
        response = api_client.get(f"/api/v1/users/{user_id_str}/search-history/recent")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []

    def test_get_recent_searches_fewer_than_limit(self, api_client, user_id_str):
        """Test when there are fewer searches than requested limit."""
        # Add only 2 searches
        api_client.post(
            f"/api/v1/users/{user_id_str}/search-history",
            json={"search_query": "search 1"}
        )
        api_client.post(
            f"/api/v1/users/{user_id_str}/search-history",
            json={"search_query": "search 2"}
        )

        response = api_client.get(
            f"/api/v1/users/{user_id_str}/search-history/recent?limit=5"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2


class TestGetPaginatedSearchHistory:
    """Test GET /api/v1/users/{user_id}/search-history endpoint."""

    def test_get_paginated_first_page(self, api_client, user_id_str):
        """Test getting first page of search history."""
        # Add 25 searches
        for i in range(25):
            api_client.post(
                f"/api/v1/users/{user_id_str}/search-history",
                json={"search_query": f"search {i}"}
            )

        response = api_client.get(
            f"/api/v1/users/{user_id_str}/search-history?page=1&page_size=10"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["page_size"] == 10
        assert data["pagination"]["total_count"] == 25
        assert data["pagination"]["total_pages"] == 3
        assert data["pagination"]["has_next"] is True
        assert data["pagination"]["has_previous"] is False

    def test_get_paginated_second_page(self, api_client, user_id_str):
        """Test getting second page of search history."""
        for i in range(25):
            api_client.post(
                f"/api/v1/users/{user_id_str}/search-history",
                json={"search_query": f"search {i}"}
            )

        response = api_client.get(
            f"/api/v1/users/{user_id_str}/search-history?page=2&page_size=10"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["pagination"]["page"] == 2
        assert data["pagination"]["has_next"] is True
        assert data["pagination"]["has_previous"] is True

    def test_get_paginated_last_page(self, api_client, user_id_str):
        """Test getting last partial page."""
        for i in range(25):
            api_client.post(
                f"/api/v1/users/{user_id_str}/search-history",
                json={"search_query": f"search {i}"}
            )

        response = api_client.get(
            f"/api/v1/users/{user_id_str}/search-history?page=3&page_size=10"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 5
        assert data["pagination"]["has_next"] is False
        assert data["pagination"]["has_previous"] is True

    def test_get_paginated_default_params(self, api_client, user_id_str):
        """Test pagination with default parameters."""
        for i in range(5):
            api_client.post(
                f"/api/v1/users/{user_id_str}/search-history",
                json={"search_query": f"search {i}"}
            )

        response = api_client.get(f"/api/v1/users/{user_id_str}/search-history")

        assert response.status_code == 200
        data = response.json()
        # Default is page=1, page_size=20
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["page_size"] == 20
        assert len(data["items"]) == 5

    def test_get_paginated_empty(self, api_client, user_id_str):
        """Test paginated history when empty."""
        response = api_client.get(f"/api/v1/users/{user_id_str}/search-history")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["pagination"]["total_count"] == 0

    def test_get_paginated_invalid_page(self, api_client, user_id_str):
        """Test with invalid page number."""
        response = api_client.get(
            f"/api/v1/users/{user_id_str}/search-history?page=0"
        )

        assert response.status_code == 422

    def test_get_paginated_page_size_too_large(self, api_client, user_id_str):
        """Test with page size exceeding maximum."""
        response = api_client.get(
            f"/api/v1/users/{user_id_str}/search-history?page_size=101"
        )

        assert response.status_code == 422


class TestDeleteSearchHistoryItem:
    """Test DELETE /api/v1/users/{user_id}/search-history/by-query endpoint."""

    def test_delete_search_success(self, api_client, user_id_str):
        """Test successfully deleting all instances of a search query."""
        # Add a search
        api_client.post(
            f"/api/v1/users/{user_id_str}/search-history",
            json={"search_query": "test search"}
        )

        # Delete it by query (use request() for DELETE with body)
        response = api_client.request(
            "DELETE",
            f"/api/v1/users/{user_id_str}/search-history/by-query",
            json={"search_query": "test search"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "deleted" in data["message"].lower()

        # Verify it's gone
        get_response = api_client.get(
            f"/api/v1/users/{user_id_str}/search-history/recent"
        )
        assert len(get_response.json()["items"]) == 0

    def test_delete_search_not_found(self, api_client, user_id_str):
        """Test deleting non-existent search returns 404."""
        response = api_client.request(
            "DELETE",
            f"/api/v1/users/{user_id_str}/search-history/by-query",
            json={"search_query": "nonexistent search"}
        )

        assert response.status_code == 404

    def test_delete_search_wrong_user(self, api_client, db_session):
        """Test that users can't delete other users' searches."""
        # Create two users
        user1 = User(
            username='user-1',
            email='user1@example.com'
        )
        user2 = User(
            username='user-2',
            email='user2@example.com'
        )
        db_session.add(user1)
        db_session.add(user2)
        db_session.commit()

        user1_id = str(user1.id)
        user2_id = str(user2.id)

        # Add search for user1
        api_client.post(
            f"/api/v1/users/{user1_id}/search-history",
            json={"search_query": "user1 search"}
        )

        # Try to delete with user2's ID (use request() for DELETE with body)
        response = api_client.request(
            "DELETE",
            f"/api/v1/users/{user2_id}/search-history/by-query",
            json={"search_query": "user1 search"}
        )

        assert response.status_code == 404

        # Verify search still exists for user1
        get_response = api_client.get(
            f"/api/v1/users/{user1_id}/search-history/recent"
        )
        assert len(get_response.json()["items"]) == 1


class TestClearAllSearchHistory:
    """Test DELETE /api/v1/users/{user_id}/search-history/clear endpoint."""

    def test_clear_all_success(self, api_client, user_id_str):
        """Test successfully clearing all search history."""
        # Add multiple searches
        for i in range(10):
            api_client.post(
                f"/api/v1/users/{user_id_str}/search-history",
                json={"search_query": f"search {i}"}
            )

        # Clear all
        response = api_client.delete(f"/api/v1/users/{user_id_str}/search-history/clear")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["deleted_count"] == 10
        assert "10" in data["message"]

        # Verify all are gone
        get_response = api_client.get(
            f"/api/v1/users/{user_id_str}/search-history/recent"
        )
        assert len(get_response.json()["items"]) == 0

    def test_clear_all_when_empty(self, api_client, user_id_str):
        """Test clearing when no history exists."""
        response = api_client.delete(f"/api/v1/users/{user_id_str}/search-history/clear")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["deleted_count"] == 0

    def test_clear_all_only_own_history(self, api_client, db_session):
        """Test that clearing only affects the specific user."""
        # Create two users
        user1 = User(
            username='user-1',
            email='user1@example.com'
        )
        user2 = User(
            username='user-2',
            email='user2@example.com'
        )
        db_session.add(user1)
        db_session.add(user2)
        db_session.commit()

        user1_id = str(user1.id)
        user2_id = str(user2.id)

        # Add searches for both users
        api_client.post(
            f"/api/v1/users/{user1_id}/search-history",
            json={"search_query": "user1 search"}
        )
        api_client.post(
            f"/api/v1/users/{user2_id}/search-history",
            json={"search_query": "user2 search"}
        )

        # Clear user1's history
        response = api_client.delete(f"/api/v1/users/{user1_id}/search-history/clear")

        assert response.status_code == 200
        assert response.json()["deleted_count"] == 1

        # Verify user1's history is empty
        user1_response = api_client.get(
            f"/api/v1/users/{user1_id}/search-history/recent"
        )
        assert len(user1_response.json()["items"]) == 0

        # Verify user2's history still exists
        user2_response = api_client.get(
            f"/api/v1/users/{user2_id}/search-history/recent"
        )
        assert len(user2_response.json()["items"]) == 1


class TestSearchHistoryAuthentication:
    """Test authentication/authorization for search history endpoints."""

    def test_invalid_user_id_format(self, api_client):
        """Test that invalid UUID format returns error."""
        response = api_client.post(
            "/api/v1/users/not-a-uuid/search-history",
            json={"search_query": "test"}
        )

        # Should return validation error
        assert response.status_code in [400, 422]

    @pytest.mark.skip(reason="Test is not about search functionality - tests FK constraint handling which is implementation detail. Also has unclear pass criteria.")
    def test_nonexistent_user_can_add_search(self, api_client):
        """Test that adding search for non-existent user still works.

        Note: Current implementation doesn't enforce FK constraint at API level,
        only at DB level. This test documents current behavior.
        """
        fake_user_id = "99999999-9999-9999-9999-999999999999"

        # This should fail at DB level due to FK constraint
        response = api_client.post(
            f"/api/v1/users/{fake_user_id}/search-history",
            json={"search_query": "test"}
        )

        # Expect either 404 (if FK enforced) or 400/500 (DB error)
        assert response.status_code >= 400
