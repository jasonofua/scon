"""
Main FastAPI application for SCONIA.
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from app.middleware.monitoring import (
    MonitoringMiddleware, RateLimitMiddleware, SecurityHeadersMiddleware
)
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
import uuid

from app.config import settings
from app.database import init_db, close_db
from app.api import api_router
from app.middleware import setup_middleware
from app.services.cache import cache_service

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting SCONIA application...")
    try:
        # Initialize cache service
        await cache_service.initialize()
        
        # Only initialize database if not in production deployment mode
        skip_db_init = getattr(settings, "SKIP_DB_INIT", False)
        if not skip_db_init:
            await init_db()
            logger.info("Database initialized successfully")
        else:
            logger.info("Skipping database initialization (SKIP_DB_INIT=True)")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        # Don't raise in production, just log the error and continue
        logger.warning("Continuing without database initialization")

    logger.info("SCONIA application startup complete")
    yield

    # Shutdown
    logger.info("Shutting down SCONIA application...")
    try:
        await cache_service.close()
        await close_db()
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Supreme Court of Nigeria Information Assistant - AI-powered legal information system",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Setup middleware
setup_middleware(app)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=settings.allowed_methods,
    allow_headers=settings.allowed_headers,
)

# Trusted host middleware for production
if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[
            "sconia.gov.ng",
            "*.sconia.gov.ng",
            "*.onrender.com",   # Render deployments
            "localhost",
            "*.run.app",        # Google Cloud Run (legacy)
        ]
    )

# Add custom middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=getattr(settings, 'rate_limit_per_minute', 60))
app.add_middleware(MonitoringMiddleware)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to responses."""
    start_time = time.time()
    
    # Add request ID for tracking
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Request-ID"] = request_id
    
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "request_id": getattr(request.state, "request_id", None)
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "timestamp": time.time()
    }

# Startup health check endpoint for Cloud Run
@app.get("/startup")
async def startup_check():
    """Startup health check endpoint for Cloud Run."""
    return {"status": "ready"}


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with welcome message."""
    return {
        "message": "Welcome to SCONIA - Supreme Court of Nigeria Information Assistant",
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else "Documentation not available in production",
        "health": "/health"
    }


# Include API routes
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", settings.port))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
