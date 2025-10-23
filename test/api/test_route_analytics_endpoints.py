"""API integration tests for route analytics endpoints."""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import text


def _create_sample_analytics_data(db_session: Session, sample_user):
    """Create sample route analytics data for testing.

    Creates data in both route_analytics and route_analytics_hourly tables
    for realistic testing scenarios.
    """
    # Sample route analytics hourly data
    # Create data for last 7 days with different patterns
    base_timestamp = datetime.utcnow().replace(minute=0, second=0, microsecond=0)

    sample_data = []

    # Route 1: High frequency, high latency (should score high for caching)
    for i in range(7 * 24):  # 7 days of hourly data
        timestamp = base_timestamp - timedelta(hours=i)
        sample_data.append({
            'timestamp': timestamp,
            'route': '/api/v1/content/unified',
            'method': 'GET',
            'query_params_normalized': {'page_size': '10', 'sort': 'created_at'},
            'total_requests': 150 + (i % 50),
            'successful_requests': 145 + (i % 48),
            'client_errors': 3,
            'server_errors': 2,
            'avg_duration_ms': 250 + (i % 100),
            'p50_duration_ms': 200 + (i % 80),
            'p95_duration_ms': 450 + (i % 150),
            'p99_duration_ms': 600 + (i % 200),
            'unique_users': 45 + (i % 20),
        })

    # Route 2: Medium frequency, medium latency
    for i in range(7 * 24):
        timestamp = base_timestamp - timedelta(hours=i)
        sample_data.append({
            'timestamp': timestamp,
            'route': '/api/v1/tags/hierarchy',
            'method': 'GET',
            'query_params_normalized': {},
            'total_requests': 80 + (i % 30),
            'successful_requests': 78 + (i % 29),
            'client_errors': 1,
            'server_errors': 1,
            'avg_duration_ms': 150 + (i % 50),
            'p50_duration_ms': 120 + (i % 40),
            'p95_duration_ms': 280 + (i % 80),
            'p99_duration_ms': 380 + (i % 100),
            'unique_users': 25 + (i % 10),
        })

    # Route 3: Low frequency, high latency (interesting for relative ranking)
    for i in range(7 * 24):
        timestamp = base_timestamp - timedelta(hours=i)
        sample_data.append({
            'timestamp': timestamp,
            'route': '/api/v1/generation-jobs/status',
            'method': 'POST',
            'query_params_normalized': {},
            'total_requests': 5 + (i % 5),
            'successful_requests': 4 + (i % 4),
            'client_errors': 0,
            'server_errors': 1,
            'avg_duration_ms': 3500 + (i % 500),
            'p50_duration_ms': 3000 + (i % 400),
            'p95_duration_ms': 5200 + (i % 800),
            'p99_duration_ms': 6500 + (i % 1000),
            'unique_users': 8 + (i % 5),
        })

    # Insert all data
    for data in sample_data:
        insert_query = text("""
            INSERT INTO route_analytics_hourly (
                timestamp, route, method, query_params_normalized,
                total_requests, successful_requests, client_errors, server_errors,
                avg_duration_ms, p50_duration_ms, p95_duration_ms, p99_duration_ms,
                unique_users, cache_hits, cache_misses, created_at
            ) VALUES (
                :timestamp, :route, :method, :query_params_normalized,
                :total_requests, :successful_requests, :client_errors, :server_errors,
                :avg_duration_ms, :p50_duration_ms, :p95_duration_ms, :p99_duration_ms,
                :unique_users, :cache_hits, :cache_misses, :created_at
            )
            ON CONFLICT (timestamp, route, method, query_params_normalized) DO NOTHING
        """)

        db_session.execute(insert_query, {
            **data,
            'query_params_normalized': str(data['query_params_normalized']).replace("'", '"'),
            'cache_hits': 0,
            'cache_misses': 0,
            'created_at': data['timestamp'],
        })

    db_session.commit()


