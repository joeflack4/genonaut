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
