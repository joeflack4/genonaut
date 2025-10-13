"""Integration tests for complete API workflows."""

import os
import pytest
import requests
from datetime import datetime
from typing import Dict, Any

from .config import TEST_API_BASE_URL, TEST_TIMEOUT


def make_request(method: str, endpoint: str, **kwargs) -> requests.Response:
    """Helper function to make API requests."""
    url = f"{TEST_API_BASE_URL}{endpoint}"
    return requests.request(method, url, timeout=TEST_TIMEOUT, **kwargs)


@pytest.mark.api_server
class TestCompleteUserWorkflow:
    """Test complete user lifecycle workflow."""
    
    def test_user_content_interaction_workflow(self):
        """Test complete workflow: create user -> create content -> interact -> recommend."""
        
        # Step 1: Create a user
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        user_data = {
            "username": f"workflow_user_{timestamp}",
            "email": f"workflow_user_{timestamp}@example.com",
            "preferences": {"theme": "dark", "test": True}
        }
        
        user_response = make_request("POST", "/api/v1/users", json=user_data)
        assert user_response.status_code == 201
        user = user_response.json()
        user_id = user["id"]
        
        # Step 2: Create content by this user
        content_data = {
            "title": f"Test Content by User {user_id}",
            "content_type": "text",
            "content_data": "This is test content for the workflow",
            "prompt": "Test prompt for workflow content",
            "creator_id": user_id,
            "item_metadata": {"workflow": "test", "creator": user["username"]},
            "is_private": False
        }

        content_response = make_request("POST", "/api/v1/content", json=content_data)
        assert content_response.status_code == 201
        content = content_response.json()
        content_id = content["id"]
        
        # Step 3: User interacts with their own content
        interaction_data = {
            "user_id": user_id,
            "content_item_id": content_id,
            "interaction_type": "view",
            "duration": 45,
            "metadata": {"workflow": "test", "self_interaction": True}
        }
        
        interaction_response = make_request("POST", "/api/v1/interactions", json=interaction_data)
        assert interaction_response.status_code == 201
        interaction = interaction_response.json()
        
        # Step 4: Check user statistics
        stats_response = make_request("GET", f"/api/v1/users/{user_id}/stats")
        assert stats_response.status_code == 200
        stats = stats_response.json()
        assert stats["total_interactions"] >= 1
        assert stats["content_created"] >= 1
        
        # Step 5: Generate recommendations for the user
        rec_gen_data = {
            "user_id": user_id,
            "algorithm_version": "workflow_test_v1.0",
            "limit": 5
        }
        
        rec_response = make_request("POST", "/api/v1/recommendations/generate", json=rec_gen_data)
        assert rec_response.status_code == 200
        recommendations = rec_response.json()
        assert "recommendations" in recommendations
        
        # Step 6: Get user's recommendations
        user_recs_response = make_request("GET", f"/api/v1/recommendations/user/{user_id}/recommendations")
        assert user_recs_response.status_code == 200
        user_recs = user_recs_response.json()
        assert "items" in user_recs
        
        # Step 7: Update user preferences
        new_preferences = {
            "preferences": {
                "theme": "light",
                "workflow_completed": True,
                "completion_time": datetime.now().isoformat()
            }
        }
        
        prefs_response = make_request("PUT", f"/api/v1/users/{user_id}/preferences", json=new_preferences)
        assert prefs_response.status_code == 200
        updated_user = prefs_response.json()
        assert updated_user["preferences"]["theme"] == "light"
        assert updated_user["preferences"]["workflow_completed"] is True
        
        print(f"✅ Complete workflow test passed for user {user_id}")


