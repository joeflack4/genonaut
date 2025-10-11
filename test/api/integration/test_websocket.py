"""Integration tests for WebSocket job status endpoints.

Note: These tests are simplified because WebSocket testing with TestClient
has limitations. Full WebSocket functionality should be tested manually or
with a running server + WebSocket client library.
"""

import json
import asyncio
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, Mock, patch

from genonaut.api.main import create_app


@pytest.fixture
def client():
    """Create a test client."""
    app = create_app()
    return TestClient(app)


class TestWebSocketEndpoint:
    """Test WebSocket endpoints for job status updates."""

    @pytest.mark.skip(reason="WEBSOCKET-TESTCLIENT-LIMITATION: WebSocket tests timeout due to limitations in FastAPI's TestClient")
    def test_websocket_connection_established(self, client):
        """Test that WebSocket connection can be established."""

        async def empty_async_iterator():
            """Empty async iterator for listen mock."""
            if False:
                yield  # Make this a generator but never actually yield

        with patch('genonaut.api.routes.websocket.get_async_redis_client') as mock_redis:
            # Mock Redis client and pubsub
            mock_pubsub = AsyncMock()
            mock_pubsub.subscribe = AsyncMock()
            mock_pubsub.listen = AsyncMock(return_value=empty_async_iterator())
            mock_pubsub.unsubscribe = AsyncMock()
            mock_pubsub.close = AsyncMock()

            mock_client_instance = AsyncMock()
            mock_client_instance.pubsub.return_value = mock_pubsub
            mock_client_instance.close = AsyncMock()

            mock_redis.return_value = mock_client_instance

            # Connect to WebSocket
            with client.websocket_connect("/ws/jobs/123") as websocket:
                # Should receive connection confirmation
                data = websocket.receive_json()

                assert data["type"] == "connection"
                assert data["job_id"] == 123
                assert data["status"] == "connected"

    @pytest.mark.skip(reason="WEBSOCKET-TESTCLIENT-LIMITATION: WebSocket tests timeout due to limitations in FastAPI's TestClient")
    def test_websocket_relays_redis_messages(self, client):
        """Test that WebSocket relays Redis pub/sub messages to client."""

        async def mock_redis_messages():
            """Simulate Redis pub/sub messages."""
            # Yield a few test messages
            yield {
                'type': 'subscribe',
                'channel': 'genonaut_test:job:123'
            }
            yield {
                'type': 'message',
                'data': json.dumps({
                    "job_id": 123,
                    "status": "processing",
                    "progress": 50
                })
            }
            yield {
                'type': 'message',
                'data': json.dumps({
                    "job_id": 123,
                    "status": "completed",
                    "content_id": 456
                })
            }

        with patch('genonaut.api.routes.websocket.get_async_redis_client') as mock_redis:
            # Mock Redis client and pubsub
            mock_pubsub = AsyncMock()
            mock_pubsub.subscribe = AsyncMock()
            mock_pubsub.listen = AsyncMock(return_value=mock_redis_messages())
            mock_pubsub.unsubscribe = AsyncMock()
            mock_pubsub.close = AsyncMock()

            mock_client_instance = AsyncMock()
            mock_client_instance.pubsub.return_value = mock_pubsub
            mock_client_instance.close = AsyncMock()

            mock_redis.return_value = mock_client_instance

            # Connect to WebSocket
            with client.websocket_connect("/ws/jobs/123") as websocket:
                # Receive connection confirmation
                connection_msg = websocket.receive_json()
                assert connection_msg["type"] == "connection"

                # Receive first job update (processing)
                update1 = websocket.receive_json(timeout=2)
                assert update1["job_id"] == 123
                assert update1["status"] == "processing"
                assert update1["progress"] == 50

                # Receive second job update (completed)
                update2 = websocket.receive_json(timeout=2)
                assert update2["job_id"] == 123
                assert update2["status"] == "completed"
                assert update2["content_id"] == 456

    @pytest.mark.skip(reason="WEBSOCKET-TESTCLIENT-LIMITATION: WebSocket tests timeout due to limitations in FastAPI's TestClient")
    def test_websocket_handles_client_disconnect(self, client):
        """Test that WebSocket properly cleans up on client disconnect."""

        async def empty_async_iterator():
            """Empty async iterator for listen mock."""
            if False:
                yield  # Make this a generator but never actually yield

        with patch('genonaut.api.routes.websocket.get_async_redis_client') as mock_redis:
            mock_pubsub = AsyncMock()
            mock_pubsub.subscribe = AsyncMock()
            mock_pubsub.listen = AsyncMock(return_value=empty_async_iterator())
            mock_pubsub.unsubscribe = AsyncMock()
            mock_pubsub.close = AsyncMock()

            mock_client_instance = AsyncMock()
            mock_client_instance.pubsub.return_value = mock_pubsub
            mock_client_instance.close = AsyncMock()

            mock_redis.return_value = mock_client_instance

            # Connect and immediately disconnect
            with client.websocket_connect("/ws/jobs/123") as websocket:
                websocket.receive_json()  # Get connection confirmation

            # Verify cleanup was called
            mock_pubsub.unsubscribe.assert_called_once()
            mock_pubsub.close.assert_called_once()
            mock_client_instance.close.assert_called_once()

    @pytest.mark.skip(reason="WEBSOCKET-TESTCLIENT-LIMITATION: WebSocket tests timeout due to limitations in FastAPI's TestClient")
    def test_websocket_ping_pong(self, client):
        """Test that WebSocket responds to ping messages."""

        async def mock_redis_messages():
            """Empty message stream that never yields."""
            if False:
                yield  # Make this a generator but never actually yield

        with patch('genonaut.api.routes.websocket.get_async_redis_client') as mock_redis:
            mock_pubsub = AsyncMock()
            mock_pubsub.subscribe = AsyncMock()
            mock_pubsub.listen = AsyncMock(return_value=mock_redis_messages())
            mock_pubsub.unsubscribe = AsyncMock()
            mock_pubsub.close = AsyncMock()

            mock_client_instance = AsyncMock()
            mock_client_instance.pubsub.return_value = mock_pubsub
            mock_client_instance.close = AsyncMock()

            mock_redis.return_value = mock_client_instance

            with client.websocket_connect("/ws/jobs/123") as websocket:
                # Get connection confirmation
                websocket.receive_json()

                # Send ping
                websocket.send_json({"type": "ping"})

                # Should receive pong
                response = websocket.receive_json(timeout=2)
                assert response["type"] == "pong"


