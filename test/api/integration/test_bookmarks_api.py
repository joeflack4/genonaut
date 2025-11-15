"""Integration tests for bookmark API endpoints."""

import pytest
import uuid
from typing import Dict, Any

from test.api.integration.test_api_endpoints import APITestClient
from test.api.integration.config import TEST_API_BASE_URL


@pytest.fixture
def api_client():
    """Provide API test client for making requests."""
    return APITestClient(TEST_API_BASE_URL)


@pytest.fixture
def test_user(api_client):
    """Create a test user for bookmark tests."""
    unique_id = str(uuid.uuid4())[:8]
    user_data = {
        "username": f"bookmark_user_{unique_id}",
        "email": f"bookmark_user_{unique_id}@example.com",
        "preferences": {"theme": "dark"}
    }
    response = api_client.post("/api/v1/users", json_data=user_data)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def test_content(api_client, test_user):
    """Create test content item for bookmarking."""
    content_data = {
        "title": "Test Content for Bookmarking",
        "content_type": "text",
        "content_data": "This is test content to be bookmarked",
        "prompt": "Test prompt for bookmark content",
        "creator_id": test_user["id"],
        "item_metadata": {"category": "test"},
        "is_private": False
    }
    response = api_client.post("/api/v1/content", json_data=content_data)
    assert response.status_code == 201
    return response.json()


