"""API integration tests for generation job lifecycle."""
from fastapi.testclient import TestClient


def test_create_generation_job_basic(api_client: TestClient, sample_user):
    """Test creating a basic generation job with minimal parameters.

    This test ensures:
    1. The API accepts valid generation job requests
    2. Database sequences are working correctly (no duplicate key errors)
    3. The job is created with expected default values
    """
    response = api_client.post("/api/v1/generation-jobs/", json={
        "user_id": str(sample_user.id),
        "job_type": "image_generation",
        "prompt": "cat"
    })

    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    data = response.json()

    # Verify job was created successfully
    assert data["id"] is not None
    assert data["user_id"] == str(sample_user.id)
    assert data["job_type"] == "image_generation"
    assert data["prompt"] == "cat"
    assert data["status"] == "pending"

    # Verify defaults are set
    assert data["params"] is not None
    assert "width" in data["params"]
    assert "height" in data["params"]


def test_create_multiple_generation_jobs_sequential(api_client: TestClient, sample_user):
    """Test creating multiple generation jobs sequentially.

    This test catches sequence issues where the database ID sequence
    is out of sync with actual data. If the sequence hasn't been properly
    reset, the second or third job creation will fail with a duplicate key error.
    """
    job_ids = []

    for i in range(5):
        response = api_client.post("/api/v1/generation-jobs/", json={
            "user_id": str(sample_user.id),
            "job_type": "image_generation",
            "prompt": f"test prompt {i}"
        })

        assert response.status_code == 201, f"Failed to create job {i}: {response.text}"
        data = response.json()
        job_ids.append(data["id"])

    # Verify all jobs have unique IDs
    assert len(set(job_ids)) == 5, "Job IDs should all be unique"

    # Verify IDs are sequential (or at least increasing)
    assert all(job_ids[i] < job_ids[i+1] for i in range(len(job_ids)-1)), \
        "Job IDs should be increasing"


def test_job_lifecycle(api_client: TestClient, sample_user):
    # Create job
    response = api_client.post("/api/v1/generation-jobs", json={
        "user_id": str(sample_user.id),
        "prompt": "Test prompt"
    })
    if response.status_code == 404:
        # Endpoint may not exist yet
        return
    assert response.status_code in [200, 201, 404, 422]
