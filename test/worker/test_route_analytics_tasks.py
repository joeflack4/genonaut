"""Integration tests for route analytics Celery tasks.

These tests verify the end-to-end functionality of route analytics tasks:
1. Transfer from Redis to PostgreSQL
2. Hourly aggregation
"""

import json
import time
from datetime import datetime, timedelta
from typing import Generator
from unittest.mock import patch, MagicMock

import pytest
from sqlalchemy.orm import Session
from sqlalchemy import text

from genonaut.worker.tasks import (
    transfer_route_analytics_to_postgres,
    aggregate_route_analytics_hourly,
)
from genonaut.worker.pubsub import get_redis_client
from genonaut.api.config import get_settings

# Import PostgreSQL fixtures
from test.db.postgres_fixtures import postgres_engine, postgres_session


@pytest.fixture()
def db_session(postgres_session) -> Generator[Session, None, None]:
    """Yield a PostgreSQL session for worker tests.

    This fixture uses the PostgreSQL test database with automatic rollback
    for test isolation.
    """
    yield postgres_session


@pytest.fixture()
def redis_client():
    """Provide Redis client for tests."""
    try:
        client = get_redis_client()
        client.ping()
        yield client
    except Exception as e:
        pytest.skip(f"Redis not available: {e}")


@pytest.fixture()
def clean_redis_stream(redis_client, db_session):
    """Clean up Redis stream and database before and after test."""
    settings = get_settings()
    stream_key = f"{settings.redis_ns}:route_analytics:stream"

    # Clean before test
    try:
        redis_client.delete(stream_key)
    except:
        pass

    # Also clean database table to ensure isolation
    try:
        db_session.execute(text("DELETE FROM route_analytics"))
        db_session.commit()
    except:
        db_session.rollback()

    yield stream_key

    # Clean after test
    try:
        redis_client.delete(stream_key)
    except:
        pass

    # Clean database again
    try:
        db_session.execute(text("DELETE FROM route_analytics"))
        db_session.commit()
    except:
        db_session.rollback()


def _add_test_event_to_redis(redis_client, stream_key, **kwargs):
    """Add a test route analytics event to Redis Stream.

    Args:
        redis_client: Redis client instance
        stream_key: Redis stream key
        **kwargs: Event data (route, method, duration_ms, etc.)

    Returns:
        Event ID from Redis XADD
    """
    default_event = {
        'route': kwargs.get('route', '/api/v1/test'),
        'method': kwargs.get('method', 'GET'),
        'user_id': kwargs.get('user_id', ''),  # Empty string -> None in transfer task
        'timestamp': str(kwargs.get('timestamp', time.time())),
        'duration_ms': str(kwargs.get('duration_ms', 100)),
        'status_code': str(kwargs.get('status_code', 200)),
        'query_params': kwargs.get('query_params', '{}'),
        'query_params_normalized': kwargs.get('query_params_normalized', '{}'),
        'request_size_bytes': str(kwargs.get('request_size_bytes', 0)),
        'response_size_bytes': str(kwargs.get('response_size_bytes', 1234)),
        'error_type': kwargs.get('error_type', ''),
        'cache_status': kwargs.get('cache_status', ''),
    }

    return redis_client.xadd(stream_key, default_event)