@pytest.mark.api_server
class TestContentGenerationWorkflow:
    """Test content generation workflow."""
    
    # TODO: Re-enable after generation feature implementation
    @pytest.mark.skip(reason="Generation feature not yet implemented - pending generation job lifecycle functionality")
    def test_generation_job_lifecycle(self):
        """Test complete generation job lifecycle."""
        
        # Step 1: Create a user
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        user_data = {
            "username": f"gen_user_{timestamp}",
            "email": f"gen_user_{timestamp}@example.com"
        }
        
        user_response = make_request("POST", "/api/v1/users", json=user_data)
        assert user_response.status_code == 201
        user_id = user_response.json()["id"]
        
        # Step 2: Create a generation job
        job_data = {
            "user_id": user_id,
            "job_type": "text_generation",
            "prompt": "Generate a short story about API testing and automation",
            "parameters": {
                "max_length": 500,
                "temperature": 0.7,
                "model": "test_model",
                "workflow": "integration_test"
            }
        }
        
        job_response = make_request("POST", "/api/v1/generation-jobs", json=job_data)
        assert job_response.status_code == 201
        job = job_response.json()
        job_id = job["id"]
        assert job["status"] == "pending"
        
        # Step 3: Check job status
        status_response = make_request("GET", f"/api/v1/generation-jobs/{job_id}")
        assert status_response.status_code == 200
        job_status = status_response.json()
        assert job_status["id"] == job_id
        
        # Step 4: Update job status to running (simulating job processing)
        status_update = {"status": "running"}
        update_response = make_request("PUT", f"/api/v1/generation-jobs/{job_id}/status", json=status_update)
        assert update_response.status_code == 200
        running_job = update_response.json()
        assert running_job["status"] == "running"
        
        # Step 5: Check queue statistics
        queue_response = make_request("GET", "/api/v1/generation-jobs/queue/stats")
        assert queue_response.status_code == 200
        queue_stats = queue_response.json()
        assert "pending_jobs" in queue_stats
        assert "running_jobs" in queue_stats
        assert queue_stats["running_jobs"] >= 1
        
        # Step 6: Get user's generation jobs
        user_jobs_response = make_request("GET", f"/api/v1/users/{user_id}/generation-jobs")
        assert user_jobs_response.status_code == 200
        user_jobs = user_jobs_response.json()
        assert "items" in user_jobs
        assert len(user_jobs["items"]) >= 1
        
        print(f"✅ Generation workflow test passed for job {job_id}")


@pytest.mark.api_server
class TestRecommendationWorkflow:
    """Test recommendation system workflow."""
    
    # TODO: Re-enable after generation feature implementation  
    @pytest.mark.skip(reason="Generation feature not yet implemented - pending recommendation workflow that depends on generation")
    def test_recommendation_system_workflow(self):
        """Test recommendation generation and serving workflow."""
        
        # Step 1: Create multiple users
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        users = []
        
        for i in range(2):
            user_data = {
                "username": f"rec_user_{i}_{timestamp}",
                "email": f"rec_user_{i}_{timestamp}@example.com",
                "preferences": {"category": f"category_{i}", "score": i * 0.5}
            }
            response = make_request("POST", "/api/v1/users", json=user_data)
            assert response.status_code == 201
            users.append(response.json())
        
        # Step 2: Create content items
        content_items = []
        for i, user in enumerate(users):
            content_data = {
                "title": f"Content {i} for Recommendations",
                "content_type": "text",
                "content_data": f"Content data for recommendation testing {i}",
                "creator_id": user["id"],
                "item_metadata": {"rec_test": True, "category": f"category_{i}"},
                "is_public": True
            }
            response = make_request("POST", "/api/v1/content", json=content_data)
            assert response.status_code == 201
            content_items.append(response.json())
        
        # Step 3: Create some interactions
        for i, user in enumerate(users):
            for j, content in enumerate(content_items):
                if i != j:  # Users interact with other users' content
                    interaction_data = {
                        "user_id": user["id"],
                        "content_item_id": content["id"],
                        "interaction_type": "like",
                        "rating": 4 + i,
                        "metadata": {"rec_test": True}
                    }
                    response = make_request("POST", "/api/v1/interactions", json=interaction_data)
                    assert response.status_code == 201
        
        # Step 4: Generate recommendations for first user
        rec_data = {
            "user_id": users[0]["id"],
            "algorithm_version": "workflow_test_v2.0",
            "limit": 10
        }
        
        gen_response = make_request("POST", "/api/v1/recommendations/generate", json=rec_data)
        assert gen_response.status_code == 200
        generated_recs = gen_response.json()
        assert "recommendations" in generated_recs
        
        # Step 5: Get unserved recommendations
        unserved_response = make_request("GET", f"/api/v1/recommendations/user/{users[0]['id']}/recommendations?unserved_only=true")
        assert unserved_response.status_code == 200
        unserved = unserved_response.json()
        assert "items" in unserved
        
        # Step 6: Mark recommendations as served (if any exist)
        if unserved["items"]:
            rec_ids = [rec["id"] for rec in unserved["items"][:3]]  # Mark first 3 as served
            served_data = {"recommendation_ids": rec_ids}
            
            served_response = make_request("POST", "/api/v1/recommendations/served", json=served_data)
            assert served_response.status_code == 200
        
        # Step 7: Get recommendation analytics
        analytics_response = make_request("GET", f"/api/v1/recommendations/analytics/user/{users[0]['id']}")
        assert analytics_response.status_code == 200
        analytics = analytics_response.json()
        assert "total_recommendations" in analytics
        
        print(f"✅ Recommendation workflow test passed for {len(users)} users and {len(content_items)} content items")