class TestMultiJobWebSocket:
    """Test multi-job WebSocket endpoint."""

    @pytest.mark.skip(reason="WEBSOCKET-TESTCLIENT-LIMITATION: WebSocket tests timeout due to limitations in FastAPI's TestClient")
    def test_multi_job_websocket_connection(self, client):
        """Test connecting to multiple jobs via query parameter."""

        async def mock_redis_messages():
            """Empty message stream."""
            return
            yield

        with patch('genonaut.api.routes.websocket.get_async_redis_client') as mock_redis:
            mock_pubsub = AsyncMock()
            mock_pubsub.subscribe = AsyncMock()
            mock_pubsub.listen = AsyncMock(return_value=mock_redis_messages())
            mock_pubsub.unsubscribe = AsyncMock()
            mock_pubsub.close = AsyncMock()

            mock_client_instance = AsyncMock()
            mock_client_instance.pubsub.return_value = mock_pubsub
            mock_client_instance.close = AsyncMock()

            mock_redis.return_value = mock_client_instance

            # Connect to multiple jobs
            with client.websocket_connect("/ws/jobs?job_ids=123,456,789") as websocket:
                # Should receive connection confirmation with all job IDs
                data = websocket.receive_json()

                assert data["type"] == "connection"
                assert set(data["job_ids"]) == {123, 456, 789}
                assert data["status"] == "connected"

                # Verify subscribed to all channels
                mock_pubsub.subscribe.assert_called_once()
                call_args = mock_pubsub.subscribe.call_args
                channels = call_args[0]
                assert len(channels) == 3
                assert any("job:123" in ch for ch in channels)
                assert any("job:456" in ch for ch in channels)
                assert any("job:789" in ch for ch in channels)

    @pytest.mark.skip(reason="WEBSOCKET-TESTCLIENT-LIMITATION: WebSocket tests timeout due to limitations in FastAPI's TestClient")
    def test_multi_job_websocket_empty_ids(self, client):
        """Test multi-job WebSocket with empty job_ids."""

        async def mock_redis_messages():
            if False:
                yield  # Make this a generator but never actually yield

        with patch('genonaut.api.routes.websocket.get_async_redis_client') as mock_redis:
            mock_pubsub = AsyncMock()
            mock_client_instance = AsyncMock()
            mock_client_instance.pubsub.return_value = mock_pubsub
            mock_redis.return_value = mock_client_instance

            # Connect with empty job IDs
            with client.websocket_connect("/ws/jobs?job_ids=") as websocket:
                # Should receive error
                data = websocket.receive_json()
                assert "error" in data