class TestTransferRouteAnalyticsToPostgres:
    """Tests for transfer_route_analytics_to_postgres task."""

    def test_transfer_single_event(self, db_session, redis_client, clean_redis_stream):
        """Successfully transfer a single event from Redis to PostgreSQL."""
        stream_key = clean_redis_stream

        # Add test event to Redis
        event_id = _add_test_event_to_redis(
            redis_client,
            stream_key,
            route='/api/v1/content/unified',
            method='GET',
            duration_ms=250,
            status_code=200
        )

        assert event_id is not None

        # Run transfer task
        result = transfer_route_analytics_to_postgres()

        # Verify task success
        assert result['status'] == 'success'
        assert result['events_transferred'] == 1

        # Verify data in PostgreSQL
        query = text("SELECT * FROM route_analytics WHERE route = '/api/v1/content/unified'")
        rows = db_session.execute(query).fetchall()

        assert len(rows) == 1
        row = rows[0]
        assert row.route == '/api/v1/content/unified'
        assert row.method == 'GET'
        assert row.duration_ms == 250
        assert row.status_code == 200

    def test_transfer_multiple_events(self, db_session, redis_client, clean_redis_stream):
        """Successfully transfer multiple events in batch."""
        stream_key = clean_redis_stream

        # Add multiple test events
        routes = [
            '/api/v1/content/unified',
            '/api/v1/tags/hierarchy',
            '/api/v1/users/profile',
        ]

        for route in routes:
            _add_test_event_to_redis(
                redis_client,
                stream_key,
                route=route,
                duration_ms=150
            )

        # Run transfer task
        result = transfer_route_analytics_to_postgres()

        # Verify task success
        assert result['status'] == 'success'
        assert result['events_transferred'] == 3

        # Verify all routes in PostgreSQL
        for route in routes:
            query = text(f"SELECT COUNT(*) FROM route_analytics WHERE route = :route")
            count = db_session.execute(query, {'route': route}).scalar()
            assert count == 1

    def test_transfer_preserves_query_params(self, db_session, redis_client, clean_redis_stream):
        """Transfer correctly preserves query parameters and normalization."""
        stream_key = clean_redis_stream

        query_params = json.dumps({'page': '2', 'page_size': '10', 'sort': 'created_at'})
        query_params_normalized = json.dumps({'page_size': '10', 'sort': 'created_at'})

        _add_test_event_to_redis(
            redis_client,
            stream_key,
            route='/api/v1/content/unified',
            query_params=query_params,
            query_params_normalized=query_params_normalized
        )

        # Run transfer task
        result = transfer_route_analytics_to_postgres()
        assert result['status'] == 'success'

        # Verify query params in PostgreSQL
        query = text("SELECT query_params, query_params_normalized FROM route_analytics WHERE route = '/api/v1/content/unified'")
        row = db_session.execute(query).fetchone()

        assert row is not None
        assert 'page' in row.query_params
        assert 'page' not in row.query_params_normalized
        assert row.query_params_normalized['page_size'] == '10'
        assert row.query_params_normalized['sort'] == 'created_at'

    def test_transfer_handles_null_user_id(self, db_session, redis_client, clean_redis_stream):
        """Transfer correctly handles events without user_id."""
        stream_key = clean_redis_stream

        _add_test_event_to_redis(
            redis_client,
            stream_key,
            route='/api/v1/health',
            user_id=''  # Empty string should become NULL
        )

        # Run transfer task
        result = transfer_route_analytics_to_postgres()
        assert result['status'] == 'success'

        # Verify NULL user_id in PostgreSQL
        query = text("SELECT user_id FROM route_analytics WHERE route = '/api/v1/health'")
        row = db_session.execute(query).fetchone()

        assert row is not None
        assert row.user_id is None

    def test_transfer_with_error_types(self, db_session, redis_client, clean_redis_stream):
        """Transfer correctly handles different error types."""
        stream_key = clean_redis_stream

        # Add events with different status codes
        test_cases = [
            ('/api/v1/success', 200, None),
            ('/api/v1/not-found', 404, 'client_error'),
            ('/api/v1/server-error', 500, 'server_error'),
        ]

        for route, status_code, expected_error_type in test_cases:
            _add_test_event_to_redis(
                redis_client,
                stream_key,
                route=route,
                status_code=status_code,
                error_type=expected_error_type or ''
            )

        # Run transfer task
        result = transfer_route_analytics_to_postgres()
        assert result['status'] == 'success'
        assert result['events_transferred'] == 3

        # Verify error types in PostgreSQL
        for route, _, expected_error_type in test_cases:
            query = text("SELECT error_type FROM route_analytics WHERE route = :route")
            row = db_session.execute(query, {'route': route}).fetchone()

            assert row is not None
            assert row.error_type == expected_error_type

    def test_transfer_with_no_events(self, db_session, redis_client, clean_redis_stream):
        """Transfer task succeeds gracefully when no events in Redis."""
        # Don't add any events

        # Run transfer task
        result = transfer_route_analytics_to_postgres()

        # Verify task success with zero transfers
        assert result['status'] == 'success'
        assert result['events_transferred'] == 0

    def test_transfer_trims_redis_after_success(self, db_session, redis_client, clean_redis_stream):
        """Transfer task processes events but keeps stream for other consumers."""
        stream_key = clean_redis_stream

        # Add test events
        for i in range(5):
            _add_test_event_to_redis(
                redis_client,
                stream_key,
                route=f'/api/v1/test-{i}'
            )

        # Verify events in stream before transfer
        stream_length_before = redis_client.xlen(stream_key)
        assert stream_length_before == 5

        # Run transfer task
        result = transfer_route_analytics_to_postgres()
        assert result['status'] == 'success'
        assert result['events_transferred'] == 5

        # Verify events still in stream after transfer
        # (Transfer task only trims when stream exceeds 100K entries)
        stream_length_after = redis_client.xlen(stream_key)
        assert stream_length_after == 5  # Events remain for other consumers


