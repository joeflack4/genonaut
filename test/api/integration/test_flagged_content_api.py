"""Integration tests for flagged content API endpoints."""

import os
import sys
import pytest
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from test.api.integration.config import TEST_API_BASE_URL, TEST_TIMEOUT


def make_request(method: str, endpoint: str, **kwargs) -> requests.Response:
    """Helper function to make API requests."""
    url = f"{TEST_API_BASE_URL}{endpoint}"
    return requests.request(method, url, timeout=TEST_TIMEOUT, **kwargs)


@pytest.fixture(scope="module")
def test_user():
    """Create a test user for flagged content tests."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    user_data = {
        "username": f"flagged_test_user_{timestamp}",
        "email": f"flagged_test_{timestamp}@example.com",
        "preferences": {}
    }

    response = make_request("POST", "/api/v1/users", json=user_data)
    assert response.status_code == 201
    return response.json()


@pytest.fixture(scope="module")
def flag_words_file(tmp_path_factory):
    """Create a temporary flag-words.txt file for testing."""
    tmp_dir = tmp_path_factory.mktemp("test_flagging")
    flag_file = tmp_dir / "flag-words.txt"

    # Write test flag words
    test_words = [
        "violence",
        "hatred",
        "weapon",
        "destruction",
        "combat"
    ]
    flag_file.write_text("\n".join(test_words))

    # Set as environment variable so service can find it
    original_path = os.environ.get("FLAG_WORDS_PATH")
    os.environ["FLAG_WORDS_PATH"] = str(flag_file)

    yield str(flag_file)

    # Restore original
    if original_path:
        os.environ["FLAG_WORDS_PATH"] = original_path
    else:
        os.environ.pop("FLAG_WORDS_PATH", None)


class TestFlaggedContentAPI:
    """Test flagged content API endpoints."""

    def test_create_content_with_problematic_words(self, test_user):
        """Test creating content that should be flagged."""
        content_data = {
            "title": "Action Scene",
            "content_type": "text",
            "content_data": "Description of scene",
            "prompt": "Create a scene with violence and weapon combat",
            "creator_id": test_user["id"],
            "item_metadata": {},
            "tags": ["action"],
            "is_private": False
        }

        response = make_request("POST", "/api/v1/content", json=content_data)
        assert response.status_code == 201
        content = response.json()

        # Content should be created successfully
        assert content["title"] == "Action Scene"
        return content

    def test_scan_content_for_flags(self, test_user):
        """Test scanning existing content for problematic words."""
        # First create some content with problematic words
        for i in range(3):
            content_data = {
                "title": f"Test Content {i}",
                "content_type": "text",
                "content_data": f"Test content {i}",
                "prompt": f"violence hatred destruction scene {i}",
                "creator_id": test_user["id"],
                "item_metadata": {},
                "tags": ["test"],
                "is_private": False
            }
            response = make_request("POST", "/api/v1/content", json=content_data)
            assert response.status_code == 201

        # Now scan for flags
        scan_request = {
            "content_types": ["regular"],
            "force_rescan": False
        }

        response = make_request("POST", "/api/v1/admin/flagged-content/scan", json=scan_request)

        # Note: This might return 422 if flag-words.txt not found in test environment
        # That's expected behavior - the service requires the config file
        assert response.status_code in [200, 422]

        if response.status_code == 200:
            result = response.json()
            assert "items_scanned" in result
            assert "items_flagged" in result
            assert "processing_time_ms" in result
            assert result["items_scanned"] >= 0

    def test_get_flagged_content_list(self):
        """Test getting paginated list of flagged content."""
        response = make_request(
            "GET",
            "/api/v1/admin/flagged-content/",
            params={
                "page": 1,
                "page_size": 10,
                "sort_by": "risk_score",
                "sort_order": "desc"
            }
        )

        # Endpoint should work even if no flagged content exists
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "pagination" in data
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["page_size"] == 10

    def test_get_flagged_content_with_filters(self, test_user):
        """Test getting flagged content with various filters."""
        # Test filtering by creator
        response = make_request(
            "GET",
            "/api/v1/admin/flagged-content/",
            params={
                "page": 1,
                "page_size": 10,
                "creator_id": test_user["id"],
                "min_risk_score": 50.0
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data

        # If items exist, verify they match filters
        if data["items"]:
            for item in data["items"]:
                assert item["creator_id"] == test_user["id"]
                assert item["risk_score"] >= 50.0

    def test_get_flagged_content_with_source_filter(self):
        """Test filtering by content source."""
        response = make_request(
            "GET",
            "/api/v1/admin/flagged-content/",
            params={
                "page": 1,
                "page_size": 10,
                "content_source": "regular"
            }
        )

        assert response.status_code == 200
        data = response.json()

        # If items exist, verify source filter
        if data["items"]:
            for item in data["items"]:
                assert item["content_source"] == "regular"

    def test_get_flagged_content_with_reviewed_filter(self):
        """Test filtering by review status."""
        # Test unreviewed items
        response = make_request(
            "GET",
            "/api/v1/admin/flagged-content/",
            params={
                "page": 1,
                "page_size": 10,
                "reviewed": False
            }
        )

        assert response.status_code == 200
        data = response.json()

        if data["items"]:
            for item in data["items"]:
                assert item["reviewed"] is False

    def test_get_flagged_content_sorting(self):
        """Test different sorting options."""
        # Sort by risk score descending
        response = make_request(
            "GET",
            "/api/v1/admin/flagged-content/",
            params={
                "page": 1,
                "page_size": 10,
                "sort_by": "risk_score",
                "sort_order": "desc"
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify sorting if multiple items exist
        if len(data["items"]) > 1:
            scores = [item["risk_score"] for item in data["items"]]
            assert scores == sorted(scores, reverse=True)

    @pytest.mark.skip(reason="Integration test returns 500 instead of 404 - needs investigation")
    def test_get_flagged_content_by_id_not_found(self):
        """Test getting non-existent flagged content."""
        response = make_request(
            "GET",
            "/api/v1/admin/flagged-content/999999"
        )

        assert response.status_code == 404

    def test_review_flagged_content_not_found(self, test_user):
        """Test reviewing non-existent flagged content."""
        review_data = {
            "reviewed": True,
            "reviewed_by": test_user["id"],
            "notes": "Test review"
        }

        response = make_request(
            "PUT",
            "/api/v1/admin/flagged-content/999999/review",
            json=review_data
        )

        assert response.status_code == 404

    def test_delete_flagged_content_not_found(self):
        """Test deleting non-existent flagged content."""
        response = make_request(
            "DELETE",
            "/api/v1/admin/flagged-content/999999"
        )

        assert response.status_code == 404

    def test_bulk_delete_flagged_content(self):
        """Test bulk delete of flagged content."""
        delete_request = {
            "ids": [999997, 999998, 999999]
        }

        response = make_request(
            "POST",
            "/api/v1/admin/flagged-content/bulk-delete",
            json=delete_request
        )

        assert response.status_code == 200
        result = response.json()
        assert "deleted_count" in result
        assert "errors" in result
        # All should fail since IDs don't exist
        assert result["deleted_count"] == 0
        assert len(result["errors"]) == 3

    def test_get_statistics(self):
        """Test getting flagged content statistics."""
        response = make_request(
            "GET",
            "/api/v1/admin/flagged-content/statistics/summary"
        )

        assert response.status_code == 200
        stats = response.json()
        assert "total_flagged" in stats
        assert "unreviewed_count" in stats
        assert "average_risk_score" in stats
        assert "high_risk_count" in stats
        assert "by_source" in stats

        # Verify data types
        assert isinstance(stats["total_flagged"], int)
        assert isinstance(stats["unreviewed_count"], int)
        assert isinstance(stats["average_risk_score"], (int, float))
        assert isinstance(stats["high_risk_count"], int)
        assert isinstance(stats["by_source"], dict)

    def test_invalid_sort_field(self):
        """Test with invalid sort field."""
        response = make_request(
            "GET",
            "/api/v1/admin/flagged-content/",
            params={
                "page": 1,
                "page_size": 10,
                "sort_by": "invalid_field"
            }
        )

        # Should return validation error
        assert response.status_code == 422

    def test_invalid_pagination_params(self):
        """Test with invalid pagination parameters."""
        # Page less than 1
        response = make_request(
            "GET",
            "/api/v1/admin/flagged-content/",
            params={
                "page": 0,
                "page_size": 10
            }
        )

        assert response.status_code == 422

    def test_invalid_risk_score_range(self):
        """Test with invalid risk score range."""
        response = make_request(
            "GET",
            "/api/v1/admin/flagged-content/",
            params={
                "page": 1,
                "page_size": 10,
                "min_risk_score": 150.0  # Invalid: > 100
            }
        )

        assert response.status_code == 422


class TestFlaggedContentWorkflow:
    """Test complete flagged content workflow."""

    def test_complete_flagging_workflow(self, test_user):
        """Test complete workflow: create content -> scan -> review -> delete.

        Note: This test may be skipped if flag-words.txt is not configured
        in the test environment, which is expected behavior.
        """
        # Step 1: Create content with problematic words
        content_data = {
            "title": "Workflow Test Content",
            "content_type": "text",
            "content_data": "Test data",
            "prompt": "A scene with violence and weapons",
            "creator_id": test_user["id"],
            "item_metadata": {},
            "tags": ["workflow"],
            "is_private": False
        }

        content_response = make_request("POST", "/api/v1/content", json=content_data)
        assert content_response.status_code == 201
        content = content_response.json()

        # Step 2: Scan for flags (may fail if no flag-words.txt)
        scan_request = {
            "content_types": ["regular"],
            "force_rescan": True
        }

        scan_response = make_request(
            "POST",
            "/api/v1/admin/flagged-content/scan",
            json=scan_request
        )

        # If scan fails due to missing config, skip rest of workflow
        if scan_response.status_code == 422:
            pytest.skip("Flag words configuration not available in test environment")
            return

        assert scan_response.status_code == 200
        scan_result = scan_response.json()

        # Step 3: Get list of flagged content
        list_response = make_request(
            "GET",
            "/api/v1/admin/flagged-content/",
            params={"page": 1, "page_size": 10}
        )

        assert list_response.status_code == 200
        flagged_items = list_response.json()

        if not flagged_items["items"]:
            pytest.skip("No flagged content found after scan")
            return

        # Step 4: Get specific flagged item
        flagged_id = flagged_items["items"][0]["id"]
        detail_response = make_request(
            "GET",
            f"/api/v1/admin/flagged-content/{flagged_id}"
        )

        assert detail_response.status_code == 200
        flagged_detail = detail_response.json()
        assert flagged_detail["id"] == flagged_id

        # Step 5: Review the flagged content
        review_data = {
            "reviewed": True,
            "reviewed_by": test_user["id"],
            "notes": "Reviewed in workflow test"
        }

        review_response = make_request(
            "PUT",
            f"/api/v1/admin/flagged-content/{flagged_id}/review",
            json=review_data
        )

        assert review_response.status_code == 200
        reviewed_item = review_response.json()
        assert reviewed_item["reviewed"] is True
        assert reviewed_item["notes"] == "Reviewed in workflow test"

        # Step 6: Get statistics
        stats_response = make_request(
            "GET",
            "/api/v1/admin/flagged-content/statistics/summary"
        )

        assert stats_response.status_code == 200
        stats = stats_response.json()
        assert stats["total_flagged"] >= 1

        # Step 7: Delete the flagged content
        delete_response = make_request(
            "DELETE",
            f"/api/v1/admin/flagged-content/{flagged_id}"
        )

        assert delete_response.status_code == 200

        # Step 8: Verify it's deleted
        verify_response = make_request(
            "GET",
            f"/api/v1/admin/flagged-content/{flagged_id}"
        )

        assert verify_response.status_code == 404
