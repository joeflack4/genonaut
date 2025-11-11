"""Genonaut FastAPI application main module."""

import faulthandler
import logging
import signal
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from genonaut.api.config import get_settings
from genonaut.api.dependencies import get_database_session
from genonaut.api.routes import content, content_auto, generation, interactions, recommendations, system, users, comfyui, images, tags, admin_flagged_content, websocket, notifications, checkpoint_models, lora_models, user_search_history, analytics, generation_analytics, bookmarks, bookmark_categories
from genonaut.api.context import build_request_context, reset_request_context, set_request_context
from genonaut.api.exceptions import StatementTimeoutError
from genonaut.api.middleware.route_analytics import RouteAnalyticsMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    settings = get_settings()

    if settings.enable_faulthandler:
        try:
            faulthandler.register(signal.SIGUSR1)
            logger.info("Faulthandler registered for SIGUSR1 signal - send kill -USR1 <pid> to dump stack traces")
        except Exception as e:
            logger.warning(f"Failed to register faulthandler: {e}")

    yield

    # Shutdown
    if settings.enable_faulthandler:
        try:
            faulthandler.unregister(signal.SIGUSR1)
        except Exception:
            pass


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Genonaut API",
        description="RESTful API for the Genonaut content recommendation system",
        version="1.0.0",
        debug=settings.api_debug,
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure this for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add route analytics middleware
    app.add_middleware(RouteAnalyticsMiddleware)

    @app.middleware("http")
    async def apply_request_context(request: Request, call_next):
        """Attach request metadata so downstream layers can reference it."""

        token = set_request_context(build_request_context(request))
        try:
            response = await call_next(request)
            return response
        finally:
            reset_request_context(token)

    @app.exception_handler(StatementTimeoutError)
    async def handle_statement_timeout_error(request: Request, exc: StatementTimeoutError) -> JSONResponse:
        """Return a consistent error payload whenever a DB statement times out."""

        response_body = {
            "error_type": "statement_timeout",
            "message": "The operation took too long to complete. Please try again or refine your request.",
            "timeout_duration": exc.timeout,
        }

        details = {}

        if exc.context:
            details["context"] = exc.context

        if exc.query:
            details["query"] = exc.query

        if details:
            response_body["details"] = details

        return JSONResponse(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            content=response_body,
        )
    
    # Include API routes
    app.include_router(users.router)
    app.include_router(content.router)
    app.include_router(content_auto.router)
    app.include_router(interactions.router)
    app.include_router(recommendations.router)
    app.include_router(generation.router)
    app.include_router(comfyui.router)
    app.include_router(images.router)
    app.include_router(tags.router)
    app.include_router(bookmarks.router)
    app.include_router(bookmark_categories.router)
    app.include_router(admin_flagged_content.router)
    app.include_router(notifications.router)
    app.include_router(checkpoint_models.router)
    app.include_router(lora_models.router)
    app.include_router(user_search_history.router)
    app.include_router(analytics.router)
    app.include_router(generation_analytics.router)
    app.include_router(system.router)
    app.include_router(websocket.router)
    
    # Legacy health check endpoint (for backwards compatibility)
    @app.get("/health")
    async def legacy_health_check():
        """Legacy health check endpoint."""
        return {"status": "healthy", "message": "Use /api/v1/health for detailed health check"}
    
    # Root endpoint
    @app.get("/")
    async def root(db: Session = Depends(get_database_session)):
        """Root endpoint."""
        try:
            # Get database name
            db_name_result = db.execute(text("SELECT current_database()")).fetchone()
            db_name = db_name_result[0] if db_name_result else "unknown"
        except Exception:
            db_name = "unknown"

        return {
            "message": "Welcome to Genonaut API",
            "version": "1.0.0",
            "database": db_name,
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/api/v1/health",
            "database_info": "/api/v1/databases",
            "global_stats": "/api/v1/stats/global",
            "tag_hierarchy": "/api/v1/tags/hierarchy"
        }
    
    return app

# Create the app instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "genonaut.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug,
    )