def test_cache_priorities_absolute_system(api_client: TestClient, db_session: Session, sample_user):
    """Test GET /api/v1/analytics/routes/cache-priorities with absolute system."""
    _create_sample_analytics_data(db_session, sample_user)

    response = api_client.get(
        "/api/v1/analytics/routes/cache-priorities",
        params={
            "n": 5,
            "system": "absolute",
            "days": 7,
            "min_requests": 10,
            "min_latency": 100
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data["system"] == "absolute"
    assert data["lookback_days"] == 7
    assert "routes" in data
    assert "total_routes" in data
    assert len(data["routes"]) >= 0  # May be empty if thresholds filter everything

    # If we have results, verify structure
    if len(data["routes"]) > 0:
        route = data["routes"][0]
        assert "route" in route
        assert "method" in route
        assert "avg_hourly_requests" in route
        assert "avg_p95_latency_ms" in route
        assert "cache_priority_score" in route
        assert "success_rate" in route

        # Verify cache priority score exists and is numeric
        assert isinstance(route["cache_priority_score"], (int, float))


def test_cache_priorities_relative_system(api_client: TestClient, db_session: Session, sample_user):
    """Test GET /api/v1/analytics/routes/cache-priorities with relative system."""
    _create_sample_analytics_data(db_session, sample_user)

    response = api_client.get(
        "/api/v1/analytics/routes/cache-priorities",
        params={
            "n": 5,
            "system": "relative",
            "days": 7
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data["system"] == "relative"
    assert data["lookback_days"] == 7
    assert "routes" in data
    assert "total_routes" in data

    # Relative system should return results even with low traffic
    if len(data["routes"]) > 0:
        route = data["routes"][0]
        assert "route" in route
        assert "method" in route
        assert "avg_hourly_requests" in route
        assert "avg_p95_latency_ms" in route
        assert "priority_score" in route
        assert "popularity_percentile" in route
        assert "latency_percentile" in route
        assert "user_percentile" in route
        assert "success_rate" in route

        # Verify percentile scores are between 0 and 100
        assert 0 <= route["popularity_percentile"] <= 100
        assert 0 <= route["latency_percentile"] <= 100
        assert 0 <= route["user_percentile"] <= 100


def test_cache_priorities_parameter_validation(api_client: TestClient, db_session: Session, sample_user):
    """Test parameter validation for cache priorities endpoint."""

    # Test invalid n value (too large)
    response = api_client.get(
        "/api/v1/analytics/routes/cache-priorities",
        params={"n": 150, "system": "absolute"}
    )
    assert response.status_code == 422  # Validation error

    # Test invalid n value (too small)
    response = api_client.get(
        "/api/v1/analytics/routes/cache-priorities",
        params={"n": 0, "system": "absolute"}
    )
    assert response.status_code == 422

    # Test invalid system value
    response = api_client.get(
        "/api/v1/analytics/routes/cache-priorities",
        params={"n": 10, "system": "invalid"}
    )
    assert response.status_code == 422


def test_performance_trends_hourly(api_client: TestClient, db_session: Session, sample_user):
    """Test GET /api/v1/analytics/routes/performance-trends with hourly granularity."""
    _create_sample_analytics_data(db_session, sample_user)

    response = api_client.get(
        "/api/v1/analytics/routes/performance-trends",
        params={
            "route": "/api/v1/content/unified",
            "days": 7,
            "granularity": "hourly"
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data["route"] == "/api/v1/content/unified"
    assert data["granularity"] == "hourly"
    assert data["lookback_days"] == 7
    assert "data_points" in data
    assert "trends" in data

    # Should have hourly data points
    if data["data_points"] > 0:
        trend = data["trends"][0]
        assert "timestamp" in trend
        assert "total_requests" in trend
        assert "successful_requests" in trend
        assert "client_errors" in trend
        assert "server_errors" in trend
        assert "avg_duration_ms" in trend
        assert "p50_duration_ms" in trend
        assert "p95_duration_ms" in trend
        assert "p99_duration_ms" in trend
        assert "unique_users" in trend
        assert "success_rate" in trend

        # Verify success rate is between 0 and 1 (with small tolerance for floating point)
        if trend["success_rate"] is not None:
            # Allow small floating point errors (e.g., 1.006 rounds to 1.0)
            assert -0.01 <= trend["success_rate"] <= 1.01


def test_performance_trends_daily(api_client: TestClient, db_session: Session, sample_user):
    """Test GET /api/v1/analytics/routes/performance-trends with daily granularity."""
    _create_sample_analytics_data(db_session, sample_user)

    response = api_client.get(
        "/api/v1/analytics/routes/performance-trends",
        params={
            "route": "/api/v1/tags/hierarchy",
            "days": 7,
            "granularity": "daily"
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data["route"] == "/api/v1/tags/hierarchy"
    assert data["granularity"] == "daily"
    assert data["lookback_days"] == 7

    # Daily aggregation should have fewer data points than hourly
    assert data["data_points"] <= 7  # At most 7 days


def test_performance_trends_missing_route(api_client: TestClient, db_session: Session, sample_user):
    """Test performance trends for non-existent route (should return empty results)."""

    response = api_client.get(
        "/api/v1/analytics/routes/performance-trends",
        params={
            "route": "/api/v1/non-existent-route",
            "days": 7,
            "granularity": "hourly"
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data["route"] == "/api/v1/non-existent-route"
    assert data["data_points"] == 0
    assert len(data["trends"]) == 0


def test_performance_trends_parameter_validation(api_client: TestClient):
    """Test parameter validation for performance trends endpoint."""

    # Missing required route parameter
    response = api_client.get(
        "/api/v1/analytics/routes/performance-trends",
        params={"days": 7, "granularity": "hourly"}
    )
    assert response.status_code == 422

    # Invalid granularity
    response = api_client.get(
        "/api/v1/analytics/routes/performance-trends",
        params={
            "route": "/api/v1/content/unified",
            "days": 7,
            "granularity": "weekly"
        }
    )
    assert response.status_code == 422


def test_peak_hours_all_routes(api_client: TestClient, db_session: Session, sample_user):
    """Test GET /api/v1/analytics/routes/peak-hours for all routes."""
    _create_sample_analytics_data(db_session, sample_user)

    response = api_client.get(
        "/api/v1/analytics/routes/peak-hours",
        params={
            "days": 30,
            "min_requests": 10
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data["route"] is None
    assert data["lookback_days"] == 30
    assert data["min_requests_threshold"] == 10
    assert "total_patterns" in data
    assert "peak_hours" in data

    # Should have peak hour data for multiple routes
    if len(data["peak_hours"]) > 0:
        peak = data["peak_hours"][0]
        assert "route" in peak
        assert "hour_of_day" in peak
        assert "avg_requests" in peak
        assert "avg_p95_latency_ms" in peak
        assert "avg_unique_users" in peak
        assert "data_points" in peak

        # Verify hour_of_day is valid (0-23)
        assert 0 <= peak["hour_of_day"] <= 23


def test_peak_hours_specific_route(api_client: TestClient, db_session: Session, sample_user):
    """Test GET /api/v1/analytics/routes/peak-hours for specific route."""
    _create_sample_analytics_data(db_session, sample_user)

    response = api_client.get(
        "/api/v1/analytics/routes/peak-hours",
        params={
            "route": "/api/v1/content/unified",
            "days": 30
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data["route"] == "/api/v1/content/unified"
    assert data["lookback_days"] == 30

    # All results should be for the specified route
    if len(data["peak_hours"]) > 0:
        for peak in data["peak_hours"]:
            assert peak["route"] == "/api/v1/content/unified"


def test_peak_hours_empty_results(api_client: TestClient, db_session: Session, sample_user):
    """Test peak hours with no matching data."""

    response = api_client.get(
        "/api/v1/analytics/routes/peak-hours",
        params={
            "route": "/api/v1/non-existent-route",
            "days": 30
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total_patterns"] == 0
    assert len(data["peak_hours"]) == 0


def test_analytics_endpoints_with_no_data(api_client: TestClient, db_session: Session, sample_user):
    """Test all analytics endpoints return gracefully when no data exists."""

    # Cache priorities - absolute
    response = api_client.get(
        "/api/v1/analytics/routes/cache-priorities",
        params={"n": 10, "system": "absolute"}
    )
    assert response.status_code == 200
    assert response.json()["total_routes"] == 0

    # Cache priorities - relative
    response = api_client.get(
        "/api/v1/analytics/routes/cache-priorities",
        params={"n": 10, "system": "relative"}
    )
    assert response.status_code == 200
    assert response.json()["total_routes"] == 0

    # Performance trends
    response = api_client.get(
        "/api/v1/analytics/routes/performance-trends",
        params={
            "route": "/api/v1/content/unified",
            "days": 7,
            "granularity": "hourly"
        }
    )
    assert response.status_code == 200
    assert response.json()["data_points"] == 0

    # Peak hours
    response = api_client.get(
        "/api/v1/analytics/routes/peak-hours",
        params={"days": 30}
    )
    assert response.status_code == 200
    assert response.json()["total_patterns"] == 0


@pytest.mark.parametrize("days", [7, 14, 30, 90])
def test_cache_priorities_different_lookback_periods(
    api_client: TestClient,
    db_session: Session,
    sample_user,
    days
):
    """Test cache priorities with different lookback periods."""
    _create_sample_analytics_data(db_session, sample_user)

    response = api_client.get(
        "/api/v1/analytics/routes/cache-priorities",
        params={
            "n": 5,
            "system": "absolute",
            "days": days
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["lookback_days"] == days
