"""
FastAPI application entry point for Wind Turbine Analytics API.

This module creates and configures the FastAPI application with:
- CORS middleware for frontend communication
- API routes for analysis workflows
- Health check endpoint
- Extended timeout configuration
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.logger_config import get_logger
from src.wind_turbine_analytics.api.routes import analyze_router, health_router, config_router
from src.wind_turbine_analytics.api.routes.upload import router as upload_router
from src.wind_turbine_analytics.api.routes.sessions import router as sessions_router

logger = get_logger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Wind Turbine Analytics API",
    description=(
        "REST API for triggering wind turbine analysis workflows (RunTest and SCADA). "
        "Returns interactive Plotly charts and data tables as JSON."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative frontend port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health_router)
app.include_router(upload_router)  # ZIP upload endpoint
app.include_router(sessions_router)  # Session management endpoints
app.include_router(analyze_router)
app.include_router(config_router)

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
