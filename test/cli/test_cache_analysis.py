"""Tests for cache analysis CLI tools.

Tests both System 1 (absolute thresholds) and System 2 (relative ranking).
"""

from datetime import datetime, timedelta
from typing import Generator

import pytest
from sqlalchemy.orm import Session
from sqlalchemy import text

from genonaut.cli.cache_analysis import (
    calculate_cache_priority_score,
    get_top_routes_for_caching,
    format_output_table,
    format_output_json,
)
from genonaut.cli.cache_analysis_relative import (
    calculate_relative_priority_score,
    get_top_routes_relative,
    _calculate_percentile,
    format_output_table_relative,
    format_output_json_relative,
)

# Import PostgreSQL fixtures
from test.db.postgres_fixtures import postgres_engine, postgres_session


@pytest.fixture()
def db_session(postgres_session) -> Generator[Session, None, None]:
    """Yield a PostgreSQL session for CLI tests.

    This fixture uses the PostgreSQL test database with automatic rollback
    for test isolation.
    """
    yield postgres_session


def _create_sample_hourly_analytics(db_session: Session):
    """Create sample hourly analytics data for testing cache analysis.

    Creates data representing different routes with varying patterns:
    - High frequency, high latency
    - Medium frequency, medium latency
    - Low frequency, very high latency
    - High frequency, low latency

    Args:
        db_session: Database session
    """
    base_timestamp = datetime.utcnow().replace(minute=0, second=0, microsecond=0)

    # Sample routes with different characteristics
    routes_data = [
        # Route 1: High frequency (150 req/hr), high latency (450ms p95)
        {
            'route': '/api/v1/content/unified',
            'method': 'GET',
            'query_params_normalized': '{"page_size": "10", "sort": "created_at"}',
            'avg_requests': 150,
            'p95_latency': 450,
            'unique_users': 45,
        },
        # Route 2: Medium frequency (80 req/hr), medium latency (280ms p95)
        {
            'route': '/api/v1/tags/hierarchy',
            'method': 'GET',
            'query_params_normalized': '{}',
            'avg_requests': 80,
            'p95_latency': 280,
            'unique_users': 25,
        },
        # Route 3: Low frequency (5 req/hr), very high latency (5200ms p95)
        {
            'route': '/api/v1/generation-jobs/status',
            'method': 'POST',
            'query_params_normalized': '{}',
            'avg_requests': 5,
            'p95_latency': 5200,
            'unique_users': 8,
        },
        # Route 4: High frequency (200 req/hr), low latency (50ms p95)
        {
            'route': '/api/v1/health',
            'method': 'GET',
            'query_params_normalized': '{}',
            'avg_requests': 200,
            'p95_latency': 50,
            'unique_users': 100,
        },
    ]

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
    """)

    # Create 7 days of hourly data for each route
    for i in range(7 * 24):  # 7 days * 24 hours
        timestamp = base_timestamp - timedelta(hours=i)

        for route_data in routes_data:
            db_session.execute(insert_query, {
                'timestamp': timestamp,
                'route': route_data['route'],
                'method': route_data['method'],
                'query_params_normalized': route_data['query_params_normalized'],
                'total_requests': route_data['avg_requests'],
                'successful_requests': route_data['avg_requests'] - 2,
                'client_errors': 1,
                'server_errors': 1,
                'avg_duration_ms': int(route_data['p95_latency'] * 0.7),
                'p50_duration_ms': int(route_data['p95_latency'] * 0.5),
                'p95_duration_ms': route_data['p95_latency'],
                'p99_duration_ms': int(route_data['p95_latency'] * 1.2),
                'unique_users': route_data['unique_users'],
                'cache_hits': 0,
                'cache_misses': 0,
                'created_at': timestamp,
            })

    db_session.commit()


# ============================================================================
# Tests for System 1: Absolute Thresholds
# ============================================================================

class TestCachePriorityScoreCalculation:
    """Tests for cache priority score calculation (System 1)."""

    def test_score_increases_with_frequency(self):
        """Higher request frequency increases priority score."""
        row1 = {
            'avg_hourly_requests': 100,
            'avg_p95_latency': 200,
            'avg_unique_users': 50,
        }
        row2 = {
            'avg_hourly_requests': 200,
            'avg_p95_latency': 200,
            'avg_unique_users': 50,
        }

        score1 = calculate_cache_priority_score(row1)
        score2 = calculate_cache_priority_score(row2)

        assert score2 > score1

    def test_score_increases_with_latency(self):
        """Higher latency increases priority score."""
        row1 = {
            'avg_hourly_requests': 100,
            'avg_p95_latency': 100,
            'avg_unique_users': 50,
        }
        row2 = {
            'avg_hourly_requests': 100,
            'avg_p95_latency': 500,
            'avg_unique_users': 50,
        }

        score1 = calculate_cache_priority_score(row1)
        score2 = calculate_cache_priority_score(row2)

        assert score2 > score1

    def test_score_increases_with_unique_users(self):
        """Higher unique user count increases priority score."""
        row1 = {
            'avg_hourly_requests': 100,
            'avg_p95_latency': 200,
            'avg_unique_users': 10,
        }
        row2 = {
            'avg_hourly_requests': 100,
            'avg_p95_latency': 200,
            'avg_unique_users': 100,
        }

        score1 = calculate_cache_priority_score(row1)
        score2 = calculate_cache_priority_score(row2)

        assert score2 > score1

    def test_user_diversity_score_capped(self):
        """User diversity score component is capped at 10."""
        row = {
            'avg_hourly_requests': 0,  # Isolate user diversity component
            'avg_p95_latency': 0,
            'avg_unique_users': 1000,  # Very high
        }

        score = calculate_cache_priority_score(row)

        # User diversity component: min(unique_users / 10, 10) = min(100, 10) = 10
        assert score == 10


class TestGetTopRoutesForCaching:
    """Tests for get_top_routes_for_caching function (System 1)."""

    def test_returns_top_n_routes(self, db_session):
        """Returns requested number of top routes."""
        _create_sample_hourly_analytics(db_session)

        routes = get_top_routes_for_caching(n=2, lookback_days=7)

        assert len(routes) <= 2

    def test_filters_by_minimum_requests(self, db_session):
        """Filters out routes below minimum request threshold."""
        _create_sample_hourly_analytics(db_session)

        # Set high threshold that should exclude low-traffic routes
        routes = get_top_routes_for_caching(
            n=10,
            lookback_days=7,
            min_requests_per_hour=50
        )

        # Should exclude /api/v1/generation-jobs/status (only 5 req/hr)
        route_paths = [r['route'] for r in routes]
        assert '/api/v1/generation-jobs/status' not in route_paths

    def test_filters_by_minimum_latency(self, db_session):
        """Filters out routes below minimum latency threshold."""
        _create_sample_hourly_analytics(db_session)

        # Set high latency threshold
        routes = get_top_routes_for_caching(
            n=10,
            lookback_days=7,
            min_latency_ms=200
        )

        # Should exclude /api/v1/health (only 50ms p95)
        route_paths = [r['route'] for r in routes]
        assert '/api/v1/health' not in route_paths

    def test_routes_sorted_by_priority(self, db_session):
        """Routes are sorted by descending cache priority score."""
        _create_sample_hourly_analytics(db_session)

        routes = get_top_routes_for_caching(
            n=10,
            lookback_days=7,
            min_requests_per_hour=10,
            min_latency_ms=100
        )

        if len(routes) > 1:
            # Verify descending order
            for i in range(len(routes) - 1):
                assert routes[i]['cache_priority_score'] >= routes[i+1]['cache_priority_score']

    def test_includes_all_required_fields(self, db_session):
        """Returned routes include all required fields."""
        _create_sample_hourly_analytics(db_session)

        routes = get_top_routes_for_caching(n=1, lookback_days=7)

        if len(routes) > 0:
            route = routes[0]
            required_fields = [
                'route', 'method', 'query_params_normalized',
                'avg_hourly_requests', 'avg_p95_latency', 'avg_unique_users',
                'cache_priority_score', 'success_rate', 'total_requests'
            ]

            for field in required_fields:
                assert field in route


class TestCacheAnalysisOutputFormats:
    """Tests for output formatting functions (System 1)."""

    def test_table_format_output(self, db_session):
        """Table format produces readable output."""
        _create_sample_hourly_analytics(db_session)

        routes = get_top_routes_for_caching(n=2, lookback_days=7)
        table = format_output_table(routes)

        assert isinstance(table, str)
        assert len(table) > 0
        # Should contain table headers
        assert 'Route' in table or 'route' in table
        assert 'Priority Score' in table or 'Priority' in table

    def test_json_format_output(self, db_session):
        """JSON format produces valid JSON."""
        import json

        _create_sample_hourly_analytics(db_session)

        routes = get_top_routes_for_caching(n=2, lookback_days=7)
        json_output = format_output_json(routes)

        # Should be valid JSON
        parsed = json.loads(json_output)
        assert isinstance(parsed, list)

        if len(parsed) > 0:
            route = parsed[0]
            assert 'route' in route
            assert 'cache_priority_score' in route
            assert isinstance(route['avg_hourly_requests'], (int, float))


# ============================================================================
# Tests for System 2: Relative Ranking
# ============================================================================

class TestCalculatePercentile:
    """Tests for percentile calculation helper."""

    def test_percentile_of_lowest_value(self):
        """Lowest value in distribution is at 0th percentile."""
        distribution = [10, 20, 30, 40, 50]
        result = _calculate_percentile(10, distribution)
        assert result >= 0
        assert result <= 20  # Should be low percentile

    def test_percentile_of_highest_value(self):
        """Highest value in distribution is at 100th percentile."""
        distribution = [10, 20, 30, 40, 50]
        result = _calculate_percentile(50, distribution)
        assert result >= 80  # Should be high percentile
        assert result <= 100

    def test_percentile_of_median(self):
        """Median value is around 50th percentile."""
        distribution = [10, 20, 30, 40, 50]
        result = _calculate_percentile(30, distribution)
        assert 40 <= result <= 60  # Should be near middle

    def test_percentile_with_empty_distribution(self):
        """Empty distribution returns default (50.0)."""
        result = _calculate_percentile(25, [])
        assert result == 50.0

    def test_percentile_clamped_to_0_100(self):
        """Percentile result is always between 0 and 100."""
        distribution = [10, 20, 30]
        result1 = _calculate_percentile(5, distribution)  # Below min
        result2 = _calculate_percentile(50, distribution)  # Above max

        assert 0 <= result1 <= 100
        assert 0 <= result2 <= 100


class TestCalculateRelativePriorityScore:
    """Tests for relative priority score calculation (System 2)."""

    def test_score_uses_weighted_percentiles(self):
        """Score is weighted average of percentiles."""
        row = {
            'avg_hourly_requests': 50,
            'avg_p95_latency': 300,
            'avg_unique_users': 25,
        }

        stats = {
            'request_distribution': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
            'latency_distribution': [100, 200, 300, 400, 500],
            'user_distribution': [5, 10, 15, 20, 25, 30, 35],
        }

        result = calculate_relative_priority_score(row, stats)

        assert 'priority_score' in result
        assert 'popularity_percentile' in result
        assert 'latency_percentile' in result
        assert 'user_percentile' in result

        # Score should be weighted average: 40% latency + 40% popularity + 20% users
        expected_score = (
            result['latency_percentile'] * 0.4 +
            result['popularity_percentile'] * 0.4 +
            result['user_percentile'] * 0.2
        )

        assert abs(result['priority_score'] - expected_score) < 0.1

    def test_high_latency_increases_score(self):
        """High latency percentile increases priority score."""
        row_low_latency = {
            'avg_hourly_requests': 50,
            'avg_p95_latency': 100,  # Low
            'avg_unique_users': 25,
        }

        row_high_latency = {
            'avg_hourly_requests': 50,
            'avg_p95_latency': 500,  # High
            'avg_unique_users': 25,
        }

        stats = {
            'request_distribution': [50],
            'latency_distribution': [100, 200, 300, 400, 500],
            'user_distribution': [25],
        }

        score_low = calculate_relative_priority_score(row_low_latency, stats)
        score_high = calculate_relative_priority_score(row_high_latency, stats)

        assert score_high['priority_score'] > score_low['priority_score']


class TestGetTopRoutesRelative:
    """Tests for get_top_routes_relative function (System 2)."""

    def test_returns_top_n_routes(self, db_session):
        """Returns requested number of top routes."""
        from unittest.mock import patch
        _create_sample_hourly_analytics(db_session)

        # Mock get_database_session to use test session
        with patch('genonaut.cli.cache_analysis_relative.get_database_session') as mock_get_db:
            def session_generator():
                yield db_session
            mock_get_db.return_value = session_generator()

            routes = get_top_routes_relative(n=2, lookback_days=7)
            assert len(routes) <= 2

    def test_no_minimum_thresholds(self, db_session):
        """Returns routes even with very low traffic (no thresholds)."""
        from unittest.mock import patch
        _create_sample_hourly_analytics(db_session)

        # Mock get_database_session to use test session
        with patch('genonaut.cli.cache_analysis_relative.get_database_session') as mock_get_db:
            def session_generator():
                yield db_session
            mock_get_db.return_value = session_generator()

            # Should include all routes, even low-traffic ones
            routes = get_top_routes_relative(n=10, lookback_days=7)

            # Should include /api/v1/generation-jobs/status (only 5 req/hr)
            route_paths = [r['route'] for r in routes]

            # Check that we got some routes
            assert len(routes) > 0, f"Expected routes but got: {routes}"

            # Check for specific low-traffic route
            assert '/api/v1/generation-jobs/status' in route_paths

    def test_routes_sorted_by_relative_priority(self, db_session):
        """Routes are sorted by descending relative priority score."""
        from unittest.mock import patch
        _create_sample_hourly_analytics(db_session)

        with patch('genonaut.cli.cache_analysis_relative.get_database_session') as mock_get_db:
            def session_generator():
                yield db_session
            mock_get_db.return_value = session_generator()

            routes = get_top_routes_relative(n=10, lookback_days=7)

            if len(routes) > 1:
                # Verify descending order
                for i in range(len(routes) - 1):
                    assert routes[i]['priority_score'] >= routes[i+1]['priority_score']

    def test_includes_percentile_fields(self, db_session):
        """Returned routes include percentile scores."""
        from unittest.mock import patch
        _create_sample_hourly_analytics(db_session)

        with patch('genonaut.cli.cache_analysis_relative.get_database_session') as mock_get_db:
            def session_generator():
                yield db_session
            mock_get_db.return_value = session_generator()

            routes = get_top_routes_relative(n=1, lookback_days=7)

            if len(routes) > 0:
                route = routes[0]
                assert 'priority_score' in route
                assert 'popularity_percentile' in route
                assert 'latency_percentile' in route
                assert 'user_percentile' in route

                # Percentiles should be between 0 and 100
                assert 0 <= route['popularity_percentile'] <= 100
                assert 0 <= route['latency_percentile'] <= 100
                assert 0 <= route['user_percentile'] <= 100


class TestRelativeOutputFormats:
    """Tests for output formatting functions (System 2)."""

    def test_table_format_includes_percentiles(self, db_session):
        """Table format includes percentile columns."""
        _create_sample_hourly_analytics(db_session)

        routes = get_top_routes_relative(n=2, lookback_days=7)
        table = format_output_table_relative(routes)

        assert isinstance(table, str)
        assert len(table) > 0
        # Should contain percentile indicators
        assert 'Pop%' in table or 'Lat%' in table or 'User%' in table

    def test_json_format_includes_percentiles(self, db_session):
        """JSON format includes percentile fields."""
        import json

        _create_sample_hourly_analytics(db_session)

        routes = get_top_routes_relative(n=2, lookback_days=7)
        json_output = format_output_json_relative(routes)

        parsed = json.loads(json_output)
        assert isinstance(parsed, list)

        if len(parsed) > 0:
            route = parsed[0]
            assert 'priority_score' in route
            assert 'popularity_percentile' in route
            assert 'latency_percentile' in route
            assert 'user_percentile' in route


# ============================================================================
# Comparison Tests
# ============================================================================

class TestAbsoluteVsRelativeComparison:
    """Tests comparing System 1 (absolute) vs System 2 (relative)."""

    def test_absolute_filters_relative_does_not(self, db_session):
        """Absolute system filters by thresholds, relative does not."""
        _create_sample_hourly_analytics(db_session)

        # Absolute with high thresholds
        absolute_routes = get_top_routes_for_caching(
            n=10,
            min_requests_per_hour=50,
            min_latency_ms=200
        )

        # Relative has no thresholds
        relative_routes = get_top_routes_relative(n=10)

        # Relative should return more routes (includes low-traffic ones)
        assert len(relative_routes) >= len(absolute_routes)

    def test_both_systems_rank_high_impact_routes(self, db_session):
        """Both systems should rank high-frequency, high-latency routes highly."""
        _create_sample_hourly_analytics(db_session)

        absolute_routes = get_top_routes_for_caching(n=5)
        relative_routes = get_top_routes_relative(n=5)

        # /api/v1/content/unified should be highly ranked in both
        # (high frequency 150 req/hr, high latency 450ms)
        absolute_top_routes = [r['route'] for r in absolute_routes[:3]]
        relative_top_routes = [r['route'] for r in relative_routes[:3]]

        # Both should include the high-impact route in top 3
        high_impact_route = '/api/v1/content/unified'
        assert high_impact_route in absolute_top_routes or len(absolute_routes) < 3
        assert high_impact_route in relative_top_routes or len(relative_routes) < 3
