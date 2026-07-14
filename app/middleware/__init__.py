"""
Middleware package for SCONIA application.
"""
from .monitoring import (
    MonitoringMiddleware,
    RateLimitMiddleware, 
    SecurityHeadersMiddleware
)

def setup_middleware(app):
    """Setup all middleware for the FastAPI application."""
    # Add middleware in reverse order of execution
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(MonitoringMiddleware)
    
    return app

__all__ = [
    "MonitoringMiddleware",
    "RateLimitMiddleware", 
    "SecurityHeadersMiddleware",
    "setup_middleware"
]