class TestAPIHealthAndMonitoring:
    """Test API health and monitoring endpoints."""
    
    def test_system_health_monitoring(self):
        """Test system health and monitoring endpoints."""
        
        # Test health check
        health_response = make_request("GET", "/api/v1/health")
        assert health_response.status_code == 200
        health = health_response.json()
        assert health["status"] == "healthy"
        assert "database" in health
        assert health["database"]["status"] == "connected"
        
        # Test database info
        db_response = make_request("GET", "/api/v1/databases")
        assert db_response.status_code == 200
        db_info = db_response.json()
        assert "current_database" in db_info
        assert "available_databases" in db_info
        
        # Test global statistics
        stats_response = make_request("GET", "/api/v1/stats/global")
        assert stats_response.status_code == 200
        stats = stats_response.json()
        
        required_stats = ["total_users", "total_content", "total_interactions", "total_recommendations"]
        for stat in required_stats:
            assert stat in stats
            assert isinstance(stats[stat], int)
            assert stats[stat] >= 0
        
        print("✅ System health and monitoring test passed")


class TestSearchAndFiltering:
    """Test search and filtering capabilities."""
    
    @pytest.mark.skip(reason="Comprehensive search functionality not yet implemented - TODO: Implement after basic search")
    def test_comprehensive_search_workflow(self):
        """Test search functionality across different endpoints."""
        
        # Step 1: Create test data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create user
        user_data = {
            "username": f"search_user_{timestamp}",
            "email": f"search_user_{timestamp}@example.com",
            "preferences": {"search_test": True}
        }
        user_response = make_request("POST", "/api/v1/users", json=user_data)
        assert user_response.status_code == 201
        user_id = user_response.json()["id"]
        
        # Create searchable content
        content_data = {
            "title": f"Searchable Content {timestamp}",
            "content_type": "text",
            "content_data": "This content contains searchable keywords for testing",
            "prompt": "Test prompt for workflow content",
            "creator_id": user_id,
            "item_metadata": {"searchable": True, "keywords": ["search", "test", "api"]},
            "is_public": True
        }
        content_response = make_request("POST", "/api/v1/content", json=content_data)
        assert content_response.status_code == 201
        content_id = content_response.json()["id"]
        
        # Step 2: Test content search
        search_data = {
            "search_term": "Searchable",
            "content_type": "text",
            "public_only": True,
            "limit": 10
        }
        search_response = make_request("POST", "/api/v1/content/search", json=search_data)
        assert search_response.status_code == 200
        search_results = search_response.json()
        assert "items" in search_results
        
        # Verify our content appears in search results
        content_ids = [item["id"] for item in search_results["items"]]
        assert content_id in content_ids
        
        # Step 3: Test user search
        user_search_data = {
            "active_only": True,
            "limit": 10
        }
        user_search_response = make_request("POST", "/api/v1/users/search", json=user_search_data)
        assert user_search_response.status_code == 200
        user_search_results = user_search_response.json()
        assert "items" in user_search_results
        
        # Step 4: Test filtering by tags would go here if implemented

        print(f"✅ Search and filtering workflow test passed")


# Helper function to run a quick smoke test
def run_smoke_test():
    """Run a quick smoke test to verify API is responding."""
    try:
        response = make_request("GET", "/api/v1/health")
        if response.status_code == 200:
            print("✅ API smoke test passed - server is responding")
            return True
        else:
            print(f"❌ API smoke test failed - status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API smoke test failed - error: {e}")
        return False


if __name__ == "__main__":
    """Run basic smoke test when executed directly."""
    print(f"Testing API at: {TEST_API_BASE_URL}")
    run_smoke_test()
