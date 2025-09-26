"""Security middleware for API endpoints."""

import logging
import time
from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from genonaut.api.services.security_service import get_security_service
from genonaut.api.services.metrics_service import get_metrics_service

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""

    def __init__(self, app, config: Optional[dict] = None):
        """Initialize security headers middleware.

        Args:
            app: FastAPI app instance
            config: Optional configuration
        """
        super().__init__(app)
        self.config = config or {}

        # Default security headers
        self.security_headers = {
            # Prevent XSS attacks
            'X-XSS-Protection': '1; mode=block',

            # Prevent content type sniffing
            'X-Content-Type-Options': 'nosniff',

            # Prevent clickjacking
            'X-Frame-Options': 'DENY',

            # HTTPS enforcement (if enabled)
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',

            # Content Security Policy (restrictive default)
            'Content-Security-Policy': (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            ),

            # Referrer policy
            'Referrer-Policy': 'strict-origin-when-cross-origin',

            # Permissions policy
            'Permissions-Policy': (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "gyroscope=(), "
                "speaker=()"
            )
        }

        # Update with custom headers from config
        if 'security_headers' in self.config:
            self.security_headers.update(self.config['security_headers'])

    async def dispatch(self, request: Request, call_next):
        """Process request and add security headers to response.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response with security headers
        """
        try:
            # Process the request
            response = await call_next(request)

            # Add security headers
            for header, value in self.security_headers.items():
                response.headers[header] = value

            # Add cache control for API responses
            if request.url.path.startswith('/api/'):
                response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'

            return response

        except Exception as e:
            logger.error(f"Security middleware error: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error"},
                headers=self.security_headers
            )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests."""

    def __init__(self, app, config: Optional[dict] = None):
        """Initialize rate limiting middleware.

        Args:
            app: FastAPI app instance
            config: Optional configuration
        """
        super().__init__(app)
        self.config = config or {}
        self.security_service = get_security_service()
        self.metrics_service = get_metrics_service()

        # Endpoints that require rate limiting
        self.rate_limited_endpoints = {
            '/api/v1/comfyui/generate': 'generation_request',
            '/api/v1/comfyui/models/': 'model_list',
            # Add more endpoints as needed
        }

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response or rate limit error
        """
        # Get client information
        client_ip = self._get_client_ip(request)
        user_id = self._get_user_id(request)

        # Check if endpoint should be rate limited
        operation = self._get_operation_type(request.url.path, request.method)

        if operation:
            # Perform rate limit check
            is_allowed, message, retry_after = self.security_service.check_rate_limit(
                user_id or client_ip,
                operation,
                client_ip
            )

            if not is_allowed:
                # Track rate limit hit
                self.metrics_service.increment_counter(
                    "rate_limit_exceeded",
                    labels={"operation": operation, "ip": client_ip}
                )

                logger.warning(f"Rate limit exceeded for {client_ip} (user: {user_id}) on {operation}: {message}")

                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "message": message,
                        "retry_after": retry_after
                    },
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Remaining": "0"
                    }
                )

        # Track API request
        if request.url.path.startswith('/api/'):
            endpoint = self._normalize_endpoint(request.url.path)
            start_time = time.time()

            try:
                response = await call_next(request)
                duration = time.time() - start_time

                # Record metrics
                self.metrics_service.record_response_time(endpoint, duration)
                self.metrics_service.increment_counter(
                    "api_requests",
                    labels={"endpoint": endpoint, "method": request.method, "status": str(response.status_code)}
                )

                return response

            except Exception as e:
                duration = time.time() - start_time
                self.metrics_service.record_response_time(endpoint, duration)
                self.metrics_service.increment_counter(
                    "api_errors",
                    labels={"endpoint": endpoint, "method": request.method, "error": type(e).__name__}
                )
                raise
        else:
            return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request.

        Args:
            request: HTTP request

        Returns:
            Client IP address
        """
        # Check for forwarded headers
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()

        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip

        # Fall back to client host
        if request.client:
            return request.client.host

        return "unknown"

    def _get_user_id(self, request: Request) -> Optional[str]:
        """Get user ID from request (if authenticated).

        Args:
            request: HTTP request

        Returns:
            User ID if available
        """
        # This would depend on your authentication system
        # For now, return None as we don't have auth implemented
        return None

    def _get_operation_type(self, path: str, method: str) -> Optional[str]:
        """Determine operation type for rate limiting.

        Args:
            path: Request path
            method: HTTP method

        Returns:
            Operation type or None if not rate limited
        """
        # Check exact matches first
        if path in self.rate_limited_endpoints:
            return self.rate_limited_endpoints[path]

        # Check pattern matches
        if path.startswith('/api/v1/comfyui/') and method == 'POST':
            return 'generation_request'
        elif path.startswith('/api/v1/comfyui/models') and method == 'GET':
            return 'model_list'
        elif path.startswith('/api/'):
            return 'api_request'

        return None

    def _normalize_endpoint(self, path: str) -> str:
        """Normalize endpoint path for metrics.

        Args:
            path: Request path

        Returns:
            Normalized endpoint path
        """
        # Replace IDs with placeholder
        import re
        normalized = re.sub(r'/\d+', '/{id}', path)
        normalized = re.sub(r'/[a-f0-9-]{36}', '/{uuid}', normalized)  # UUID pattern
        return normalized


def get_cors_middleware_config() -> dict:
    """Get CORS middleware configuration.

    Returns:
        CORS configuration dictionary
    """
    # @question: What are your CORS requirements?
    return {
        "allow_origins": [
            "http://localhost:3000",   # React dev server
            "http://localhost:5173",   # Vite dev server
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            # Add production origins here
        ],
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        "allow_headers": [
            "Accept",
            "Accept-Language",
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "X-CSRF-Token"
        ],
        "expose_headers": [
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
            "Retry-After"
        ]
    }


def setup_security_middleware(app):
    """Set up security middleware for the FastAPI app.

    Args:
        app: FastAPI application instance
    """
    # Add CORS middleware
    cors_config = get_cors_middleware_config()
    app.add_middleware(
        CORSMiddleware,
        **cors_config
    )

    # Add rate limiting middleware
    app.add_middleware(RateLimitMiddleware)

    # Add security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)

    logger.info("Security middleware configured successfully")