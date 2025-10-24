"""Integration tests for generation analytics API endpoints.

These tests verify the generation analytics REST API endpoints work correctly
and return properly formatted data.
"""

import uuid
from datetime import datetime, timedelta
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import text

from genonaut.api.main import app
from test.db.postgres_fixtures import postgres_session


@pytest.fixture()
def client():
    """Create FastAPI test client."""
    return TestClient(app)


@pytest.fixture()
def db_session(postgres_session) -> Generator[Session, None, None]:
    """Yield a PostgreSQL session for API tests."""
    yield postgres_session


@pytest.fixture()
def sample_generation_data(db_session):
    """Insert sample generation events for testing."""
    user_id = str(uuid.uuid4())
    ref_time = datetime.utcnow().replace(minute=0, second=0, microsecond=0)

    # Insert multiple events with varying characteristics
    events = [
        # Successful generations
        {
            'event_type': 'request',
            'generation_id': str(uuid.uuid4()),
            'user_id': user_id,
            'timestamp': ref_time,
            'generation_type': 'standard',
        },
        {
            'event_type': 'completion',
            'generation_id': str(uuid.uuid4()),
            'user_id': user_id,
            'timestamp': ref_time,
            'duration_ms': 3500,
            'success': True,
            'model_checkpoint': 'sd_xl_base_1.0.safetensors',
        },
        # Failed generation
        {
            'event_type': 'completion',
            'generation_id': str(uuid.uuid4()),
            'user_id': user_id,
            'timestamp': ref_time,
            'duration_ms': 15000,
            'success': False,
            'error_type': 'timeout',
            'error_message': 'ComfyUI request timeout',
        },
    ]

    for event in events:
        cols = ', '.join(event.keys())
        placeholders = ', '.join([f':{k}' for k in event.keys()])
        db_session.execute(
            text(f"""
                INSERT INTO generation_events ({cols}, created_at)
                VALUES ({placeholders}, NOW())
            """),
            event
        )

    # Also insert hourly metrics for some tests
    db_session.execute(text("""
        INSERT INTO generation_metrics_hourly (
            timestamp,
            total_requests,
            successful_generations,
            failed_generations,
            cancelled_generations,
            avg_duration_ms,
            p50_duration_ms,
            p95_duration_ms,
            p99_duration_ms,
            unique_users,
            avg_queue_length,
            max_queue_length,
            total_images_generated,
            created_at
        ) VALUES (
            :timestamp,
            10,
            9,
            1,
            0,
            3500,
            3200,
            5500,
            7200,
            5,
            2.5,
            8,
            9,
            NOW()
        )
    """), {'timestamp': ref_time})

    db_session.commit()

    yield {
        'user_id': user_id,
        'ref_time': ref_time
    }

    # Cleanup
    db_session.execute(text("DELETE FROM generation_events"))
    db_session.execute(text("DELETE FROM generation_metrics_hourly"))
    db_session.commit()


