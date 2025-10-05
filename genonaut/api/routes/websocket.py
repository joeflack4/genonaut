"""WebSocket endpoints for real-time job status updates.

This module provides WebSocket endpoints that clients can connect to for
receiving real-time updates about generation job progress.
"""

import json
import logging
import asyncio
from typing import Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

try:
    import redis.asyncio as aioredis  # type: ignore
except ImportError:  # pragma: no cover - optional dependency for real-time features
    aioredis = None  # type: ignore

from genonaut.api.config import get_settings
from genonaut.worker.pubsub import get_job_channel

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/ws", tags=["websocket"])


async def get_async_redis_client() -> Any:
    """Get an async Redis client instance.

    Returns:
        Async Redis client configured with the current environment's URL
    """
    if aioredis is None:
        raise RuntimeError("redis package with asyncio support is required for WebSocket pubsub functionality.")

    return await aioredis.from_url(settings.redis_url, decode_responses=True)


@router.websocket("/jobs/{job_id}")
async def job_status_websocket(
    websocket: WebSocket,
    job_id: int
):
    """WebSocket endpoint for real-time job status updates.

    Clients can connect to this endpoint to receive real-time updates about
    a specific generation job's progress.

    Args:
        websocket: WebSocket connection
        job_id: The generation job ID to monitor

    Message Format:
        {
            "job_id": 123,
            "status": "processing",
            "progress": 50,
            "timestamp": "2025-10-03T12:00:00Z"
        }

    Example client usage:
        ```javascript
        const ws = new WebSocket('ws://localhost:8001/ws/jobs/123');
        ws.onmessage = (event) => {
            const update = JSON.parse(event.data);
            console.log('Job status:', update.status);
        };
        ```
    """
    await websocket.accept()
    logger.info(f"WebSocket client connected for job {job_id}")

    redis_client: Optional[Any] = None
    pubsub: Optional[Any] = None

    try:
        # Connect to Redis and subscribe to job channel
        redis_client = await get_async_redis_client()
        pubsub = redis_client.pubsub()
        channel = get_job_channel(job_id)

        await pubsub.subscribe(channel)
        logger.info(f"Subscribed to Redis channel: {channel}")

        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection",
            "job_id": job_id,
            "status": "connected"
        })

        # Listen for Redis pub/sub messages and relay to WebSocket
        async def redis_listener():
            """Background task to listen for Redis messages."""
            try:
                async for message in pubsub.listen():
                    if message['type'] == 'message':
                        data = message['data']
                        logger.debug(f"Received Redis message for job {job_id}: {data}")

                        # Parse and relay the message
                        try:
                            if isinstance(data, str):
                                payload = json.loads(data)
                            else:
                                payload = data

                            await websocket.send_json(payload)
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse Redis message: {e}")
                        except Exception as e:
                            logger.error(f"Failed to send WebSocket message: {e}")
                            break
            except asyncio.CancelledError:
                logger.info(f"Redis listener cancelled for job {job_id}")
                raise
            except Exception as e:
                logger.error(f"Error in Redis listener for job {job_id}: {e}", exc_info=True)

        # Start the Redis listener task
        listener_task = asyncio.create_task(redis_listener())

        try:
            # Keep connection alive and handle client messages (if any)
            while True:
                # Wait for client messages (currently we just use this to detect disconnection)
                data = await websocket.receive_text()
                logger.debug(f"Received client message for job {job_id}: {data}")

                # Optionally handle client commands here (e.g., unsubscribe, ping)
                try:
                    client_msg = json.loads(data)
                    if client_msg.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                except json.JSONDecodeError:
                    pass  # Ignore malformed messages

        except WebSocketDisconnect:
            logger.info(f"WebSocket client disconnected for job {job_id}")
            listener_task.cancel()
            try:
                await listener_task
            except asyncio.CancelledError:
                pass

    except Exception as e:
        logger.error(f"Error in WebSocket connection for job {job_id}: {e}", exc_info=True)

    finally:
        # Clean up Redis subscription
        if pubsub:
            try:
                await pubsub.unsubscribe()
                await pubsub.close()
                logger.info(f"Unsubscribed from Redis channel for job {job_id}")
            except Exception as e:
                logger.error(f"Error unsubscribing from Redis: {e}")

        if redis_client:
            try:
                await redis_client.close()
            except Exception as e:
                logger.error(f"Error closing Redis client: {e}")


@router.websocket("/jobs")
async def multi_job_status_websocket(
    websocket: WebSocket,
    job_ids: str = Query(..., description="Comma-separated list of job IDs to monitor")
):
    """WebSocket endpoint for monitoring multiple jobs simultaneously.

    Args:
        websocket: WebSocket connection
        job_ids: Comma-separated list of job IDs (e.g., "123,456,789")

    Example:
        ws://localhost:8001/ws/jobs?job_ids=123,456,789
    """
    await websocket.accept()

    try:
        # Parse job IDs
        ids = [int(id.strip()) for id in job_ids.split(",") if id.strip()]
        logger.info(f"WebSocket client connected for jobs: {ids}")

        if not ids:
            await websocket.send_json({"error": "No valid job IDs provided"})
            await websocket.close()
            return

        # Connect to Redis and subscribe to multiple channels
        redis_client = await get_async_redis_client()
        pubsub = redis_client.pubsub()

        channels = [get_job_channel(job_id) for job_id in ids]
        await pubsub.subscribe(*channels)
        logger.info(f"Subscribed to {len(channels)} Redis channels")

        # Send connection confirmation
        await websocket.send_json({
            "type": "connection",
            "job_ids": ids,
            "status": "connected"
        })

        # Listen for messages
        async def redis_listener():
            """Background task to listen for Redis messages."""
            try:
                async for message in pubsub.listen():
                    if message['type'] == 'message':
                        data = message['data']
                        try:
                            if isinstance(data, str):
                                payload = json.loads(data)
                            else:
                                payload = data
                            await websocket.send_json(payload)
                        except Exception as e:
                            logger.error(f"Failed to relay message: {e}")
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error(f"Error in multi-job Redis listener: {e}", exc_info=True)

        listener_task = asyncio.create_task(redis_listener())

        try:
            while True:
                data = await websocket.receive_text()
                logger.debug(f"Received client message: {data}")

                try:
                    client_msg = json.loads(data)
                    if client_msg.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                except json.JSONDecodeError:
                    pass

        except WebSocketDisconnect:
            logger.info(f"Multi-job WebSocket client disconnected")
            listener_task.cancel()
            try:
                await listener_task
            except asyncio.CancelledError:
                pass

    except Exception as e:
        logger.error(f"Error in multi-job WebSocket: {e}", exc_info=True)

    finally:
        if 'pubsub' in locals():
            try:
                await pubsub.unsubscribe()
                await pubsub.close()
            except Exception as e:
                logger.error(f"Error unsubscribing: {e}")

        if 'redis_client' in locals():
            try:
                await redis_client.close()
            except Exception as e:
                logger.error(f"Error closing Redis client: {e}")
