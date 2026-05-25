"""
FastAPI application entry point for Wind Turbine Analytics API.

This module creates and configures the FastAPI application with:
- CORS middleware for frontend communication
- API routes for analysis workflows
- Health check endpoint
- Extended timeout configuration
- Static file serving for frontend (production mode)
"""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.logger_config import get_logger
from src.wind_turbine_analytics.api.config import settings
from src.wind_turbine_analytics.api.routes import analyze_router, health_router, config_router
from src.wind_turbine_analytics.api.routes.upload import router as upload_router
from src.wind_turbine_analytics.api.routes.sessions import router as sessions_router

logger = get_logger(__name__)

# Create FastAPI application with centralized config
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS with settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(health_router)
app.include_router(upload_router)  # ZIP upload endpoint
app.include_router(sessions_router)  # Session management endpoints
app.include_router(analyze_router)
app.include_router(config_router)

# Serve frontend static files (production mode)
# Priority: static_frontend (Databricks) > frontend/dist (local)
project_root = Path(__file__).parent.parent.parent.parent
FRONTEND_BUILD_DIR = project_root / "static_frontend"
if not FRONTEND_BUILD_DIR.exists():
    FRONTEND_BUILD_DIR = project_root / "frontend" / "dist"

if FRONTEND_BUILD_DIR.exists():
    logger.debug(f"Frontend build directory found at {FRONTEND_BUILD_DIR}")

    # Mount static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=FRONTEND_BUILD_DIR / "assets"), name="assets")

    # Catch-all route to serve index.html for React Router
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """
        Serve React frontend for all non-API routes.

        This allows React Router to handle client-side routing.
        API routes (prefixed with /api or registered above) are handled first.
        """
        # If path starts with api/, health, or docs, let FastAPI handle it
        if full_path.startswith(("api/", "health", "docs", "redoc", "openapi.json")):
            raise HTTPException(status_code=404, detail="API endpoint not found")

        # Serve index.html for all other routes (React Router will handle them)
        index_file = FRONTEND_BUILD_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)

        raise HTTPException(status_code=404, detail="Frontend not built")
else:
    logger.warning(f"Frontend build directory not found at {FRONTEND_BUILD_DIR}. Run 'npm run build' in frontend/")

logger.debug("FastAPI application initialized successfully")


@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    logger.debug("=" * 60)
    logger.debug("Wind Turbine Analytics API starting...")
    logger.debug("API Documentation: http://localhost:8000/docs")
    logger.debug("Health Check: http://localhost:8000/health")
    logger.debug("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown information."""
    logger.debug("Wind Turbine Analytics API shutting down...")