class TestGenerationAnalyticsEndpoints:
    """Test generation analytics API endpoints."""

    def test_get_generation_overview(self, client, sample_generation_data):
        """Test GET /api/v1/analytics/generation/overview endpoint."""
        response = client.get("/api/v1/analytics/generation/overview?days=7")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert 'lookback_days' in data
        assert 'total_requests' in data
        assert 'successful_generations' in data
        assert 'failed_generations' in data
        assert 'cancelled_generations' in data
        assert 'success_rate_pct' in data
        assert 'avg_duration_ms' in data
        assert 'p95_duration_ms' in data

        # Verify data types
        assert isinstance(data['total_requests'], int)
        assert isinstance(data['success_rate_pct'], (int, float))

    def test_get_generation_overview_with_custom_days(self, client, sample_generation_data):
        """Test overview endpoint with custom days parameter."""
        response = client.get("/api/v1/analytics/generation/overview?days=30")

        assert response.status_code == 200
        data = response.json()
        assert data['lookback_days'] == 30

    def test_get_generation_trends_hourly(self, client, sample_generation_data):
        """Test GET /api/v1/analytics/generation/trends with hourly interval."""
        response = client.get(
            "/api/v1/analytics/generation/trends?days=7&interval=hourly"
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data['interval'] == 'hourly'
        assert data['lookback_days'] == 7
        assert 'total_data_points' in data
        assert 'data_points' in data
        assert isinstance(data['data_points'], list)

        # Verify data point structure if any exist
        if data['data_points']:
            point = data['data_points'][0]
            assert 'timestamp' in point
            assert 'total_requests' in point
            assert 'successful_generations' in point
            assert 'failed_generations' in point
            assert 'avg_duration_ms' in point
            assert 'p95_duration_ms' in point
            assert 'success_rate' in point

    def test_get_generation_trends_daily(self, client, sample_generation_data):
        """Test GET /api/v1/analytics/generation/trends with daily interval."""
        response = client.get(
            "/api/v1/analytics/generation/trends?days=30&interval=daily"
        )

        assert response.status_code == 200
        data = response.json()

        assert data['interval'] == 'daily'
        assert data['lookback_days'] == 30

    def test_get_user_generation_analytics(self, client, sample_generation_data):
        """Test GET /api/v1/analytics/generation/users/{user_id} endpoint."""
        user_id = sample_generation_data['user_id']

        response = client.get(
            f"/api/v1/analytics/generation/users/{user_id}?days=30"
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data['user_id'] == user_id
        assert data['lookback_days'] == 30
        assert 'total_requests' in data
        assert 'successful_generations' in data
        assert 'failed_generations' in data
        assert 'success_rate_pct' in data
        assert 'avg_duration_ms' in data
        assert 'recent_activity' in data
        assert 'failure_breakdown' in data

        # Verify recent activity is a list
        assert isinstance(data['recent_activity'], list)

        # Verify failure breakdown is a list
        assert isinstance(data['failure_breakdown'], list)

    def test_get_user_generation_analytics_nonexistent_user(self, client):
        """Test user analytics with non-existent user returns empty results."""
        nonexistent_user_id = str(uuid.uuid4())

        response = client.get(
            f"/api/v1/analytics/generation/users/{nonexistent_user_id}?days=30"
        )

        assert response.status_code == 200
        data = response.json()

        # Should return zero results for non-existent user
        assert data['total_requests'] == 0
        assert data['successful_generations'] == 0

    def test_get_model_performance(self, client, sample_generation_data):
        """Test GET /api/v1/analytics/generation/models endpoint."""
        response = client.get("/api/v1/analytics/generation/models?days=30")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert 'lookback_days' in data
        assert 'total_models' in data
        assert 'models' in data
        assert isinstance(data['models'], list)

        # Verify model structure if any exist
        if data['models']:
            model = data['models'][0]
            assert 'model_checkpoint' in model
            assert 'total_generations' in model
            assert 'successful_generations' in model
            assert 'failed_generations' in model
            assert 'success_rate_pct' in model
            assert 'avg_duration_ms' in model
            assert 'p50_duration_ms' in model
            assert 'p95_duration_ms' in model

    def test_get_failure_analysis(self, client, sample_generation_data):
        """Test GET /api/v1/analytics/generation/failures endpoint."""
        response = client.get("/api/v1/analytics/generation/failures?days=7")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert 'lookback_days' in data
        assert 'total_error_types' in data
        assert 'error_types' in data
        assert 'failure_trends' in data

        assert isinstance(data['error_types'], list)
        assert isinstance(data['failure_trends'], list)

        # Verify error type structure if any exist
        if data['error_types']:
            error = data['error_types'][0]
            assert 'error_type' in error
            assert 'count' in error
            assert 'avg_duration_ms' in error or error['avg_duration_ms'] is None
            assert 'sample_messages' in error

    def test_get_peak_usage_times(self, client, sample_generation_data):
        """Test GET /api/v1/analytics/generation/peak-hours endpoint."""
        response = client.get("/api/v1/analytics/generation/peak-hours?days=30")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert 'lookback_days' in data
        assert 'total_hours_analyzed' in data
        assert 'peak_hours' in data
        assert isinstance(data['peak_hours'], list)

        # Verify peak hour structure if any exist
        if data['peak_hours']:
            hour = data['peak_hours'][0]
            assert 'hour_of_day' in hour
            assert 'avg_requests' in hour
            assert 'avg_queue_length' in hour or hour['avg_queue_length'] is None
            assert 'avg_p95_duration_ms' in hour or hour['avg_p95_duration_ms'] is None
            assert 'data_points' in hour

            # Hour should be 0-23
            assert 0 <= hour['hour_of_day'] <= 23

    def test_overview_invalid_days_parameter(self, client):
        """Test overview endpoint rejects invalid days parameter."""
        # Days too low
        response = client.get("/api/v1/analytics/generation/overview?days=0")
        assert response.status_code == 422  # Validation error

        # Days too high
        response = client.get("/api/v1/analytics/generation/overview?days=100")
        assert response.status_code == 422  # Validation error

    def test_trends_invalid_interval_parameter(self, client):
        """Test trends endpoint rejects invalid interval parameter."""
        response = client.get(
            "/api/v1/analytics/generation/trends?days=7&interval=weekly"
        )
        assert response.status_code == 422  # Validation error

    def test_user_analytics_invalid_user_id(self, client):
        """Test user analytics endpoint rejects invalid UUID."""
        response = client.get(
            "/api/v1/analytics/generation/users/not-a-uuid?days=30"
        )
        assert response.status_code == 422  # Validation error

    def test_all_endpoints_return_json(self, client, sample_generation_data):
        """Test that all endpoints return JSON content type."""
        endpoints = [
            "/api/v1/analytics/generation/overview?days=7",
            "/api/v1/analytics/generation/trends?days=7&interval=hourly",
            f"/api/v1/analytics/generation/users/{sample_generation_data['user_id']}?days=30",
            "/api/v1/analytics/generation/models?days=30",
            "/api/v1/analytics/generation/failures?days=7",
            "/api/v1/analytics/generation/peak-hours?days=30",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200
            assert 'application/json' in response.headers['content-type']

    def test_endpoints_handle_empty_database(self, client):
        """Test that endpoints handle empty database gracefully."""
        # Use a time period where no data exists
        endpoints = [
            "/api/v1/analytics/generation/overview?days=7",
            "/api/v1/analytics/generation/trends?days=7&interval=hourly",
            "/api/v1/analytics/generation/models?days=30",
            "/api/v1/analytics/generation/failures?days=7",
            "/api/v1/analytics/generation/peak-hours?days=30",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            # Should return 200 with zero/empty results, not crash
            assert response.status_code == 200
            data = response.json()
            # Different endpoints have different zero-state structures
            # but they should all return valid JSON

    def test_concurrent_requests(self, client, sample_generation_data):
        """Test that concurrent requests to analytics endpoints work correctly."""
        import concurrent.futures

        def make_request():
            response = client.get("/api/v1/analytics/generation/overview?days=7")
            return response.status_code

        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All requests should succeed
        assert all(status == 200 for status in results)
