"""
Monitoring middleware for SCONIA.
Tracks API performance and metrics.
"""
import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.services.monitoring import performance_monitor
from app.config import settings

logger = logging.getLogger(__name__)


class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware to track API performance and metrics."""
    
    def __init__(self, app, exclude_paths: list = None):
        """
        Initialize monitoring middleware.
        
        Args:
            app: FastAPI application
            exclude_paths: List of paths to exclude from monitoring
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/docs",
            "/openapi.json",
            "/favicon.ico"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and track metrics."""
        # Skip monitoring for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Extract request info
        method = request.method
        path = request.url.path
        
        # Track request
        start_time = time.time()
        
        try:
            # Use performance monitor context manager
            async with performance_monitor.track_request(path, method):
                response = await call_next(request)
            
            # Record additional metrics based on endpoint
            response_time = time.time() - start_time
            
            # Track specific endpoint types
            if "/chat" in path:
                # This would be enhanced to extract actual intent from response
                performance_monitor.record_chat_query(
                    response_time=response_time,
                    intent="general",  # Would extract from actual response
                    success=response.status_code < 400
                )
            
            elif "/search" in path:
                # This would be enhanced to extract actual result count
                performance_monitor.record_search_query(
                    response_time=response_time,
                    result_count=0,  # Would extract from actual response
                    query_type="api"
                )
            
            # Add performance headers to response
            response.headers["X-Response-Time"] = f"{response_time:.3f}s"
            response.headers["X-Request-ID"] = str(id(request))
            
            return response
            
        except Exception as e:
            # Error occurred - still record metrics
            response_time = time.time() - start_time
            logger.error(f"Error in request {method} {path}: {e}")
            
            # Re-raise the exception
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware."""
    
    def __init__(self, app, requests_per_minute: int = 60, exclude_paths: list = None):
        """
        Initialize rate limiting middleware.
        
        Args:
            app: FastAPI application
            requests_per_minute: Maximum requests per minute per IP
            exclude_paths: List of paths to exclude from rate limiting
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts = {}
        self.last_reset = time.time()
        # Exclude health check and monitoring endpoints
        self.exclude_paths = exclude_paths or [
            "/health",
            "/startup",
            "/ready",
            "/metrics"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            response = await call_next(request)
            # Still add rate limit headers for transparency
            response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
            response.headers["X-RateLimit-Remaining"] = str(self.requests_per_minute)
            return response
        
        current_time = time.time()
        client_ip = request.client.host
        
        # Reset counts every minute
        if current_time - self.last_reset > 60:
            self.request_counts.clear()
            self.last_reset = current_time
        
        # Check rate limit
        current_count = self.request_counts.get(client_ip, 0)
        
        if current_count >= self.requests_per_minute:
            # Rate limit exceeded
            from fastapi import HTTPException
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": "60"}
            )
        
        # Increment count
        self.request_counts[client_ip] = current_count + 1
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, self.requests_per_minute - self.request_counts.get(client_ip, 0))
        )
        response.headers["X-RateLimit-Reset"] = str(int(self.last_reset + 60))
        
        return response

class CORSMiddleware(BaseHTTPMiddleware):
    """Enhanced CORS middleware with monitoring."""
    
    def __init__(self, app, allowed_origins: list = None):
        """
        Initialize CORS middleware.
        
        Args:
            app: FastAPI application
            allowed_origins: List of allowed origins
        """
        super().__init__(app)
        self.allowed_origins = allowed_origins or ["*"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle CORS with monitoring."""
        origin = request.headers.get("origin")
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = Response()
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            response.headers["Access-Control-Max-Age"] = "86400"
            return response
        
        # Process request
        response = await call_next(request)
        
        # Add CORS headers
        if origin and (self.allowed_origins == ["*"] or origin in self.allowed_origins):
            response.headers["Access-Control-Allow-Origin"] = origin
        else:
            response.headers["Access-Control-Allow-Origin"] = "*"
        
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        
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
