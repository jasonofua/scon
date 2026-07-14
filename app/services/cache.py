"""
Redis-based caching service for SCONIA performance optimization.
Implements query result caching, session caching, and frequently accessed data caching.
"""
import json
import hashlib
import logging
from typing import Any, Optional, Dict, List, Union, Tuple
from datetime import datetime, timedelta
import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Redis-based caching service for SCONIA."""
    
    def __init__(self):
        """Initialize cache service."""
        self.redis_client = None
        self.default_ttl = 3600  # 1 hour
        self.query_cache_ttl = 1800  # 30 minutes for query results
        self.session_cache_ttl = 7200  # 2 hours for session data
        self.static_cache_ttl = 86400  # 24 hours for static data (judges, procedures)
        
    async def initialize(self):
        """Initialize Redis connection."""
        try:
            if settings.redis_url:
                self.redis_client = redis.from_url(
                    settings.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    retry_on_timeout=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                # Test connection
                await self.redis_client.ping()
                logger.info("Redis cache service initialized successfully")
            else:
                logger.warning("Redis URL not configured, cache service disabled")
        except Exception as e:
            logger.error(f"Failed to initialize Redis cache: {e}")
            self.redis_client = None
    
    async def close(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
    
    def _generate_cache_key(self, prefix: str, *args) -> str:
        """Generate a cache key from prefix and arguments."""
        # Create a hash of the arguments for consistent key generation
        key_data = f"{prefix}:{':'.join(str(arg) for arg in args)}"
        return f"sconia:{hashlib.md5(key_data.encode()).hexdigest()[:16]}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.redis_client:
            return None
        
        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        if not self.redis_client:
            return False
        
        try:
            ttl = ttl or self.default_ttl
            serialized_value = json.dumps(value, default=str)  # default=str handles datetime objects
            await self.redis_client.setex(key, ttl, serialized_value)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.redis_client:
            return False
        
        try:
            result = await self.redis_client.delete(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.redis_client:
            return False
        
        try:
            result = await self.redis_client.exists(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    # Query result caching
    async def get_query_result(self, query: str, intent: str) -> Optional[Dict[str, Any]]:
        """Get cached query result."""
        key = self._generate_cache_key("query", query.lower().strip(), intent)
        return await self.get(key)
    
    async def set_query_result(self, query: str, intent: str, result: Dict[str, Any]) -> bool:
        """Cache query result."""
        key = self._generate_cache_key("query", query.lower().strip(), intent)
        return await self.set(key, result, self.query_cache_ttl)
    
    # RAG context caching
    async def get_rag_context(self, query: str) -> Optional[Tuple[str, List[Dict[str, Any]]]]:
        """Get cached RAG context and sources."""
        key = self._generate_cache_key("rag", query.lower().strip())
        cached_data = await self.get(key)
        if cached_data:
            return cached_data.get('context', ''), cached_data.get('sources', [])
        return None
    
    async def set_rag_context(self, query: str, context: str, sources: List[Dict[str, Any]]) -> bool:
        """Cache RAG context and sources."""
        key = self._generate_cache_key("rag", query.lower().strip())
        data = {'context': context, 'sources': sources}
        return await self.set(key, data, self.query_cache_ttl)
    
    # Session caching
    async def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get cached session data."""
        key = self._generate_cache_key("session", session_id)
        return await self.get(key)
    
    async def set_session_data(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Cache session data."""
        key = self._generate_cache_key("session", session_id)
        return await self.set(key, data, self.session_cache_ttl)
    
    # Static data caching (judges, procedures, fees)
    async def get_judges_data(self) -> Optional[List[Dict[str, Any]]]:
        """Get cached judges data."""
        key = self._generate_cache_key("static", "judges")
        return await self.get(key)
    
    async def set_judges_data(self, judges: List[Dict[str, Any]]) -> bool:
        """Cache judges data."""
        key = self._generate_cache_key("static", "judges")
        return await self.set(key, judges, self.static_cache_ttl)
    
    async def get_constitutional_provisions(self, chapter: Optional[str] = None, section: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """Get cached constitutional provisions."""
        key = self._generate_cache_key("constitutional", chapter or "all", section or "all")
        return await self.get(key)
    
    async def set_constitutional_provisions(self, provisions: List[Dict[str, Any]], chapter: Optional[str] = None, section: Optional[str] = None) -> bool:
        """Cache constitutional provisions."""
        key = self._generate_cache_key("constitutional", chapter or "all", section or "all")
        return await self.set(key, provisions, self.static_cache_ttl)
    
    async def get_fee_schedules(self) -> Optional[List[Dict[str, Any]]]:
        """Get cached fee schedules."""
        key = self._generate_cache_key("static", "fees")
        return await self.get(key)
    
    async def set_fee_schedules(self, fees: List[Dict[str, Any]]) -> bool:
        """Cache fee schedules."""
        key = self._generate_cache_key("static", "fees")
        return await self.set(key, fees, self.static_cache_ttl)
    
    # Bulk operations
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching a pattern."""
        if not self.redis_client:
            return 0
        
        try:
            keys = await self.redis_client.keys(f"sconia:*{pattern}*")
            if keys:
                return await self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache invalidate pattern error for {pattern}: {e}")
            return 0
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.redis_client:
            return {"status": "disabled"}
        
        try:
            info = await self.redis_client.info()
            return {
                "status": "active",
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": info.get("keyspace_hits", 0) / max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1)
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"status": "error", "error": str(e)}


# Global cache service instance
cache_service = CacheService()