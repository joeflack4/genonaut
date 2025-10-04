"""Unit tests for Redis pub/sub functionality."""

import json
from unittest.mock import Mock, patch, MagicMock
import pytest

from genonaut.worker.pubsub import (
    get_job_channel,
    publish_job_update,
    publish_job_started,
    publish_job_processing,
    publish_job_completed,
    publish_job_failed,
)


class TestPubSubFunctions:
    """Test pub/sub utility functions."""

    @patch('genonaut.worker.pubsub.settings')
    def test_get_job_channel(self, mock_settings):
        """Test job channel name generation with namespace."""
        mock_settings.redis_ns = "genonaut_test"

        channel = get_job_channel(123)

        assert channel == "genonaut_test:job:123"

    @patch('genonaut.worker.pubsub.get_redis_client')
    def test_publish_job_update(self, mock_get_client):
        """Test publishing a job update to Redis."""
        mock_client = Mock()
        mock_client.publish.return_value = 2  # 2 subscribers
        mock_get_client.return_value = mock_client

        publish_job_update(123, "processing", {"progress": 50})

        # Verify publish was called
        mock_client.publish.assert_called_once()

        # Verify channel and message
        call_args = mock_client.publish.call_args
        channel = call_args[0][0]
        message_json = call_args[0][1]

        assert "job:123" in channel
        message = json.loads(message_json)
        assert message["job_id"] == 123
        assert message["status"] == "processing"
        assert message["progress"] == 50

    @patch('genonaut.worker.pubsub.get_redis_client')
    def test_publish_job_update_handles_redis_errors(self, mock_get_client):
        """Test that Redis errors don't crash the publisher."""
        mock_client = Mock()
        mock_client.publish.side_effect = Exception("Redis connection failed")
        mock_get_client.return_value = mock_client

        # Should not raise exception
        publish_job_update(123, "started")

        # Verify publish was attempted
        mock_client.publish.assert_called_once()

    @patch('genonaut.worker.pubsub.publish_job_update')
    def test_publish_job_started(self, mock_publish):
        """Test publishing 'started' status."""
        publish_job_started(123)

        mock_publish.assert_called_once_with(123, "started")

    @patch('genonaut.worker.pubsub.publish_job_update')
    def test_publish_job_processing_without_progress(self, mock_publish):
        """Test publishing 'processing' status without progress."""
        publish_job_processing(123)

        mock_publish.assert_called_once_with(123, "processing", {})

    @patch('genonaut.worker.pubsub.publish_job_update')
    def test_publish_job_processing_with_progress(self, mock_publish):
        """Test publishing 'processing' status with progress."""
        publish_job_processing(123, progress=75.5)

        mock_publish.assert_called_once_with(123, "processing", {"progress": 75.5})

    @patch('genonaut.worker.pubsub.publish_job_update')
    def test_publish_job_completed_minimal(self, mock_publish):
        """Test publishing 'completed' status with minimal data."""
        publish_job_completed(123)

        mock_publish.assert_called_once_with(123, "completed", {})

    @patch('genonaut.worker.pubsub.publish_job_update')
    def test_publish_job_completed_full(self, mock_publish):
        """Test publishing 'completed' status with all data."""
        publish_job_completed(
            123,
            content_id=456,
            output_paths=["/path/to/image1.png", "/path/to/image2.png"]
        )

        expected_data = {
            "content_id": 456,
            "output_paths": ["/path/to/image1.png", "/path/to/image2.png"]
        }
        mock_publish.assert_called_once_with(123, "completed", expected_data)

    @patch('genonaut.worker.pubsub.publish_job_update')
    def test_publish_job_failed(self, mock_publish):
        """Test publishing 'failed' status with error message."""
        publish_job_failed(123, error="Connection timeout")

        mock_publish.assert_called_once_with(123, "failed", {"error": "Connection timeout"})

    @patch('genonaut.worker.pubsub.get_redis_client')
    def test_message_format(self, mock_get_client):
        """Test that published messages have correct JSON format."""
        mock_client = Mock()
        mock_client.publish.return_value = 1
        mock_get_client.return_value = mock_client

        publish_job_update(999, "completed", {"content_id": 888, "output_paths": ["file.png"]})

        # Parse the published message
        call_args = mock_client.publish.call_args
        message_json = call_args[0][1]
        message = json.loads(message_json)

        # Verify structure
        assert isinstance(message, dict)
        assert "job_id" in message
        assert "status" in message
        assert "timestamp" in message
        assert "content_id" in message
        assert "output_paths" in message

        # Verify values
        assert message["job_id"] == 999
        assert message["status"] == "completed"
        assert message["content_id"] == 888
        assert message["output_paths"] == ["file.png"]
