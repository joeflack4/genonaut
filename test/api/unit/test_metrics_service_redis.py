"""Unit tests for MetricsService Redis writes.

These tests verify that MetricsService correctly writes generation events
to Redis Streams without impacting performance.
"""

import time
import json
import uuid
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest

from genonaut.api.services.metrics_service import MetricsService
from genonaut.worker.pubsub import get_redis_client
from genonaut.api.config import get_settings


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
def clean_redis_stream(redis_client):
    """Clean up Redis stream before and after test."""
    settings = get_settings()
    stream_key = f"{settings.redis_ns}:generation_events:stream"

    # Clean before test
    try:
        redis_client.delete(stream_key)
    except:
        pass

    yield stream_key

    # Clean after test
    try:
        redis_client.delete(stream_key)
    except:
        pass


@pytest.fixture()
def metrics_service():
    """Create MetricsService instance for testing."""
    return MetricsService()


class TestMetricsServiceRedisWrites:
    """Test MetricsService writes to Redis."""

    def test_record_generation_request_writes_to_redis(
        self,
        metrics_service,
        redis_client,
        clean_redis_stream
    ):
        """Test that record_generation_request writes to Redis Stream."""
        stream_key = clean_redis_stream
        user_id = str(uuid.uuid4())
        generation_id = str(uuid.uuid4())

        # Record a generation request
        metrics_service.record_generation_request(
            user_id=user_id,
            generation_type="standard",
            generation_id=generation_id
        )

        # Check Redis stream has the event
        events = redis_client.xrange(stream_key, count=1)

        assert len(events) == 1
        event_id, event_data = events[0]

        # Verify event data (Redis returns strings, not bytes)
        assert event_data['event_type'] == 'request'
        assert event_data['user_id'] == user_id
        assert event_data['generation_id'] == generation_id
        assert event_data['generation_type'] == 'standard'

    def test_record_generation_completion_writes_to_redis(
        self,
        metrics_service,
        redis_client,
        clean_redis_stream
    ):
        """Test that record_generation_completion writes to Redis Stream."""
        stream_key = clean_redis_stream
        user_id = str(uuid.uuid4())
        generation_id = str(uuid.uuid4())

        # Record a generation completion (duration in seconds)
        metrics_service.record_generation_completion(
            user_id=user_id,
            duration=3.5,  # 3.5 seconds = 3500 ms
            success=True,
            generation_id=generation_id
        )

        # Check Redis stream has the event
        events = redis_client.xrange(stream_key, count=1)

        assert len(events) == 1
        event_id, event_data = events[0]

        # Verify event data (Redis returns strings, not bytes)
        assert event_data['event_type'] == 'completion'
        assert event_data['user_id'] == user_id
        assert event_data['generation_id'] == generation_id
        assert event_data['duration_ms'] == '3500'
        assert event_data['success'] == 'True'

    def test_record_generation_cancelled_writes_to_redis(
        self,
        metrics_service,
        redis_client,
        clean_redis_stream
    ):
        """Test that record_generation_cancelled writes to Redis Stream."""
        stream_key = clean_redis_stream
        user_id = str(uuid.uuid4())
        generation_id = str(uuid.uuid4())

        # Record a generation cancellation
        metrics_service.record_generation_cancelled(
            user_id=user_id,
            generation_id=generation_id
        )

        # Check Redis stream has the event
        events = redis_client.xrange(stream_key, count=1)

        assert len(events) == 1
        event_id, event_data = events[0]

        # Verify event data (Redis returns strings, not bytes)
        assert event_data['event_type'] == 'cancellation'
        assert event_data['user_id'] == user_id
        assert event_data['generation_id'] == generation_id

    def test_record_generation_failure_writes_error_details(
        self,
        metrics_service,
        redis_client,
        clean_redis_stream
    ):
        """Test that failures write error details to Redis."""
        stream_key = clean_redis_stream
        user_id = str(uuid.uuid4())
        generation_id = str(uuid.uuid4())

        # Record a failed generation (duration in seconds)
        metrics_service.record_generation_completion(
            user_id=user_id,
            duration=15.0,  # 15 seconds = 15000 ms
            success=False,
            error_type="timeout",
            generation_id=generation_id
        )

        # Check Redis stream has the event with error details
        events = redis_client.xrange(stream_key, count=1)

        assert len(events) == 1
        event_id, event_data = events[0]

        # Verify error details (Redis returns strings, not bytes)
        assert event_data['success'] == 'False'
        assert event_data['error_type'] == 'timeout'
        # Note: error_message is not included in MetricsService Redis writes

    def test_redis_write_performance_overhead(
        self,
        metrics_service,
        redis_client,
        clean_redis_stream
    ):
        """Test that Redis writes have < 1ms overhead."""
        user_id = str(uuid.uuid4())

        # Measure time for 100 writes
        start_time = time.time()

        for i in range(100):
            metrics_service.record_generation_request(
                user_id=user_id,
                generation_type="standard",
                generation_id=str(uuid.uuid4())
            )

        elapsed_ms = (time.time() - start_time) * 1000
        avg_overhead_ms = elapsed_ms / 100

        # Average overhead should be < 1ms per write
        assert avg_overhead_ms < 1.0, f"Redis write overhead ({avg_overhead_ms:.2f}ms) exceeds 1ms target"

    def test_redis_unavailable_does_not_crash(self, metrics_service):
        """Test that service handles Redis unavailability gracefully."""
        user_id = str(uuid.uuid4())

        # Mock Redis client to raise exception
        with patch('genonaut.api.services.metrics_service.get_redis_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.xadd.side_effect = Exception("Redis connection failed")
            mock_get_client.return_value = mock_client

            # Should not crash even if Redis is unavailable
            try:
                metrics_service.record_generation_request(
                    user_id=user_id,
                    generation_type="standard"
                )
            except Exception as e:
                pytest.fail(f"MetricsService should not crash when Redis is unavailable: {e}")

    def test_multiple_events_preserve_order(
        self,
        metrics_service,
        redis_client,
        clean_redis_stream
    ):
        """Test that multiple events maintain order in Redis Stream."""
        stream_key = clean_redis_stream
        user_id = str(uuid.uuid4())
        generation_id = str(uuid.uuid4())

        # Record request, completion, and cancellation in sequence
        metrics_service.record_generation_request(
            user_id=user_id,
            generation_id=generation_id,
            generation_type="standard"
        )

        time.sleep(0.001)  # Small delay to ensure timestamp ordering

        metrics_service.record_generation_completion(
            user_id=user_id,
            generation_id=generation_id,
            duration=3.5,  # 3.5 seconds
            success=True
        )

        # Get all events from stream
        events = redis_client.xrange(stream_key)

        # Should have 2 events in order (Redis returns strings, not bytes)
        assert len(events) == 2
        assert events[0][1]['event_type'] == 'request'
        assert events[1][1]['event_type'] == 'completion'

    def test_redis_stream_trimming(
        self,
        metrics_service,
        redis_client,
        clean_redis_stream
    ):
        """Test that Redis stream is trimmed to prevent unbounded growth."""
        stream_key = clean_redis_stream
        user_id = str(uuid.uuid4())

        # The stream should be trimmed to maxlen=100000 (approximate)
        # We can't easily test the full 100K limit, but we can verify
        # that the XADD command includes maxlen parameter

        with patch.object(redis_client, 'xadd', wraps=redis_client.xadd) as mock_xadd:
            metrics_service.record_generation_request(
                user_id=user_id,
                generation_type="standard"
            )

            # Verify xadd was called with maxlen parameter
            assert mock_xadd.called
            call_kwargs = mock_xadd.call_args[1]
            assert 'maxlen' in call_kwargs
            assert call_kwargs['maxlen'] == 100000
            assert call_kwargs.get('approximate') == True

    def test_backward_compatibility_without_generation_id(
        self,
        metrics_service,
        redis_client,
        clean_redis_stream
    ):
        """Test that methods work without generation_id parameter (backward compatibility)."""
        stream_key = clean_redis_stream
        user_id = str(uuid.uuid4())

        # Call without generation_id (old API)
        metrics_service.record_generation_request(
            user_id=user_id,
            generation_type="standard"
        )

        # Should still write to Redis
        events = redis_client.xrange(stream_key, count=1)
        assert len(events) == 1

        # generation_id should be empty string or None (Redis returns strings, not bytes)
        event_data = events[0][1]
        generation_id_value = event_data.get('generation_id', '')
        assert generation_id_value in ['', 'None']

    def test_in_memory_tracking_still_works(self, metrics_service):
        """Test that in-memory tracking still works alongside Redis writes."""
        user_id = str(uuid.uuid4())

        # Get initial stats
        initial_stats = metrics_service.get_metrics_summary()
        initial_requests = initial_stats["generation_metrics"]["total_requests"]

        # Record a generation request
        metrics_service.record_generation_request(
            user_id=user_id,
            generation_type="standard"
        )

        # In-memory stats should be updated
        updated_stats = metrics_service.get_metrics_summary()
        updated_requests = updated_stats["generation_metrics"]["total_requests"]

        assert updated_requests == initial_requests + 1
