import json
import hashlib
import logging
import asyncio
from typing import Any, Optional, Callable
from functools import wraps
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SimpleCache:
    """Simple in-memory cache with TTL support"""
    def __init__(self):
        self._cache = {}
    
    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate cache key from function name and arguments"""
        key_data = f"{func_name}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key in self._cache:
            value, expiry = self._cache[key]
            if datetime.now() < expiry:
                return value
            else:
                del self._cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in cache with TTL in seconds"""
        expiry = datetime.now() + timedelta(seconds=ttl)
        self._cache[key] = (value, expiry)
    
    def clear(self):
        """Clear all cache entries"""
        self._cache.clear()
        logger.info("Cache cleared")

# Global cache instance
cache = SimpleCache()

def cache_result(ttl: int = 3600):
    """Decorator to cache function results"""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache_key = cache._generate_key(func.__name__, args, kwargs)
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            logger.debug(f"Cached result for {func.__name__}")
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache_key = cache._generate_key(func.__name__, args, kwargs)
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            logger.debug(f"Cached result for {func.__name__}")
            return result
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator