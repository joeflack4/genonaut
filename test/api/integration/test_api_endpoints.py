"""Integration tests for API endpoints that require a running web server."""

import os
import pytest
import requests
import json
from typing import Dict, Any, Optional

# Configuration for API testing
TEST_API_BASE_URL = os.getenv("API_BASE_URL", "http://0.0.0.0:8099")
TEST_TIMEOUT = 30  # seconds


class APITestClient:
    """Helper class for making API requests during testing."""
    
    def __init__(self, base_url: str = TEST_API_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> requests.Response:
        """Make GET request to API endpoint."""
        url = f"{self.base_url}{endpoint}"
        return self.session.get(url, params=params, timeout=TEST_TIMEOUT)
    
    def post(self, endpoint: str, data: Optional[Dict] = None, json_data: Optional[Dict] = None) -> requests.Response:
        """Make POST request to API endpoint."""
        url = f"{self.base_url}{endpoint}"
        return self.session.post(url, data=data, json=json_data, timeout=TEST_TIMEOUT)
    
    def put(self, endpoint: str, data: Optional[Dict] = None, json_data: Optional[Dict] = None) -> requests.Response:
        """Make PUT request to API endpoint."""
        url = f"{self.base_url}{endpoint}"
        return self.session.put(url, data=data, json=json_data, timeout=TEST_TIMEOUT)
    
    def delete(self, endpoint: str) -> requests.Response:
        """Make DELETE request to API endpoint."""
        url = f"{self.base_url}{endpoint}"
        return self.session.delete(url, timeout=TEST_TIMEOUT)


@pytest.fixture
def api_client():
    """Provide API test client for making requests."""
    return APITestClient()


@pytest.fixture
def test_user_data():
    """Sample user data for testing."""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    return {
        "username": f"testuser_{unique_id}",
        "email": f"testuser_{unique_id}@example.com",
        "preferences": {"theme": "dark", "notifications": True}
    }


@pytest.fixture
def test_content_data():
    """Sample content data for testing."""
    return {
        "title": "Test Content for API",
        "content_type": "text",
        "content_data": "This is test content created via API",
        "creator_id": 1,  # Will be updated with actual user ID
        "item_metadata": {"category": "test", "source": "api_test"},
        "tags": ["test", "api", "integration"],
        "is_public": True,
        "is_private": False
    }


class TestSystemEndpoints:
    """Test system/health endpoints."""
    
    def test_health_check(self, api_client):
        """Test the health check endpoint."""
        response = api_client.get("/api/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "database" in data
        assert data["status"] == "healthy"
    
    def test_root_endpoint(self, api_client):
        """Test the root endpoint."""
        response = api_client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "Genonaut API" in data["message"]
    
    def test_database_info(self, api_client):
        """Test the database info endpoint."""
        response = api_client.get("/api/v1/databases")
        assert response.status_code == 200
        
        data = response.json()
        assert "current_database" in data
        assert "available_databases" in data
        assert isinstance(data["available_databases"], list)
    
    def test_global_stats(self, api_client):
        """Test the global statistics endpoint."""
        response = api_client.get("/api/v1/stats/global")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_users" in data
        assert "total_content" in data
        assert "total_interactions" in data
        assert "total_recommendations" in data
        assert all(isinstance(v, int) for v in data.values())


class TestUserEndpoints:
    """Test user management endpoints."""
    
    def test_create_user(self, api_client, test_user_data):
        """Test creating a new user."""
        response = api_client.post("/api/v1/users", json_data=test_user_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"]
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
        
        return data  # Return for use in other tests
    
    def test_get_user(self, api_client, test_user_data):
        """Test getting user by ID."""
        # First create a user
        create_response = api_client.post("/api/v1/users", json_data=test_user_data)
        assert create_response.status_code == 201
        user_id = create_response.json()["id"]
        
        # Then retrieve it
        response = api_client.get(f"/api/v1/users/{user_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == user_id
        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"]
    
    def test_get_user_not_found(self, api_client):
        """Test getting non-existent user returns 404."""
        response = api_client.get("/api/v1/users/99999")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_update_user(self, api_client, test_user_data):
        """Test updating user information."""
        # Create user first
        create_response = api_client.post("/api/v1/users", json_data=test_user_data)
        user_id = create_response.json()["id"]
        
        # Update user
        update_data = {
            "username": f"updated_{test_user_data['username']}",
            "email": f"updated_{test_user_data['email']}"
        }
        response = api_client.put(f"/api/v1/users/{user_id}", json_data=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["username"] == update_data["username"]
        assert data["email"] == update_data["email"]
        assert "updated_at" in data
    
    def test_update_user_preferences(self, api_client, test_user_data):
        """Test updating user preferences."""
        # Create user first
        create_response = api_client.post("/api/v1/users", json_data=test_user_data)
        user_id = create_response.json()["id"]
        
        # Update preferences
        new_preferences = {
            "preferences": {
                "theme": "light",
                "lang": "es",
                "new_setting": "value"
            }
        }
        response = api_client.put(f"/api/v1/users/{user_id}/preferences", json_data=new_preferences)
        assert response.status_code == 200
        
        data = response.json()
        # Should merge with existing preferences
        assert data["preferences"]["theme"] == "light"
        assert data["preferences"]["notifications"] is True  # Preserved
        assert data["preferences"]["lang"] == "es"
        assert data["preferences"]["new_setting"] == "value"
    
    def test_search_users(self, api_client, test_user_data):
        """Test searching users."""
        # Create a user first
        api_client.post("/api/v1/users", json_data=test_user_data)
        
        # Search for users
        search_params = {
            "active_only": True,
            "limit": 10
        }
        response = api_client.get("/api/v1/users/search", params=search_params)
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)
    
    def test_get_user_statistics(self, api_client, test_user_data):
        """Test getting user statistics."""
        # Create user first
        create_response = api_client.post("/api/v1/users", json_data=test_user_data)
        user_id = create_response.json()["id"]
        
        response = api_client.get(f"/api/v1/users/{user_id}/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_interactions" in data
        assert "content_created" in data
        assert "avg_rating_given" in data
        assert isinstance(data["total_interactions"], int)
        assert isinstance(data["content_created"], int)


class TestContentEndpoints:
    """Test content management endpoints."""
    
    def test_create_content(self, api_client, test_user_data, test_content_data):
        """Test creating new content."""
        # Create user first
        user_response = api_client.post("/api/v1/users", json_data=test_user_data)
        user_id = user_response.json()["id"]
        
        # Update content data with real user ID
        test_content_data["creator_id"] = user_id
        
        response = api_client.post("/api/v1/content", json_data=test_content_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["title"] == test_content_data["title"]
        assert data["content_type"] == test_content_data["content_type"]
        assert data["creator_id"] == user_id
        assert "id" in data
        assert "created_at" in data
        
        return data
    
    def test_get_content(self, api_client, test_user_data, test_content_data):
        """Test getting content by ID."""
        # Create user and content first
        user_response = api_client.post("/api/v1/users", json_data=test_user_data)
        user_id = user_response.json()["id"]
        test_content_data["creator_id"] = user_id
        
        create_response = api_client.post("/api/v1/content", json_data=test_content_data)
        content_id = create_response.json()["id"]
        
        # Get content
        response = api_client.get(f"/api/v1/content/{content_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == content_id
        assert data["title"] == test_content_data["title"]
    
    def test_list_content(self, api_client):
        """Test listing content with pagination."""
        params = {
            "skip": 0,
            "limit": 10,
            "public_only": True
        }
        response = api_client.get("/api/v1/content", params=params)
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)
    
    @pytest.mark.skip(
        reason="Content search functionality not yet implemented - TODO: Implement search service and endpoint")
    def test_search_content(self, api_client):
        """Test content search functionality."""
        search_data = {
            "search_term": "test",
            "public_only": True,
            "limit": 5
        }
        response = api_client.post("/api/v1/content/search", json_data=search_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
    
    def test_update_content_quality(self, api_client, test_user_data, test_content_data):
        """Test updating content quality score."""
        # Create user and content first
        user_response = api_client.post("/api/v1/users", json_data=test_user_data)
        user_id = user_response.json()["id"]
        test_content_data["creator_id"] = user_id
        
        create_response = api_client.post("/api/v1/content", json_data=test_content_data)
        content_id = create_response.json()["id"]
        
        # Update quality score
        quality_data = {"quality_score": 0.85}
        response = api_client.put(f"/api/v1/content/{content_id}/quality", json_data=quality_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["quality_score"] == 0.85


class TestInteractionEndpoints:
    """Test interaction tracking endpoints."""
    
    def test_record_interaction(self, api_client, test_user_data, test_content_data):
        """Test recording a user interaction."""
        # Create user and content first
        user_response = api_client.post("/api/v1/users", json_data=test_user_data)
        user_id = user_response.json()["id"]
        test_content_data["creator_id"] = user_id
        
        content_response = api_client.post("/api/v1/content", json_data=test_content_data)
        content_id = content_response.json()["id"]
        
        # Record interaction
        interaction_data = {
            "user_id": user_id,
            "content_item_id": content_id,
            "interaction_type": "like",
            "rating": 5,
            "duration": 120,
            "metadata": {"source": "api_test"}
        }
        
        response = api_client.post("/api/v1/interactions", json_data=interaction_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["user_id"] == user_id
        assert data["content_item_id"] == content_id
        assert data["interaction_type"] == "like"
        assert data["rating"] == 5
        assert "id" in data
        assert "created_at" in data
    
    def test_get_user_interactions(self, api_client, test_user_data):
        """Test getting interactions for a user."""
        # Create user first
        user_response = api_client.post("/api/v1/users", json_data=test_user_data)
        user_id = user_response.json()["id"]
        
        # Get user interactions
        response = api_client.get(f"/api/v1/users/{user_id}/interactions")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
    
    def test_get_interaction_analytics(self, api_client, test_user_data):
        """Test getting interaction analytics."""
        # Create user first
        user_response = api_client.post("/api/v1/users", json_data=test_user_data)
        user_id = user_response.json()["id"]
        
        response = api_client.get(f"/api/v1/interactions/analytics/user-behavior/{user_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_interactions" in data
        assert "interaction_types" in data
        assert "favorite_content_types" in data


class TestRecommendationEndpoints:
    """Test recommendation endpoints."""
    
    def test_create_recommendation(self, api_client, test_user_data, test_content_data):
        """Test creating a recommendation."""
        # Create user and content first
        user_response = api_client.post("/api/v1/users", json_data=test_user_data)
        user_id = user_response.json()["id"]
        test_content_data["creator_id"] = user_id
        
        content_response = api_client.post("/api/v1/content", json_data=test_content_data)
        content_id = content_response.json()["id"]
        
        # Create recommendation
        rec_data = {
            "user_id": user_id,
            "content_item_id": content_id,
            "recommendation_score": 0.85,
            "algorithm_version": "test_v1.0",
            "metadata": {"test": "recommendation"}
        }
        
        response = api_client.post("/api/v1/recommendations", json_data=rec_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["user_id"] == user_id
        assert data["content_item_id"] == content_id
        assert data["recommendation_score"] == 0.85
        assert data["algorithm_version"] == "test_v1.0"
    
    def test_get_user_recommendations(self, api_client, test_user_data):
        """Test getting recommendations for a user."""
        # Create user first
        user_response = api_client.post("/api/v1/users", json_data=test_user_data)
        user_id = user_response.json()["id"]
        
        response = api_client.get(f"/api/v1/recommendations/user/{user_id}/recommendations")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
    
    def test_generate_recommendations(self, api_client, test_user_data):
        """Test generating recommendations for a user."""
        # Create user first
        user_response = api_client.post("/api/v1/users", json_data=test_user_data)
        user_id = user_response.json()["id"]
        
        gen_data = {
            "user_id": user_id,
            "algorithm_version": "test_v1.0",
            "limit": 5
        }
        
        response = api_client.post("/api/v1/recommendations/generate", json_data=gen_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "recommendations" in data
        assert "algorithm_version" in data
        assert isinstance(data["recommendations"], list)


class TestGenerationJobEndpoints:
    """Test generation job endpoints."""
    
    def test_create_generation_job(self, api_client, test_user_data):
        """Test creating a generation job."""
        # Create user first
        user_response = api_client.post("/api/v1/users", json_data=test_user_data)
        user_id = user_response.json()["id"]
        
        job_data = {
            "user_id": user_id,
            "job_type": "text_generation",
            "prompt": "Generate a test story about API testing",
            "parameters": {
                "max_length": 1000,
                "temperature": 0.7,
                "model": "test_model"
            }
        }
        
        response = api_client.post("/api/v1/generation-jobs", json_data=job_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["user_id"] == user_id
        assert data["job_type"] == "text_generation"
        assert data["prompt"] == job_data["prompt"]
        assert data["status"] == "pending"
        assert "id" in data
        assert "created_at" in data
    
    def test_get_generation_job(self, api_client, test_user_data):
        """Test getting generation job by ID."""
        # Create user and job first
        user_response = api_client.post("/api/v1/users", json_data=test_user_data)
        user_id = user_response.json()["id"]
        
        job_data = {
            "user_id": user_id,
            "job_type": "text_generation",
            "prompt": "Test prompt"
        }
        
        create_response = api_client.post("/api/v1/generation-jobs", json_data=job_data)
        job_id = create_response.json()["id"]
        
        # Get job
        response = api_client.get(f"/api/v1/generation-jobs/{job_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == job_id
        assert data["user_id"] == user_id
    
    # TODO: Re-enable after generation feature implementation
    @pytest.mark.skip(reason="Generation feature not yet implemented - pending generation job listing functionality")
    def test_list_generation_jobs(self, api_client):
        """Test listing generation jobs."""
        params = {
            "status": "pending",
            "limit": 10
        }
        response = api_client.get("/api/v1/generation-jobs", params=params)
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
    
    def test_update_job_status(self, api_client, test_user_data):
        """Test updating generation job status."""
        # Create user and job first
        user_response = api_client.post("/api/v1/users", json_data=test_user_data)
        user_id = user_response.json()["id"]
        
        job_data = {
            "user_id": user_id,
            "job_type": "text_generation",
            "prompt": "Test prompt"
        }
        
        create_response = api_client.post("/api/v1/generation-jobs", json_data=job_data)
        job_id = create_response.json()["id"]
        
        # Update status
        status_data = {
            "status": "running"
        }
        response = api_client.put(f"/api/v1/generation-jobs/{job_id}/status", json_data=status_data)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "running"
        assert "updated_at" in data

    def test_cancel_generation_job(self, api_client, test_user_data):
        """Test cancelling a generation job."""
        # Create user first
        user_response = api_client.post("/api/v1/users", json_data=test_user_data)
        user_id = user_response.json()["id"]

        # First create a generation job
        job_data = {
            "user_id": user_id,
            "job_type": "text_generation",
            "prompt": "Test prompt for cancellation",
            "parameters": {
                "max_length": 100,
                "temperature": 0.7
            }
        }

        create_response = api_client.post("/api/v1/generation-jobs", json_data=job_data)
        assert create_response.status_code == 201
        job_id = create_response.json()["id"]

        # Cancel the job with a reason
        cancel_data = {
            "reason": "User requested cancellation"
        }
        response = api_client.post(f"/api/v1/generation-jobs/{job_id}/cancel", json_data=cancel_data)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "cancelled"
        assert data["error_message"] == "Cancelled: User requested cancellation"
        assert "completed_at" in data

    def test_cancel_generation_job_without_reason(self, api_client, test_user_data):
        """Test cancelling a generation job without providing a reason."""
        # Create user first
        user_response = api_client.post("/api/v1/users", json_data=test_user_data)
        user_id = user_response.json()["id"]

        # First create a generation job
        job_data = {
            "user_id": user_id,
            "job_type": "text_generation",
            "prompt": "Test prompt for cancellation",
            "parameters": {}
        }

        create_response = api_client.post("/api/v1/generation-jobs", json_data=job_data)
        assert create_response.status_code == 201
        job_id = create_response.json()["id"]

        # Cancel the job without a reason
        response = api_client.post(f"/api/v1/generation-jobs/{job_id}/cancel", json_data={})
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "cancelled"
        assert data["error_message"] is None
        assert "completed_at" in data

    def test_cancel_nonexistent_job(self, api_client):
        """Test cancelling a non-existent job."""
        response = api_client.post("/api/v1/generation-jobs/999999/cancel", json_data={})
        assert response.status_code == 404

    def test_cancel_completed_job(self, api_client, test_user_data):
        """Test that cancelling a completed job fails."""
        # Create user first
        user_response = api_client.post("/api/v1/users", json_data=test_user_data)
        user_id = user_response.json()["id"]

        # First create a generation job
        job_data = {
            "user_id": user_id,
            "job_type": "text_generation",
            "prompt": "Test prompt",
            "parameters": {}
        }

        create_response = api_client.post("/api/v1/generation-jobs", json_data=job_data)
        assert create_response.status_code == 201
        job_id = create_response.json()["id"]

        # Mark it as completed
        status_data = {"status": "completed"}
        status_response = api_client.put(f"/api/v1/generation-jobs/{job_id}/status", json_data=status_data)
        assert status_response.status_code == 200

        # Try to cancel it - should fail
        response = api_client.post(f"/api/v1/generation-jobs/{job_id}/cancel", json_data={})
        assert response.status_code == 422
        assert "Cannot cancel job with status 'completed'" in response.json()["detail"]


class TestErrorHandling:
    """Test API error handling."""
    
    def test_invalid_json_request(self, api_client):
        """Test API response to invalid JSON."""
        # Send invalid JSON to user creation endpoint
        response = requests.post(
            f"{TEST_API_BASE_URL}/api/v1/users",
            data="invalid json",
            headers={"Content-Type": "application/json"},
            timeout=TEST_TIMEOUT
        )
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_missing_required_fields(self, api_client):
        """Test API response to missing required fields."""
        # Send user creation request without required fields
        incomplete_data = {"username": "test"}  # Missing email
        response = api_client.post("/api/v1/users", json_data=incomplete_data)
        assert response.status_code == 422
        
        data = response.json()
        assert "detail" in data
    
    def test_invalid_endpoint(self, api_client):
        """Test API response to invalid endpoint."""
        response = api_client.get("/api/v1/nonexistent")
        assert response.status_code == 404
    
    def test_validation_errors(self, api_client):
        """Test API validation error responses."""
        # Test with invalid email
        invalid_user_data = {
            "username": "testuser",
            "email": "invalid-email-format"
        }
        response = api_client.post("/api/v1/users", json_data=invalid_user_data)
        assert response.status_code == 422
        
        data = response.json()
        assert "detail" in data
