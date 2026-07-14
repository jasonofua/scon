"""
Custom middleware for SCONIA application.
"""
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import time
import logging
from typing import Callable
import redis
from app.config import settings

logger = logging.getLogger(__name__)

# Redis client for rate limiting
redis_client = redis.from_url(settings.redis_url) if settings.redis_url else None


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""
    
    def __init__(self, app: FastAPI, calls: int = 60, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not redis_client:
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host
        key = f"rate_limit:{client_ip}"
        
        try:
            # Check current count
            current = redis_client.get(key)
            if current is None:
                # First request
                redis_client.setex(key, self.period, 1)
            else:
                current_count = int(current)
                if current_count >= self.calls:
                    return JSONResponse(
                        status_code=429,
                        content={
                            "error": "Rate limit exceeded",
                            "retry_after": redis_client.ttl(key)
                        }
                    )
                else:
                    redis_client.incr(key)
        
        except Exception as e:
            logger.warning(f"Rate limiting error: {e}")
            # Continue without rate limiting if Redis fails
        
        return await call_next(request)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Request/response logging middleware."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {request.client.host}"
        )
        
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(
            f"Response: {response.status_code} "
            f"in {process_time:.4f}s"
        )
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        if not settings.debug:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


def setup_middleware(app: FastAPI):
    """Setup all middleware for the application."""
    
    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Request logging
    if settings.debug:
        app.add_middleware(LoggingMiddleware)
    
    # Rate limiting
    app.add_middleware(
        RateLimitMiddleware,
        calls=settings.rate_limit_per_minute,
        period=60
    )
