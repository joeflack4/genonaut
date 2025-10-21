"""Performance timing middleware for debugging request performance."""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class PerformanceTimingMiddleware(BaseHTTPMiddleware):
    """Middleware to track detailed request timing breakdown."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log detailed timing information."""
        start_time = time.perf_counter()

        # Store timing markers in request state
        request.state.timing_markers = {
            'request_start': start_time,
        }

        response = await call_next(request)

        end_time = time.perf_counter()
        total_time = end_time - start_time

        # Log detailed timing for specific endpoints
        if '/api/v1/content/unified' in str(request.url.path):
            logger.info(
                f"[PERF] {request.method} {request.url.path} "
                f"total={total_time*1000:.2f}ms "
                f"query_params={dict(request.query_params)}"
            )

            # Log any custom timing markers set during request processing
            if hasattr(request.state, 'perf_timings'):
                timings_str = ' '.join([
                    f"{k}={v*1000:.2f}ms"
                    for k, v in request.state.perf_timings.items()
                ])
                logger.info(f"[PERF BREAKDOWN] {timings_str}")

        # Add timing header to response
        response.headers['X-Response-Time'] = f"{total_time*1000:.2f}ms"

        return response
