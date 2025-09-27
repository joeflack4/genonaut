"""Genonaut FastAPI application main module."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from genonaut.api.config import get_settings
from genonaut.api.routes import content, content_auto, generation, interactions, recommendations, system, users, comfyui, images, tags

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="Genonaut API",
        description="RESTful API for the Genonaut content recommendation system",
        version="1.0.0",
        debug=settings.api_debug,
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure this for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
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
    app.include_router(system.router)
    
    # Legacy health check endpoint (for backwards compatibility)
    @app.get("/health")
    async def legacy_health_check():
        """Legacy health check endpoint."""
        return {"status": "healthy", "message": "Use /api/v1/health for detailed health check"}
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": "Welcome to Genonaut API",
            "version": "1.0.0",
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
