"""
FastAPI Main Application

Entry point for the Grist AI Assistant API.
"""

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import colorlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.models import settings
from app.api.routes import router
from app.middleware.error_handler import register_exception_handlers

# ============================================================================
# Logging Configuration
# ============================================================================


def setup_logging():
    """
    Configure colorful logging for better visual distinction.
    Uses LOG_LEVEL from centralized configuration.
    """
    # Create a color formatter
    formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(name)s%(reset)s %(message)s",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
    )

    # Configure root logger
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))

    # Set specific log levels for noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.INFO)


setup_logging()
logger = logging.getLogger(__name__)


# ============================================================================
# Application Lifecycle
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("🚀 Starting Grist AI Assistant API...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Log Level: {settings.log_level}")
    logger.info(f"LLM Model: {settings.openai_model}")
    logger.info(f"Grist Base URL: {settings.grist_base_url}")

    # TODO: Initialize database connections
    # TODO: Initialize Redis connection
    # TODO: Warm up LLM (optional pre-load)

    yield

    # Shutdown
    logger.info("🛑 Shutting down Grist AI Assistant API...")

    # TODO: Close database connections
    # TODO: Close Redis connection
    # TODO: Cleanup resources


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Grist AI Assistant API",
    description="AI-powered assistant for Grist documents using LangChain and OpenAI",
    version="0.1.0",
    lifespan=lifespan,
)

# ============================================================================
# Middleware
# ============================================================================

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# TODO: Add more middleware
# - Request ID middleware (for tracing)
# - Rate limiting middleware
# - Authentication middleware
# - Error handling middleware

# ============================================================================
# Routes
# ============================================================================

# API v1 routes with versioning prefix
app.include_router(router, prefix="/api/v1")

# Register exception handlers
register_exception_handlers(app)


# ============================================================================
# Serve Frontend (Production)
# ============================================================================

# Check if frontend static files exist (production mode)
static_dir = Path(__file__).parent.parent.parent / "static"
if static_dir.exists():
    logger.info(f"📦 Serving frontend from {static_dir}")
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="frontend")
else:
    logger.warning("⚠️  Frontend static files not found - API only mode")
    
    @app.get("/")
    async def root():
        """Root endpoint with API information (dev mode)."""
        return {
            "name": "Grist AI Assistant API",
            "version": "0.1.0",
            "environment": settings.environment,
            "model": settings.openai_model,
            "docs": "/docs",
            "health": "/api/v1/health",
            "chat": "/api/v1/chat",
        }


# ============================================================================
# Error Handlers
# ============================================================================

# TODO: Add custom error handlers
# - 404 handler with helpful messages
# - 500 handler with error tracking
# - Validation error handler with detailed feedback


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=(settings.environment == "development"),
        log_config=None,  # Use our custom logging
    )
