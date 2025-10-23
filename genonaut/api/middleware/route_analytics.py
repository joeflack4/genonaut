"""Middleware for capturing route analytics data.

This middleware tracks all API requests and writes analytics data to Redis Streams
for later batch processing into PostgreSQL. Data includes:
- Route path and HTTP method
- User ID (if available)
- Request/response timing
- Status codes and error types
- Request/response sizes
- Query parameters (both raw and normalized)

The analytics data is used for cache planning and performance monitoring.
"""

import json
import logging
import time
from typing import Dict, Optional, Any
from urllib.parse import urlencode, parse_qs, urlparse

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from genonaut.api.config import get_settings
from genonaut.worker.pubsub import get_redis_client

logger = logging.getLogger(__name__)


def normalize_query_params(query_string: str) -> Dict[str, Any]:
    """Normalize query parameters for cache analysis.

    Removes variable pagination parameters (page, offset, limit, cursor)
    while preserving filtering/sorting parameters that define distinct query patterns.

    Args:
        query_string: Raw query string from request

    Returns:
        Dictionary of normalized query parameters (pagination params excluded)

    Example:
        >>> normalize_query_params("page=2&page_size=10&sort=created_at")
        {"page_size": "10", "sort": "created_at"}
    """
    # Parameters to exclude from normalization (vary within same pattern)
    variable_params = {'page', 'offset', 'limit', 'cursor'}

    if not query_string:
        return {}

    # Parse query string
    parsed = parse_qs(query_string, keep_blank_values=True)

    # Remove variable params and flatten single values
    normalized = {}
    for key, values in parsed.items():
        if key not in variable_params:
            # Take first value if multiple (most common case)
            normalized[key] = values[0] if len(values) == 1 else values

    return normalized


def get_user_id_from_request(request: Request) -> Optional[str]:
    """Extract user ID from request if available.

    Args:
        request: FastAPI request object

    Returns:
        User ID string or None
    """
    # TODO: Extract from auth token/session when auth is implemented
    # For now, check if user_id is in request state or headers
    if hasattr(request.state, 'user_id'):
        return str(request.state.user_id)

    # Check for user_id in headers (for testing)
    user_id = request.headers.get('X-User-ID')
    if user_id:
        return user_id

    return None


def get_error_type_from_status(status_code: int) -> Optional[str]:
    """Categorize error type from HTTP status code.

    Args:
        status_code: HTTP status code

    Returns:
        Error category string or None for successful responses
    """
    if status_code >= 500:
        return 'server_error'
    elif status_code >= 400:
        return 'client_error'
    return None


class RouteAnalyticsMiddleware(BaseHTTPMiddleware):
    """Middleware to capture route analytics for all API requests.

    Writes analytics data to Redis Streams for background processing.
    Target overhead: < 1ms per request.
    """

    def __init__(self, app, config: Optional[dict] = None):
        """Initialize route analytics middleware.

        Args:
            app: FastAPI app instance
            config: Optional configuration
        """
        super().__init__(app)
        self.config = config or {}
        self.settings = get_settings()

        # Only track API routes
        self.track_path_prefix = '/api/'

        # Redis Stream key for route analytics
        self.stream_key = f"{self.settings.redis_ns}:route_analytics:stream"

        # Disable analytics if Redis is not available (test mode)
        self.enabled = True
        try:
            # Test Redis connection
            client = get_redis_client()
            client.ping()
        except Exception as e:
            logger.warning(f"Route analytics disabled - Redis unavailable: {e}")
            self.enabled = False

    async def dispatch(self, request: Request, call_next):
        """Process request and capture analytics data.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response from downstream handlers
        """
        # Skip non-API routes
        if not request.url.path.startswith(self.track_path_prefix):
            return await call_next(request)

        # Skip if analytics disabled
        if not self.enabled:
            return await call_next(request)

        # Capture request start time
        start_time = time.time()
        request_size = request.headers.get('Content-Length', 0)
        try:
            request_size = int(request_size)
        except (ValueError, TypeError):
            request_size = 0

        # Process request
        response = None
        error_occurred = False
        status_code = 500  # Default to server error if something goes wrong

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response

        except Exception as e:
            error_occurred = True
            logger.error(f"Error processing request {request.url.path}: {e}")
            raise

        finally:
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Get response size if available
            response_size = 0
            if response and hasattr(response, 'headers'):
                content_length = response.headers.get('Content-Length', 0)
                try:
                    response_size = int(content_length)
                except (ValueError, TypeError):
                    response_size = 0

            # Write analytics data to Redis (async, non-blocking)
            try:
                self._write_analytics_async(
                    request=request,
                    duration_ms=duration_ms,
                    status_code=status_code,
                    request_size_bytes=request_size,
                    response_size_bytes=response_size,
                    error_occurred=error_occurred
                )
            except Exception as e:
                # Log error but don't fail the request
                logger.error(f"Failed to write route analytics: {e}")

    def _write_analytics_async(
        self,
        request: Request,
        duration_ms: int,
        status_code: int,
        request_size_bytes: int,
        response_size_bytes: int,
        error_occurred: bool
    ) -> None:
        """Write analytics data to Redis Stream.

        This should be fast (< 1ms) since Redis writes are in-memory.

        Args:
            request: FastAPI request object
            duration_ms: Request duration in milliseconds
            status_code: HTTP status code
            request_size_bytes: Request payload size
            response_size_bytes: Response payload size
            error_occurred: Whether an error occurred during processing
        """
        try:
            # Extract route information
            base_route = request.url.path
            method = request.method
            query_string = request.url.query or ""

            # Parse and normalize query params
            query_params = dict(parse_qs(query_string, keep_blank_values=True))
            # Flatten single values for cleaner storage
            query_params_flat = {
                k: v[0] if len(v) == 1 else v
                for k, v in query_params.items()
            }

            query_params_normalized = normalize_query_params(query_string)

            # Get user ID if available
            user_id = get_user_id_from_request(request)

            # Determine error type
            error_type = get_error_type_from_status(status_code)

            # Build analytics event data
            event_data = {
                'route': base_route,
                'method': method,
                'user_id': user_id or '',
                'timestamp': time.time(),
                'duration_ms': str(duration_ms),
                'status_code': str(status_code),
                'query_params': json.dumps(query_params_flat),
                'query_params_normalized': json.dumps(query_params_normalized),
                'request_size_bytes': str(request_size_bytes),
                'response_size_bytes': str(response_size_bytes),
                'error_type': error_type or '',
                'cache_status': '',  # Future: track cache hit/miss
            }

            # Write to Redis Stream
            client = get_redis_client()

            # XADD returns the ID of the added entry
            entry_id = client.xadd(
                self.stream_key,
                event_data,
                maxlen=100000,  # Keep last 100K entries (auto-trim old data)
                approximate=True  # More efficient trimming
            )

            logger.debug(f"Route analytics captured: {method} {base_route} ({duration_ms}ms) -> Redis entry {entry_id}")

        except Exception as e:
            # Log but don't fail the request
            logger.error(f"Failed to write analytics to Redis: {e}", exc_info=True)
