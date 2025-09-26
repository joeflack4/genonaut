"""Simple in-memory caching service for ComfyUI-related data."""

import time
import threading
from typing import Any, Dict, Optional, Union, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from functools import wraps
import logging

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Represents a cached value with expiration."""
    value: Any
    expires_at: float
    created_at: float

    def is_expired(self) -> bool:
        """Check if this cache entry has expired."""
        return time.time() > self.expires_at


class InMemoryCache:
    """Thread-safe in-memory cache with TTL support."""

    def __init__(self):
        """Initialize the cache."""
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or expired
        """
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None

            if entry.is_expired():
                del self._cache[key]
                return None

            return entry.value

    def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> None:
        """Set a value in the cache with TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds (default: 1 hour)
        """
        with self._lock:
            now = time.time()
            entry = CacheEntry(
                value=value,
                expires_at=now + ttl_seconds,
                created_at=now
            )
            self._cache[key] = entry

    def delete(self, key: str) -> bool:
        """Delete a key from the cache.

        Args:
            key: Cache key to delete

        Returns:
            True if key existed and was deleted
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """Clear all entries from the cache."""
        with self._lock:
            self._cache.clear()

    def cleanup_expired(self) -> int:
        """Remove expired entries from the cache.

        Returns:
            Number of entries removed
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)

    def size(self) -> int:
        """Get the current size of the cache."""
        with self._lock:
            return len(self._cache)

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            now = time.time()
            valid_entries = sum(1 for entry in self._cache.values() if not entry.is_expired())
            expired_entries = len(self._cache) - valid_entries

            return {
                'total_entries': len(self._cache),
                'valid_entries': valid_entries,
                'expired_entries': expired_entries,
                'keys': list(self._cache.keys())
            }


# Global cache instance
_cache_instance: Optional[InMemoryCache] = None
_cache_lock = threading.Lock()


def get_cache() -> InMemoryCache:
    """Get the global cache instance (singleton)."""
    global _cache_instance
    if _cache_instance is None:
        with _cache_lock:
            if _cache_instance is None:
                _cache_instance = InMemoryCache()
    return _cache_instance


def cached(key_prefix: str, ttl_seconds: int = 3600):
    """Decorator to cache function results.

    Args:
        key_prefix: Prefix for the cache key
        ttl_seconds: Time to live in seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"

            cache = get_cache()

            # Try to get from cache first
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return result

            # Execute function and cache result
            logger.debug(f"Cache miss for key: {cache_key}")
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl_seconds)

            return result
        return wrapper
    return decorator


class ComfyUICacheService:
    """Service for ComfyUI-specific caching operations."""

    # Cache keys
    AVAILABLE_MODELS_KEY = "comfyui:available_models"
    MODEL_STATS_KEY = "comfyui:model_stats"
    COMFYUI_HEALTH_KEY = "comfyui:health_status"
    USER_STATS_PREFIX = "comfyui:user_stats"

    # Default TTL values (in seconds)
    MODELS_TTL = 3600  # 1 hour
    STATS_TTL = 900    # 15 minutes
    HEALTH_TTL = 30    # 30 seconds

    def __init__(self):
        """Initialize the ComfyUI cache service."""
        self.cache = get_cache()

    def get_available_models(self) -> Optional[List[Dict[str, Any]]]:
        """Get cached available models list."""
        return self.cache.get(self.AVAILABLE_MODELS_KEY)

    def set_available_models(self, models: List[Dict[str, Any]]) -> None:
        """Cache available models list."""
        self.cache.set(self.AVAILABLE_MODELS_KEY, models, self.MODELS_TTL)
        logger.info(f"Cached {len(models)} available models")

    def invalidate_models_cache(self) -> None:
        """Invalidate the available models cache."""
        self.cache.delete(self.AVAILABLE_MODELS_KEY)
        logger.info("Invalidated available models cache")

    def get_model_stats(self) -> Optional[Dict[str, int]]:
        """Get cached model statistics."""
        return self.cache.get(self.MODEL_STATS_KEY)

    def set_model_stats(self, stats: Dict[str, int]) -> None:
        """Cache model statistics."""
        self.cache.set(self.MODEL_STATS_KEY, stats, self.STATS_TTL)
        logger.debug(f"Cached model statistics: {stats}")

    def get_user_stats(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached user generation statistics."""
        key = f"{self.USER_STATS_PREFIX}:{user_id}"
        return self.cache.get(key)

    def set_user_stats(self, user_id: str, stats: Dict[str, Any]) -> None:
        """Cache user generation statistics."""
        key = f"{self.USER_STATS_PREFIX}:{user_id}"
        self.cache.set(key, stats, self.STATS_TTL)
        logger.debug(f"Cached user stats for {user_id}: {stats}")

    def get_comfyui_health(self) -> Optional[Dict[str, Any]]:
        """Get cached ComfyUI health status."""
        return self.cache.get(self.COMFYUI_HEALTH_KEY)

    def set_comfyui_health(self, health_status: Dict[str, Any]) -> None:
        """Cache ComfyUI health status."""
        self.cache.set(self.COMFYUI_HEALTH_KEY, health_status, self.HEALTH_TTL)
        logger.debug(f"Cached ComfyUI health status: {health_status}")

    def invalidate_user_stats(self, user_id: str) -> None:
        """Invalidate cached user statistics."""
        key = f"{self.USER_STATS_PREFIX}:{user_id}"
        self.cache.delete(key)
        logger.debug(f"Invalidated user stats for {user_id}")

    def clear_all_cache(self) -> None:
        """Clear all cached data."""
        self.cache.clear()
        logger.info("Cleared all ComfyUI cache data")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.cache.stats()

    def cleanup_expired_entries(self) -> int:
        """Clean up expired cache entries."""
        removed = self.cache.cleanup_expired()
        if removed > 0:
            logger.info(f"Cleaned up {removed} expired cache entries")
        return removed