class TestAggregateRouteAnalyticsHourly:
    """Tests for aggregate_route_analytics_hourly task."""

    def _run_aggregation_with_session(self, db_session, reference_time=None):
        """Helper to run aggregation with mocked session and commit.

        Args:
            db_session: Database session to use
            reference_time: Optional reference time for aggregation (ISO format string).
                          If not provided, uses current time.
        """
        # Store original methods
        original_commit = db_session.commit
        original_close = db_session.close

        # Replace commit with flush to maintain test isolation
        # Replace close with a no-op to keep session alive
        db_session.commit = db_session.flush
        db_session.close = lambda: None  # No-op

        try:
            with patch('genonaut.worker.tasks.get_database_session') as mock_get_db:
                def session_generator():
                    yield db_session
                mock_get_db.return_value = session_generator()

                # If no reference_time provided, use current time
                if reference_time is None:
                    reference_time = datetime.utcnow().isoformat()

                # Run aggregation
                result = aggregate_route_analytics_hourly(reference_time=reference_time)

                return result
        finally:
            # Restore original methods
            db_session.commit = original_commit
            db_session.close = original_close

    def _create_raw_analytics_data(self, db_session, base_timestamp=None):
        """Create sample raw route analytics data for testing aggregation.

        Args:
            db_session: Database session
            base_timestamp: Base timestamp for events (defaults to 1 hour ago)

        Returns:
            Base timestamp used
        """
        if base_timestamp is None:
            # Default to 1 hour ago (last completed hour)
            base_timestamp = datetime.utcnow() - timedelta(hours=1)

        # Ensure timestamp is at start of hour
        base_timestamp = base_timestamp.replace(minute=0, second=0, microsecond=0)

        # Create events for a specific route with varying latencies
        insert_query = text("""
            INSERT INTO route_analytics (
                route, method, user_id, timestamp, duration_ms, status_code,
                query_params, query_params_normalized,
                request_size_bytes, response_size_bytes, created_at
            ) VALUES (
                :route, :method, :user_id, :timestamp, :duration_ms, :status_code,
                :query_params, :query_params_normalized,
                :request_size_bytes, :response_size_bytes, :created_at
            )
        """)

        # Create multiple events within the hour
        # Note: user_id set to None since it's nullable and we don't need user tracking for these tests
        events = [
            # Fast requests
            (base_timestamp + timedelta(minutes=5), 100, 200),
            (base_timestamp + timedelta(minutes=10), 120, 200),
            (base_timestamp + timedelta(minutes=15), 110, 200),
            # Slow requests
            (base_timestamp + timedelta(minutes=20), 500, 200),
            (base_timestamp + timedelta(minutes=25), 450, 200),
            # Error
            (base_timestamp + timedelta(minutes=30), 200, 404),
            (base_timestamp + timedelta(minutes=35), 150, 500),
        ]

        for timestamp, duration, status in events:
            db_session.execute(insert_query, {
                'route': '/api/v1/content/unified',
                'method': 'GET',
                'user_id': None,
                'timestamp': timestamp,
                'duration_ms': duration,
                'status_code': status,
                'query_params': '{"page_size": "10"}',
                'query_params_normalized': '{"page_size": "10"}',
                'request_size_bytes': 100,
                'response_size_bytes': 1000,
                'created_at': timestamp,
            })

        # Use flush instead of commit to keep data in same transaction
        db_session.flush()
        return base_timestamp

    def test_aggregation_creates_hourly_stats(self, db_session):
        """Aggregation task creates hourly statistics."""
        # Create raw data for last hour
        base_timestamp = self._create_raw_analytics_data(db_session)

        # Flush to ensure data is available to the same session
        db_session.flush()

        # Run aggregation task with mocked session
        # Pass reference_time as 1 hour after base_timestamp (the "current" hour from test perspective)
        reference_time = (base_timestamp + timedelta(hours=1)).isoformat()
        result = self._run_aggregation_with_session(db_session, reference_time=reference_time)

        # Verify task success
        assert result['status'] == 'success'
        assert result['rows_aggregated'] > 0

        # Verify aggregated data exists
        query = text("""
            SELECT * FROM route_analytics_hourly
            WHERE route = '/api/v1/content/unified'
                AND timestamp = :timestamp
        """)
        row = db_session.execute(query, {'timestamp': base_timestamp}).fetchone()

        assert row is not None
        assert row.route == '/api/v1/content/unified'
        assert row.method == 'GET'
        assert row.total_requests == 7

    def test_aggregation_calculates_success_rate(self, db_session):
        """Aggregation correctly calculates success rate."""
        base_timestamp = self._create_raw_analytics_data(db_session)

        # Flush to ensure data is available to the same session
        db_session.flush()

        # Run aggregation with mocked session
        reference_time = (base_timestamp + timedelta(hours=1)).isoformat()
        self._run_aggregation_with_session(db_session, reference_time=reference_time)

        # Verify success rate
        query = text("""
            SELECT total_requests, successful_requests, client_errors, server_errors
            FROM route_analytics_hourly
            WHERE route = '/api/v1/content/unified'
                AND timestamp = :timestamp
        """)
        row = db_session.execute(query, {'timestamp': base_timestamp}).fetchone()

        assert row is not None
        assert row.total_requests == 7
        assert row.successful_requests == 5  # 5 requests with status 200
        assert row.client_errors == 1  # 1 request with status 404
        assert row.server_errors == 1  # 1 request with status 500

    def test_aggregation_calculates_percentiles(self, db_session):
        """Aggregation correctly calculates latency percentiles."""
        base_timestamp = self._create_raw_analytics_data(db_session)

        # Flush to ensure data is available to the same session
        db_session.flush()

        # Run aggregation with mocked session
        reference_time = (base_timestamp + timedelta(hours=1)).isoformat()
        self._run_aggregation_with_session(db_session, reference_time=reference_time)

        # Verify percentiles
        query = text("""
            SELECT avg_duration_ms, p50_duration_ms, p95_duration_ms, p99_duration_ms
            FROM route_analytics_hourly
            WHERE route = '/api/v1/content/unified'
                AND timestamp = :timestamp
        """)
        row = db_session.execute(query, {'timestamp': base_timestamp}).fetchone()

        assert row is not None
        # Durations: 100, 110, 120, 150, 200, 450, 500
        assert row.avg_duration_ms > 0
        assert row.p50_duration_ms > 0  # Median
        assert row.p95_duration_ms > row.p50_duration_ms  # p95 should be higher
        assert row.p99_duration_ms >= row.p95_duration_ms

    def test_aggregation_counts_unique_users(self, db_session):
        """Aggregation correctly counts unique users."""
        base_timestamp = self._create_raw_analytics_data(db_session)

        # Flush to ensure data is available to the same session
        db_session.flush()

        # Run aggregation with mocked session
        reference_time = (base_timestamp + timedelta(hours=1)).isoformat()
        self._run_aggregation_with_session(db_session, reference_time=reference_time)

        # Verify unique user count
        query = text("""
            SELECT unique_users
            FROM route_analytics_hourly
            WHERE route = '/api/v1/content/unified'
                AND timestamp = :timestamp
        """)
        row = db_session.execute(query, {'timestamp': base_timestamp}).fetchone()

        assert row is not None
        assert row.unique_users == 0  # All user_ids are None (NULL values not counted)

    def test_aggregation_is_idempotent(self, db_session):
        """Aggregation can be run multiple times without duplicating data."""
        base_timestamp = self._create_raw_analytics_data(db_session)

        # Flush to ensure data is available to the same session
        db_session.flush()

        # Run aggregation twice to test idempotency
        reference_time = (base_timestamp + timedelta(hours=1)).isoformat()
        result1 = self._run_aggregation_with_session(db_session, reference_time=reference_time)
        result2 = self._run_aggregation_with_session(db_session, reference_time=reference_time)

        # Both should succeed
        assert result1['status'] == 'success'
        assert result2['status'] == 'success'

        # Verify only one row exists (ON CONFLICT DO UPDATE)
        query = text("""
            SELECT COUNT(*) FROM route_analytics_hourly
            WHERE route = '/api/v1/content/unified'
                AND timestamp = :timestamp
        """)
        count = db_session.execute(query, {'timestamp': base_timestamp}).scalar()

        assert count == 1

    def test_aggregation_with_no_data(self, db_session):
        """Aggregation succeeds gracefully when no data to aggregate."""
        # Don't create any raw data

        # Run aggregation with mocked session
        result = self._run_aggregation_with_session(db_session)

        # Should succeed with zero rows
        assert result['status'] == 'success'
        assert result['rows_aggregated'] == 0

    def test_aggregation_groups_by_query_params(self, db_session):
        """Aggregation groups routes by normalized query parameters."""
        base_timestamp = datetime.utcnow() - timedelta(hours=1)
        base_timestamp = base_timestamp.replace(minute=0, second=0, microsecond=0)

        insert_query = text("""
            INSERT INTO route_analytics (
                route, method, timestamp, duration_ms, status_code,
                query_params_normalized, created_at
            ) VALUES (
                :route, :method, :timestamp, :duration_ms, :status_code,
                :query_params_normalized, :created_at
            )
        """)

        # Create events with different query param patterns
        patterns = [
            '{"page_size": "10", "sort": "created_at"}',
            '{"page_size": "10", "sort": "created_at"}',  # Duplicate pattern
            '{"page_size": "50", "sort": "created_at"}',  # Different pattern
        ]

        for i, pattern in enumerate(patterns):
            timestamp = base_timestamp + timedelta(minutes=i*10)
            db_session.execute(insert_query, {
                'route': '/api/v1/content/unified',
                'method': 'GET',
                'timestamp': timestamp,
                'duration_ms': 100,
                'status_code': 200,
                'query_params_normalized': pattern,
                'created_at': timestamp,
            })

        # Use flush instead of commit to keep data in same transaction
        db_session.flush()

        # Mock the database session to use test session
        with patch('genonaut.worker.tasks.get_database_session') as mock_get_db:
            def session_generator():
                yield db_session
            mock_get_db.return_value = session_generator()

            # Run aggregation with reference time as 1 hour after base_timestamp
            reference_time = (base_timestamp + timedelta(hours=1)).isoformat()
            aggregate_route_analytics_hourly(reference_time=reference_time)

        # Verify two distinct aggregated rows (2 different patterns)
        query = text("""
            SELECT COUNT(*) FROM route_analytics_hourly
            WHERE route = '/api/v1/content/unified'
                AND timestamp = :timestamp
        """)
        count = db_session.execute(query, {'timestamp': base_timestamp}).scalar()

        # Should have 2 rows: one for page_size=10, one for page_size=50
        assert count == 2
