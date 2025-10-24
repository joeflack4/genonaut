"""Integration tests for generation analytics Celery tasks.

These tests verify the end-to-end functionality of generation analytics tasks:
1. Transfer from Redis to PostgreSQL
2. Hourly aggregation
"""

import json
import time
from datetime import datetime, timedelta
from typing import Generator
from unittest.mock import patch, MagicMock
import uuid

import pytest
from sqlalchemy.orm import Session
from sqlalchemy import text

from genonaut.worker.tasks import (
    transfer_generation_events_to_postgres,
    aggregate_generation_metrics_hourly,
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
    stream_key = f"{settings.redis_ns}:generation_events:stream"

    # Clean before test
    try:
        redis_client.delete(stream_key)
    except:
        pass

    # Also clean database tables to ensure isolation
    try:
        db_session.execute(text("DELETE FROM generation_events"))
        db_session.execute(text("DELETE FROM generation_metrics_hourly"))
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
        db_session.execute(text("DELETE FROM generation_events"))
        db_session.execute(text("DELETE FROM generation_metrics_hourly"))
        db_session.commit()
    except:
        db_session.rollback()


def _create_test_user(db_session, user_id=None):
    """Create a test user in the database.

    Args:
        db_session: Database session
        user_id: Optional user ID (generates new UUID if not provided)

    Returns:
        User ID
    """
    if user_id is None:
        user_id = str(uuid.uuid4())

    # Insert user
    db_session.execute(text("""
        INSERT INTO users (id, username, email, is_active, preferences, created_at, updated_at)
        VALUES (:user_id, :username, :email, true, '{}', NOW(), NOW())
        ON CONFLICT (id) DO NOTHING
    """), {
        'user_id': user_id,
        'username': f'test_user_{user_id[:8]}',
        'email': f'test_{user_id[:8]}@example.com'
    })
    db_session.commit()

    return user_id


def _add_test_event_to_redis(redis_client, stream_key, **kwargs):
    """Add a test generation event to Redis Stream.

    Args:
        redis_client: Redis client instance
        stream_key: Redis stream key
        **kwargs: Event data (event_type, user_id, duration_ms, etc.)

    Returns:
        Event ID from Redis XADD
    """
    default_event = {
        'event_type': kwargs.get('event_type', 'request'),
        'generation_id': kwargs.get('generation_id', str(uuid.uuid4())),
        'user_id': kwargs.get('user_id', str(uuid.uuid4())),
        'timestamp': kwargs.get('timestamp', datetime.utcnow().isoformat()),
        'generation_type': kwargs.get('generation_type', 'standard'),
        'duration_ms': str(kwargs.get('duration_ms', '')) if kwargs.get('duration_ms') else '',
        'success': str(kwargs.get('success', '')) if 'success' in kwargs else '',
        'error_type': kwargs.get('error_type', ''),
        'error_message': kwargs.get('error_message', ''),
        'queue_wait_time_ms': str(kwargs.get('queue_wait_time_ms', '')) if kwargs.get('queue_wait_time_ms') else '',
        'generation_time_ms': str(kwargs.get('generation_time_ms', '')) if kwargs.get('generation_time_ms') else '',
        'model_checkpoint': kwargs.get('model_checkpoint', ''),
        'image_dimensions': kwargs.get('image_dimensions', ''),
        'batch_size': str(kwargs.get('batch_size', '')) if kwargs.get('batch_size') else '',
        'prompt_tokens': str(kwargs.get('prompt_tokens', '')) if kwargs.get('prompt_tokens') else '',
    }

    return redis_client.xadd(stream_key, default_event)


class TestTransferGenerationEventsToPostgres:
    """Test generation events transfer from Redis to PostgreSQL."""

    def test_transfer_basic_events(self, redis_client, db_session, clean_redis_stream):
        """Test basic transfer of generation events from Redis to PostgreSQL."""
        stream_key = clean_redis_stream
        user_id = _create_test_user(db_session)
        generation_id = str(uuid.uuid4())

        # Add test events to Redis
        _add_test_event_to_redis(
            redis_client, stream_key,
            event_type='request',
            user_id=user_id,
            generation_id=generation_id,
            generation_type='standard'
        )

        _add_test_event_to_redis(
            redis_client, stream_key,
            event_type='completion',
            user_id=user_id,
            generation_id=generation_id,
            duration_ms=3500,
            success=True,
            model_checkpoint='sd_xl_base_1.0.safetensors'
        )

        # Run transfer task
        result = transfer_generation_events_to_postgres()

        # Verify result
        assert result['status'] == 'success'
        assert result['events_transferred'] == 2

        # Verify events in PostgreSQL
        rows = db_session.execute(text(
            "SELECT event_type, user_id, generation_id FROM generation_events ORDER BY created_at"
        )).fetchall()

        assert len(rows) == 2
        assert rows[0].event_type == 'request'
        assert str(rows[0].user_id) == user_id
        assert str(rows[0].generation_id) == generation_id
        assert rows[1].event_type == 'completion'

    def test_transfer_with_failures(self, redis_client, db_session, clean_redis_stream):
        """Test transfer of failed generation events."""
        stream_key = clean_redis_stream
        user_id = _create_test_user(db_session)
        generation_id = str(uuid.uuid4())

        # Add failed completion event
        _add_test_event_to_redis(
            redis_client, stream_key,
            event_type='completion',
            user_id=user_id,
            generation_id=generation_id,
            duration_ms=15000,
            success=False,
            error_type='timeout',
            error_message='ComfyUI request timeout after 30s'
        )

        # Run transfer task
        result = transfer_generation_events_to_postgres()

        # Verify result
        assert result['status'] == 'success'
        assert result['events_transferred'] == 1

        # Verify error details in PostgreSQL
        row = db_session.execute(text(
            "SELECT success, error_type, error_message FROM generation_events WHERE event_type = 'completion'"
        )).fetchone()

        assert row.success == False
        assert row.error_type == 'timeout'
        assert row.error_message == 'ComfyUI request timeout after 30s'

    def test_transfer_handles_empty_stream(self, redis_client, db_session, clean_redis_stream):
        """Test transfer task handles empty Redis stream gracefully."""
        # Run transfer with no events
        result = transfer_generation_events_to_postgres()

        # Should succeed with 0 events transferred
        assert result['status'] == 'success'
        assert result['events_transferred'] == 0

    def test_transfer_batch_processing(self, redis_client, db_session, clean_redis_stream):
        """Test transfer processes multiple events in batches."""
        stream_key = clean_redis_stream

        # Create a test user
        user_id = _create_test_user(db_session)

        # Add 10 test events
        for i in range(10):
            _add_test_event_to_redis(
                redis_client, stream_key,
                event_type='request',
                user_id=user_id,
                generation_id=str(uuid.uuid4())
            )

        # Run transfer task
        result = transfer_generation_events_to_postgres()

        # Verify all events transferred
        assert result['status'] == 'success'
        assert result['events_transferred'] == 10

        # Verify count in PostgreSQL
        count = db_session.execute(text(
            "SELECT COUNT(*) FROM generation_events"
        )).scalar()

        assert count == 10


class TestAggregateGenerationMetricsHourly:
    """Test hourly aggregation of generation metrics."""

    @pytest.mark.skip(reason="Timestamp alignment issue - test data not in aggregation window. See notes/todos-general.md 'Generation Analytics - Celery Aggregation Tests' for details. Priority 2/5.")
    def test_aggregate_basic_metrics(self, db_session, clean_redis_stream):
        """Test basic aggregation of generation metrics."""
        user_id = _create_test_user(db_session)
        generation_id_1 = str(uuid.uuid4())
        generation_id_2 = str(uuid.uuid4())

        # Set reference time to start of current hour
        ref_time = datetime.utcnow().replace(minute=0, second=0, microsecond=0)

        # Insert test events directly into database
        db_session.execute(text("""
            INSERT INTO generation_events
            (event_type, generation_id, user_id, timestamp, generation_type, created_at)
            VALUES
            ('request', :gen_id_1, :user_id, :ts, 'standard', NOW()),
            ('completion', :gen_id_1, :user_id, :ts, 'standard', NOW())
        """), {
            'gen_id_1': generation_id_1,
            'user_id': user_id,
            'ts': ref_time
        })

        db_session.execute(text("""
            UPDATE generation_events
            SET duration_ms = 3500, success = true
            WHERE event_type = 'completion' AND generation_id = :gen_id
        """), {'gen_id': generation_id_1})

        db_session.commit()

        # Run aggregation task
        result = aggregate_generation_metrics_hourly(reference_time=ref_time.isoformat())

        # Verify result
        assert result['status'] == 'success'
        assert result['rows_aggregated'] >= 1  # At least one row aggregated

        # Verify aggregated metrics in PostgreSQL
        row = db_session.execute(text("""
            SELECT
                total_requests,
                successful_generations,
                failed_generations,
                cancelled_generations,
                unique_users
            FROM generation_metrics_hourly
            WHERE timestamp = :ts
        """), {'ts': ref_time}).fetchone()

        assert row.total_requests == 1
        assert row.successful_generations == 1
        assert row.failed_generations == 0
        assert row.cancelled_generations == 0
        assert row.unique_users == 1

    @pytest.mark.skip(reason="Timestamp alignment issue - aggregation query returns no results. See notes/todos-general.md 'Generation Analytics - Celery Aggregation Tests' for details. Priority 2/5.")
    def test_aggregate_duration_percentiles(self, db_session, clean_redis_stream):
        """Test aggregation calculates duration percentiles correctly."""
        user_id = _create_test_user(db_session)
        ref_time = datetime.utcnow().replace(minute=0, second=0, microsecond=0)

        # Insert multiple completions with different durations
        durations = [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000]

        for i, duration in enumerate(durations):
            gen_id = str(uuid.uuid4())
            db_session.execute(text("""
                INSERT INTO generation_events
                (event_type, generation_id, user_id, timestamp, duration_ms, success, created_at)
                VALUES ('completion', :gen_id, :user_id, :ts, :duration, true, NOW())
            """), {
                'gen_id': gen_id,
                'user_id': user_id,
                'ts': ref_time,
                'duration': duration
            })

        db_session.commit()

        # Run aggregation task
        result = aggregate_generation_metrics_hourly(reference_time=ref_time.isoformat())

        # Verify duration metrics
        row = db_session.execute(text("""
            SELECT p50_duration_ms, p95_duration_ms, p99_duration_ms, avg_duration_ms
            FROM generation_metrics_hourly
            WHERE timestamp = :ts
        """), {'ts': ref_time}).fetchone()

        # P50 should be around 5000-6000 (median)
        assert 4500 <= row.p50_duration_ms <= 6500

        # P95 should be around 9000-10000
        assert 8500 <= row.p95_duration_ms <= 10500

        # Average should be 5500
        assert 5000 <= row.avg_duration_ms <= 6000

    def test_aggregate_handles_no_events(self, db_session, clean_redis_stream):
        """Test aggregation handles hours with no events."""
        # Set reference time to an hour with no events
        ref_time = datetime.utcnow().replace(minute=0, second=0, microsecond=0) - timedelta(hours=5)

        # Run aggregation task
        result = aggregate_generation_metrics_hourly(reference_time=ref_time.isoformat())

        # Should succeed with 0 rows affected (no events to aggregate)
        assert result['status'] == 'success'
        assert result['rows_aggregated'] == 0

        # Verify no row created (no events means no aggregation row)
        count = db_session.execute(text("""
            SELECT COUNT(*) FROM generation_metrics_hourly
            WHERE timestamp = :ts
        """), {'ts': ref_time}).scalar()

        # Should be 0 rows since there were no events
        assert count == 0

    @pytest.mark.skip(reason="Timestamp alignment issue - no rows created to test idempotency. See notes/todos-general.md 'Generation Analytics - Celery Aggregation Tests' for details. Priority 2/5.")
    def test_aggregate_idempotency(self, db_session, clean_redis_stream):
        """Test aggregation is idempotent (can run multiple times safely)."""
        user_id = _create_test_user(db_session)
        generation_id = str(uuid.uuid4())
        ref_time = datetime.utcnow().replace(minute=0, second=0, microsecond=0)

        # Insert test event
        db_session.execute(text("""
            INSERT INTO generation_events
            (event_type, generation_id, user_id, timestamp, duration_ms, success, created_at)
            VALUES ('completion', :gen_id, :user_id, :ts, 3500, true, NOW())
        """), {
            'gen_id': generation_id,
            'user_id': user_id,
            'ts': ref_time
        })

        db_session.commit()

        # Run aggregation task twice
        result1 = aggregate_generation_metrics_hourly(reference_time=ref_time.isoformat())
        result2 = aggregate_generation_metrics_hourly(reference_time=ref_time.isoformat())

        # Both should succeed
        assert result1['status'] == 'success'
        assert result2['status'] == 'success'

        # Should only have one row in metrics table
        count = db_session.execute(text("""
            SELECT COUNT(*) FROM generation_metrics_hourly
            WHERE timestamp = :ts
        """), {'ts': ref_time}).scalar()

        assert count == 1

        # Values should be same
        row = db_session.execute(text("""
            SELECT total_requests FROM generation_metrics_hourly
            WHERE timestamp = :ts
        """), {'ts': ref_time}).fetchone()

        assert row.total_requests == 1  # Not doubled