@pytest.mark.api_server
class TestBookmarkCRUD:
    """Test basic bookmark CRUD operations."""

    def test_create_bookmark(self, api_client, test_user, test_content):
        """Test creating a bookmark."""
        bookmark_data = {
            "content_id": test_content["id"],
            "content_source_type": "items",
            "note": "This is my favorite content",
            "pinned": True,
            "is_public": False
        }
        response = api_client.post(
            f"/api/v1/bookmarks?user_id={test_user['id']}",
            json_data=bookmark_data
        )
        assert response.status_code == 201
        bookmark = response.json()
        assert bookmark["content_id"] == test_content["id"]
        assert bookmark["content_source_type"] == "items"
        assert bookmark["note"] == "This is my favorite content"
        assert bookmark["pinned"] is True
        assert bookmark["is_public"] is False
        assert "id" in bookmark
        assert "created_at" in bookmark

    def test_create_duplicate_bookmark(self, api_client, test_user, test_content):
        """Test that creating a duplicate bookmark fails."""
        bookmark_data = {
            "content_id": test_content["id"],
            "content_source_type": "items",
            "note": "First bookmark"
        }
        # Create first bookmark
        response1 = api_client.post(
            f"/api/v1/bookmarks?user_id={test_user['id']}",
            json_data=bookmark_data
        )
        assert response1.status_code == 201

        # Try to create duplicate
        response2 = api_client.post(
            f"/api/v1/bookmarks?user_id={test_user['id']}",
            json_data=bookmark_data
        )
        assert response2.status_code == 422

    def test_list_bookmarks(self, api_client, test_user, test_content):
        """Test listing user bookmarks."""
        # Create multiple bookmarks
        for i in range(3):
            content_response = api_client.post("/api/v1/content", json_data={
                "title": f"Content {i}",
                "content_type": "text",
                "content_data": f"Content {i}",
                "prompt": f"Prompt {i}",
                "creator_id": test_user["id"],
                "is_private": False
            })
            content = content_response.json()

            bookmark_data = {
                "content_id": content["id"],
                "content_source_type": "items",
                "note": f"Note {i}",
                "pinned": i == 0  # Only first is pinned
            }
            api_client.post(
                f"/api/v1/bookmarks?user_id={test_user['id']}",
                json_data=bookmark_data
            )

        # List all bookmarks
        response = api_client.get(f"/api/v1/bookmarks?user_id={test_user['id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3
        assert len(data["items"]) >= 3

    def test_list_pinned_bookmarks(self, api_client, test_user):
        """Test filtering bookmarks by pinned status."""
        # Create pinned and unpinned bookmarks
        for i in range(4):
            content_response = api_client.post("/api/v1/content", json_data={
                "title": f"Content {i}",
                "content_type": "text",
                "content_data": f"Content {i}",
                "prompt": f"Prompt {i}",
                "creator_id": test_user["id"],
                "is_private": False
            })
            content = content_response.json()

            bookmark_data = {
                "content_id": content["id"],
                "content_source_type": "items",
                "pinned": i < 2  # First 2 are pinned
            }
            api_client.post(
                f"/api/v1/bookmarks?user_id={test_user['id']}",
                json_data=bookmark_data
            )

        # List only pinned bookmarks
        response = api_client.get(
            f"/api/v1/bookmarks?user_id={test_user['id']}&pinned=true"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert all(item["pinned"] for item in data["items"])

    def test_get_bookmark(self, api_client, test_user, test_content):
        """Test getting a bookmark by ID."""
        # Create bookmark
        bookmark_data = {
            "content_id": test_content["id"],
            "content_source_type": "items",
            "note": "Test note"
        }
        create_response = api_client.post(
            f"/api/v1/bookmarks?user_id={test_user['id']}",
            json_data=bookmark_data
        )
        bookmark = create_response.json()

        # Get bookmark
        response = api_client.get(f"/api/v1/bookmarks/{bookmark['id']}")
        assert response.status_code == 200
        retrieved = response.json()
        assert retrieved["id"] == bookmark["id"]
        assert retrieved["note"] == "Test note"

    def test_update_bookmark(self, api_client, test_user, test_content):
        """Test updating a bookmark."""
        # Create bookmark
        bookmark_data = {
            "content_id": test_content["id"],
            "content_source_type": "items",
            "note": "Original note",
            "pinned": False
        }
        create_response = api_client.post(
            f"/api/v1/bookmarks?user_id={test_user['id']}",
            json_data=bookmark_data
        )
        bookmark = create_response.json()

        # Update bookmark
        update_data = {
            "note": "Updated note",
            "pinned": True
        }
        response = api_client.put(
            f"/api/v1/bookmarks/{bookmark['id']}",
            json_data=update_data
        )
        assert response.status_code == 200
        updated = response.json()
        assert updated["note"] == "Updated note"
        assert updated["pinned"] is True

    def test_delete_bookmark(self, api_client, test_user, test_content):
        """Test deleting a bookmark (soft delete)."""
        # Create bookmark
        bookmark_data = {
            "content_id": test_content["id"],
            "content_source_type": "items"
        }
        create_response = api_client.post(
            f"/api/v1/bookmarks?user_id={test_user['id']}",
            json_data=bookmark_data
        )
        bookmark = create_response.json()

        # Delete bookmark
        response = api_client.delete(f"/api/v1/bookmarks/{bookmark['id']}")
        assert response.status_code == 200

        # Verify bookmark is not in list
        list_response = api_client.get(f"/api/v1/bookmarks?user_id={test_user['id']}")
        data = list_response.json()
        bookmark_ids = [b["id"] for b in data["items"]]
        assert bookmark["id"] not in bookmark_ids


@pytest.mark.api_server
class TestBookmarkCategory:
    """Test bookmark category operations."""

    def test_create_category(self, api_client, test_user):
        """Test creating a bookmark category."""
        category_data = {
            "name": "My Favorites",
            "description": "All my favorite content",
            "color": "#FF5733",
            "icon": "star",
            "is_public": False
        }
        response = api_client.post(
            f"/api/v1/bookmark-categories?user_id={test_user['id']}",
            json_data=category_data
        )
        assert response.status_code == 201
        category = response.json()
        assert category["name"] == "My Favorites"
        assert category["description"] == "All my favorite content"
        assert category["color"] == "#FF5733"
        assert category["icon"] == "star"
        assert "id" in category

    def test_create_duplicate_category(self, api_client, test_user):
        """Test that creating a category with duplicate name fails."""
        category_data = {
            "name": "Test Category",
            "is_public": False
        }
        # Create first category
        response1 = api_client.post(
            f"/api/v1/bookmark-categories?user_id={test_user['id']}",
            json_data=category_data
        )
        assert response1.status_code == 201

        # Try to create duplicate
        response2 = api_client.post(
            f"/api/v1/bookmark-categories?user_id={test_user['id']}",
            json_data=category_data
        )
        assert response2.status_code == 422

    def test_list_categories(self, api_client, test_user):
        """Test listing user categories."""
        # Create multiple categories
        for i in range(3):
            category_data = {
                "name": f"Category {i}",
                "sort_index": i,
                "is_public": False
            }
            api_client.post(
                f"/api/v1/bookmark-categories?user_id={test_user['id']}",
                json_data=category_data
            )

        # List categories
        response = api_client.get(
            f"/api/v1/bookmark-categories?user_id={test_user['id']}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3
        assert len(data["items"]) >= 3

    def test_hierarchical_categories(self, api_client, test_user):
        """Test creating hierarchical categories with parent-child relationships."""
        # Create parent category
        parent_data = {
            "name": "Parent Category",
            "is_public": False
        }
        parent_response = api_client.post(
            f"/api/v1/bookmark-categories?user_id={test_user['id']}",
            json_data=parent_data
        )
        parent = parent_response.json()

        # Create child category
        child_data = {
            "name": "Child Category",
            "parent_id": parent["id"],
            "is_public": False
        }
        child_response = api_client.post(
            f"/api/v1/bookmark-categories?user_id={test_user['id']}",
            json_data=child_data
        )
        child = child_response.json()
        assert child["parent_id"] == parent["id"]

        # Get children of parent
        children_response = api_client.get(
            f"/api/v1/bookmark-categories/{parent['id']}/children"
        )
        assert children_response.status_code == 200
        children_data = children_response.json()
        assert len(children_data["items"]) >= 1

    def test_get_category(self, api_client, test_user):
        """Test getting a category by ID."""
        # Create category
        category_data = {
            "name": "Test Category",
            "description": "Test description",
            "is_public": False
        }
        create_response = api_client.post(
            f"/api/v1/bookmark-categories?user_id={test_user['id']}",
            json_data=category_data
        )
        category = create_response.json()

        # Get category
        response = api_client.get(f"/api/v1/bookmark-categories/{category['id']}")
        assert response.status_code == 200
        retrieved = response.json()
        assert retrieved["id"] == category["id"]
        assert retrieved["name"] == "Test Category"

    def test_update_category(self, api_client, test_user):
        """Test updating a category."""
        # Create category
        category_data = {
            "name": "Original Name",
            "is_public": False
        }
        create_response = api_client.post(
            f"/api/v1/bookmark-categories?user_id={test_user['id']}",
            json_data=category_data
        )
        category = create_response.json()

        # Update category
        update_data = {
            "name": "Updated Name",
            "description": "New description"
        }
        response = api_client.put(
            f"/api/v1/bookmark-categories/{category['id']}",
            json_data=update_data
        )
        assert response.status_code == 200
        updated = response.json()
        assert updated["name"] == "Updated Name"
        assert updated["description"] == "New description"

    def test_delete_category(self, api_client, test_user):
        """Test deleting a category."""
        # Create category
        category_data = {
            "name": "Category to Delete",
            "is_public": False
        }
        create_response = api_client.post(
            f"/api/v1/bookmark-categories?user_id={test_user['id']}",
            json_data=category_data
        )
        category = create_response.json()

        # Delete category
        response = api_client.delete(f"/api/v1/bookmark-categories/{category['id']}")
        assert response.status_code == 200

        # Verify category is deleted
        get_response = api_client.get(f"/api/v1/bookmark-categories/{category['id']}")
        assert get_response.status_code == 404


@pytest.mark.api_server
class TestCategoryMembership:
    """Test category membership operations."""

    def test_add_bookmark_to_category(self, api_client, test_user, test_content):
        """Test adding a bookmark to a category."""
        # Create bookmark
        bookmark_data = {
            "content_id": test_content["id"],
            "content_source_type": "items"
        }
        bookmark_response = api_client.post(
            f"/api/v1/bookmarks?user_id={test_user['id']}",
            json_data=bookmark_data
        )
        bookmark = bookmark_response.json()

        # Create category
        category_data = {
            "name": "Test Category",
            "is_public": False
        }
        category_response = api_client.post(
            f"/api/v1/bookmark-categories?user_id={test_user['id']}",
            json_data=category_data
        )
        category = category_response.json()

        # Add bookmark to category
        membership_data = {
            "category_id": category["id"],
            "position": 1
        }
        response = api_client.post(
            f"/api/v1/bookmarks/{bookmark['id']}/categories",
            json_data=membership_data
        )
        assert response.status_code == 201
        membership = response.json()
        assert membership["bookmark_id"] == bookmark["id"]
        assert membership["category_id"] == category["id"]
        assert membership["position"] == 1

    def test_remove_bookmark_from_category(self, api_client, test_user, test_content):
        """Test removing a bookmark from a category."""
        # Create bookmark
        bookmark_data = {
            "content_id": test_content["id"],
            "content_source_type": "items"
        }
        bookmark_response = api_client.post(
            f"/api/v1/bookmarks?user_id={test_user['id']}",
            json_data=bookmark_data
        )
        bookmark = bookmark_response.json()

        # Create category
        category_data = {
            "name": "Test Category",
            "is_public": False
        }
        category_response = api_client.post(
            f"/api/v1/bookmark-categories?user_id={test_user['id']}",
            json_data=category_data
        )
        category = category_response.json()

        # Add bookmark to category
        membership_data = {
            "category_id": category["id"]
        }
        api_client.post(
            f"/api/v1/bookmarks/{bookmark['id']}/categories",
            json_data=membership_data
        )

        # Remove bookmark from category
        response = api_client.delete(
            f"/api/v1/bookmarks/{bookmark['id']}/categories/{category['id']}"
        )
        assert response.status_code == 200

    def test_list_bookmarks_in_category(self, api_client, test_user):
        """Test listing bookmarks in a category."""
        # Create category
        category_data = {
            "name": "Test Category",
            "is_public": False
        }
        category_response = api_client.post(
            f"/api/v1/bookmark-categories?user_id={test_user['id']}",
            json_data=category_data
        )
        category = category_response.json()

        # Create bookmarks and add to category
        for i in range(3):
            content_response = api_client.post("/api/v1/content", json_data={
                "title": f"Content {i}",
                "content_type": "text",
                "content_data": f"Content {i}",
                "prompt": f"Prompt {i}",
                "creator_id": test_user["id"],
                "is_private": False
            })
            content = content_response.json()

            bookmark_response = api_client.post(
                f"/api/v1/bookmarks?user_id={test_user['id']}",
                json_data={
                    "content_id": content["id"],
                    "content_source_type": "items"
                }
            )
            bookmark = bookmark_response.json()

            # Add to category
            api_client.post(
                f"/api/v1/bookmarks/{bookmark['id']}/categories",
                json_data={"category_id": category["id"], "position": i}
            )

        # List bookmarks in category
        response = api_client.get(
            f"/api/v1/bookmark-categories/{category['id']}/bookmarks"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3
        assert len(data["bookmarks"]) >= 3

    def test_update_bookmark_position(self, api_client, test_user, test_content):
        """Test updating bookmark position in a category."""
        # Create bookmark
        bookmark_data = {
            "content_id": test_content["id"],
            "content_source_type": "items"
        }
        bookmark_response = api_client.post(
            f"/api/v1/bookmarks?user_id={test_user['id']}",
            json_data=bookmark_data
        )
        bookmark = bookmark_response.json()

        # Create category
        category_data = {
            "name": "Test Category",
            "is_public": False
        }
        category_response = api_client.post(
            f"/api/v1/bookmark-categories?user_id={test_user['id']}",
            json_data=category_data
        )
        category = category_response.json()

        # Add bookmark to category with position 1
        api_client.post(
            f"/api/v1/bookmarks/{bookmark['id']}/categories",
            json_data={"category_id": category["id"], "position": 1}
        )

        # Update position to 5
        response = api_client.put(
            f"/api/v1/bookmarks/{bookmark['id']}/categories/{category['id']}/position",
            json_data={"position": 5}
        )
        assert response.status_code == 200
        membership = response.json()
        assert membership["position"] == 5

    def test_list_bookmark_categories(self, api_client, test_user, test_content):
        """Test listing categories that a bookmark belongs to."""
        # Create bookmark
        bookmark_data = {
            "content_id": test_content["id"],
            "content_source_type": "items"
        }
        bookmark_response = api_client.post(
            f"/api/v1/bookmarks?user_id={test_user['id']}",
            json_data=bookmark_data
        )
        bookmark = bookmark_response.json()

        # Create multiple categories and add bookmark to them
        for i in range(2):
            category_response = api_client.post(
                f"/api/v1/bookmark-categories?user_id={test_user['id']}",
                json_data={"name": f"Category {i}", "is_public": False}
            )
            category = category_response.json()

            api_client.post(
                f"/api/v1/bookmarks/{bookmark['id']}/categories",
                json_data={"category_id": category["id"]}
            )

        # List categories for bookmark
        response = api_client.get(f"/api/v1/bookmarks/{bookmark['id']}/categories")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 2

    def test_sync_bookmark_categories_success(self, api_client, test_user, test_content):
        """Test syncing bookmark categories with a list of category IDs."""
        # Create bookmark
        bookmark_data = {
            "content_id": test_content["id"],
            "content_source_type": "items"
        }
        bookmark_response = api_client.post(
            f"/api/v1/bookmarks?user_id={test_user['id']}",
            json_data=bookmark_data
        )
        bookmark = bookmark_response.json()

        # Create three categories
        category_ids = []
        for i in range(3):
            category_response = api_client.post(
                f"/api/v1/bookmark-categories?user_id={test_user['id']}",
                json_data={"name": f"Category {i}", "is_public": False}
            )
            category = category_response.json()
            category_ids.append(category["id"])

        # Sync bookmark to first two categories
        sync_data = {
            "category_ids": category_ids[:2]
        }
        response = api_client.put(
            f"/api/v1/bookmarks/{bookmark['id']}/categories/sync?user_id={test_user['id']}",
            json_data=sync_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        result_category_ids = {item["category_id"] for item in data["items"]}
        assert result_category_ids == set(category_ids[:2])

    def test_sync_bookmark_categories_empty_list(self, api_client, test_user, test_content):
        """Test syncing bookmark categories with empty list defaults to Uncategorized."""
        # Create bookmark
        bookmark_data = {
            "content_id": test_content["id"],
            "content_source_type": "items"
        }
        bookmark_response = api_client.post(
            f"/api/v1/bookmarks?user_id={test_user['id']}",
            json_data=bookmark_data
        )
        bookmark = bookmark_response.json()

        # Sync with empty list
        sync_data = {
            "category_ids": []
        }
        response = api_client.put(
            f"/api/v1/bookmarks/{bookmark['id']}/categories/sync?user_id={test_user['id']}",
            json_data=sync_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        # Verify it's in the Uncategorized category
        # (We can't check the exact ID since it's created automatically,
        # but we can verify one membership exists)

    def test_sync_bookmark_categories_unauthorized(self, api_client, test_user, test_content):
        """Test syncing bookmark categories with wrong user fails."""
        # Create bookmark for test_user
        bookmark_data = {
            "content_id": test_content["id"],
            "content_source_type": "items"
        }
        bookmark_response = api_client.post(
            f"/api/v1/bookmarks?user_id={test_user['id']}",
            json_data=bookmark_data
        )
        bookmark = bookmark_response.json()

        # Create another user
        unique_id = str(uuid.uuid4())[:8]
        other_user_data = {
            "username": f"other_user_{unique_id}",
            "email": f"other_user_{unique_id}@example.com"
        }
        other_user_response = api_client.post("/api/v1/users", json_data=other_user_data)
        other_user = other_user_response.json()

        # Try to sync with other user's ID
        sync_data = {
            "category_ids": []
        }
        response = api_client.put(
            f"/api/v1/bookmarks/{bookmark['id']}/categories/sync?user_id={other_user['id']}",
            json_data=sync_data
        )
        assert response.status_code == 422

    def test_sync_bookmark_categories_nonexistent_bookmark(self, api_client, test_user):
        """Test syncing categories for non-existent bookmark returns 404."""
        import uuid as uuid_lib
        fake_bookmark_id = str(uuid_lib.uuid4())

        sync_data = {
            "category_ids": []
        }
        response = api_client.put(
            f"/api/v1/bookmarks/{fake_bookmark_id}/categories/sync?user_id={test_user['id']}",
            json_data=sync_data
        )
        assert response.status_code == 404

    def test_sync_bookmark_categories_nonexistent_category(self, api_client, test_user, test_content):
        """Test syncing with non-existent category returns 404."""
        # Create bookmark
        bookmark_data = {
            "content_id": test_content["id"],
            "content_source_type": "items"
        }
        bookmark_response = api_client.post(
            f"/api/v1/bookmarks?user_id={test_user['id']}",
            json_data=bookmark_data
        )
        bookmark = bookmark_response.json()

        # Try to sync with fake category ID
        import uuid as uuid_lib
        fake_category_id = str(uuid_lib.uuid4())

        sync_data = {
            "category_ids": [fake_category_id]
        }
        response = api_client.put(
            f"/api/v1/bookmarks/{bookmark['id']}/categories/sync?user_id={test_user['id']}",
            json_data=sync_data
        )
        assert response.status_code == 404


@pytest.mark.api_server
class TestBookmarkSortingAndContent:
    """Test bookmark sorting and content inclusion features (Phase 5)."""

    def test_list_bookmarks_with_content(self, api_client, test_user, test_content):
        """Test listing bookmarks with content data included."""
        # Create bookmark
        bookmark_data = {
            "content_id": test_content["id"],
            "content_source_type": "items",
            "note": "Test note"
        }
        api_client.post(
            f"/api/v1/bookmarks?user_id={test_user['id']}",
            json_data=bookmark_data
        )

        # List bookmarks with content
        response = api_client.get(
            f"/api/v1/bookmarks?user_id={test_user['id']}&include_content=true"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

        # Verify content data is included
        bookmark = data["items"][0]
        assert "content" in bookmark
        assert bookmark["content"] is not None
        assert bookmark["content"]["id"] == test_content["id"]
        assert bookmark["content"]["title"] == test_content["title"]
        assert "user_rating" in bookmark

    def test_list_bookmarks_without_content(self, api_client, test_user, test_content):
        """Test listing bookmarks without content data (legacy mode)."""
        # Create bookmark
        bookmark_data = {
            "content_id": test_content["id"],
            "content_source_type": "items"
        }
        api_client.post(
            f"/api/v1/bookmarks?user_id={test_user['id']}",
            json_data=bookmark_data
        )

        # List bookmarks without content
        response = api_client.get(
            f"/api/v1/bookmarks?user_id={test_user['id']}&include_content=false"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

        # Verify content data is NOT included
        bookmark = data["items"][0]
        assert "content" not in bookmark
        assert "user_rating" not in bookmark

    def test_bookmark_sorting_by_datetime_added(self, api_client, test_user):
        """Test sorting bookmarks by datetime_added."""
        # Create multiple content items and bookmarks
        bookmark_ids = []
        for i in range(3):
            content_data = {
                "title": f"Content {i}",
                "content_type": "text",
                "content_data": f"Content {i}",
                "prompt": "test",
                "creator_id": test_user["id"]
            }
            content_response = api_client.post("/api/v1/content", json_data=content_data)
            content = content_response.json()

            bookmark_data = {
                "content_id": content["id"],
                "content_source_type": "items"
            }
            bookmark_response = api_client.post(
                f"/api/v1/bookmarks?user_id={test_user['id']}",
                json_data=bookmark_data
            )
            bookmark_ids.append(bookmark_response.json()["id"])

        # List bookmarks sorted by datetime_added DESC (most recent first)
        response = api_client.get(
            f"/api/v1/bookmarks?user_id={test_user['id']}&sort_field=datetime_added&sort_order=desc"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 3

        # Verify DESC order (most recent first)
        for i in range(len(data["items"]) - 1):
            assert data["items"][i]["created_at"] >= data["items"][i + 1]["created_at"]

    def test_bookmark_sorting_by_quality_score(self, api_client, test_user):
        """Test sorting bookmarks by content quality_score."""
        # Create content items with different quality scores
        for i, score in enumerate([0.5, 0.9, 0.3]):
            content_data = {
                "title": f"Content Quality {score}",
                "content_type": "text",
                "content_data": f"Content {i}",
                "prompt": "test",
                "creator_id": test_user["id"],
                "quality_score": score
            }
            content_response = api_client.post("/api/v1/content", json_data=content_data)
            content = content_response.json()

            bookmark_data = {
                "content_id": content["id"],
                "content_source_type": "items"
            }
            api_client.post(
                f"/api/v1/bookmarks?user_id={test_user['id']}",
                json_data=bookmark_data
            )

        # List bookmarks sorted by quality_score DESC
        response = api_client.get(
            f"/api/v1/bookmarks?user_id={test_user['id']}&sort_field=quality_score&sort_order=desc&include_content=true"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 3

        # Verify DESC order (highest quality first)
        for i in range(len(data["items"]) - 1):
            score1 = data["items"][i]["content"]["quality_score"]
            score2 = data["items"][i + 1]["content"]["quality_score"]
            assert score1 >= score2

    def test_bookmark_sorting_alphabetical(self, api_client, test_user):
        """Test sorting bookmarks by content title alphabetically."""
        # Create content with alphabetically sortable titles
        titles = ["Zebra Content", "Apple Content", "Mango Content"]
        for title in titles:
            content_data = {
                "title": title,
                "content_type": "text",
                "content_data": "test",
                "prompt": "test",
                "creator_id": test_user["id"]
            }
            content_response = api_client.post("/api/v1/content", json_data=content_data)
            content = content_response.json()

            bookmark_data = {
                "content_id": content["id"],
                "content_source_type": "items"
            }
            api_client.post(
                f"/api/v1/bookmarks?user_id={test_user['id']}",
                json_data=bookmark_data
            )

        # List bookmarks sorted alphabetically ASC
        response = api_client.get(
            f"/api/v1/bookmarks?user_id={test_user['id']}&sort_field=alphabetical&sort_order=asc&include_content=true"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 3

        # Verify ASC alphabetical order
        for i in range(len(data["items"]) - 1):
            title1 = data["items"][i]["content"]["title"]
            title2 = data["items"][i + 1]["content"]["title"]
            assert title1 <= title2

    def test_category_bookmarks_with_content_and_sorting(self, api_client, test_user):
        """Test getting category bookmarks with content data and sorting."""
        # Create category
        category_data = {"name": "Sorted Category", "is_public": False}
        category_response = api_client.post(
            f"/api/v1/bookmark-categories?user_id={test_user['id']}",
            json_data=category_data
        )
        category = category_response.json()

        # Create bookmarks with different quality scores
        for i, score in enumerate([0.7, 0.9, 0.5]):
            content_data = {
                "title": f"Category Content {i}",
                "content_type": "text",
                "content_data": f"Content {i}",
                "prompt": "test",
                "creator_id": test_user["id"],
                "quality_score": score
            }
            content_response = api_client.post("/api/v1/content", json_data=content_data)
            content = content_response.json()

            # Create bookmark
            bookmark_data = {
                "content_id": content["id"],
                "content_source_type": "items"
            }
            bookmark_response = api_client.post(
                f"/api/v1/bookmarks?user_id={test_user['id']}",
                json_data=bookmark_data
            )
            bookmark = bookmark_response.json()

            # Add to category
            api_client.post(
                f"/api/v1/bookmarks/{bookmark['id']}/categories",
                json_data={"category_id": category["id"]}
            )

        # Get category bookmarks sorted by quality_score
        response = api_client.get(
            f"/api/v1/bookmark-categories/{category['id']}/bookmarks"
            f"?user_id={test_user['id']}&sort_field=quality_score&sort_order=desc&include_content=true"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3

        # Verify content is included and sorted by quality_score
        bookmarks = data["bookmarks"]
        assert all("content" in bm for bm in bookmarks)
        for i in range(len(bookmarks) - 1):
            score1 = bookmarks[i]["content"]["quality_score"]
            score2 = bookmarks[i + 1]["content"]["quality_score"]
            assert score1 >= score2

    def test_category_sorting_by_updated_at(self, api_client, test_user):
        """Test sorting bookmark categories by updated_at."""
        # Create multiple categories
        category_ids = []
        for i in range(3):
            category_data = {
                "name": f"Category {i}",
                "description": f"Description {i}",
                "is_public": False
            }
            response = api_client.post(
                f"/api/v1/bookmark-categories?user_id={test_user['id']}",
                json_data=category_data
            )
            category_ids.append(response.json()["id"])

        # Update middle category to make it most recent
        api_client.put(
            f"/api/v1/bookmark-categories/{category_ids[1]}",
            json_data={"description": "Updated description"}
        )

        # List categories sorted by updated_at DESC
        response = api_client.get(
            f"/api/v1/bookmark-categories?user_id={test_user['id']}&sort_field=updated_at&sort_order=desc"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 3

        # Verify DESC order by updated_at
        for i in range(len(data["items"]) - 1):
            updated1 = data["items"][i]["updated_at"]
            updated2 = data["items"][i + 1]["updated_at"]
            assert updated1 >= updated2

    def test_category_sorting_alphabetical(self, api_client, test_user):
        """Test sorting bookmark categories alphabetically by name."""
        # Create categories with alphabetically sortable names
        names = ["Zebra Category", "Apple Category", "Mango Category"]
        for name in names:
            api_client.post(
                f"/api/v1/bookmark-categories?user_id={test_user['id']}",
                json_data={"name": name, "is_public": False}
            )

        # List categories sorted alphabetically ASC
        response = api_client.get(
            f"/api/v1/bookmark-categories?user_id={test_user['id']}&sort_field=name&sort_order=asc"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 3

        # Verify ASC alphabetical order
        for i in range(len(data["items"]) - 1):
            name1 = data["items"][i]["name"]
            name2 = data["items"][i + 1]["name"]
            assert name1 <= name2
