"""Caching layer for GitHub API responses and local file change detection."""

import json
import sqlite3
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class CacheEntry:
    """Represents a cached item with metadata."""
    key: str
    data: Any
    created_at: datetime
    expires_at: Optional[datetime] = None
    etag: Optional[str] = None
    last_modified: Optional[str] = None


class CacheProvider(ABC):
    """Abstract base class for cache providers."""

    @abstractmethod
    def get(self, key: str) -> Optional[CacheEntry]:
        """Retrieve a cache entry by key."""
        pass

    @abstractmethod
    def set(self, key: str, data: Any, ttl: Optional[int] = None,
            etag: Optional[str] = None, last_modified: Optional[str] = None) -> None:
        """Store a cache entry."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a cache entry."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all cache entries."""
        pass

    @abstractmethod
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count removed."""
        pass


class SQLiteCacheProvider(CacheProvider):
    """SQLite-based cache provider."""

    def __init__(self, cache_db_path: str):
        """
        Initialize SQLite cache provider.

        Args:
            cache_db_path: Path to the cache database file
        """
        self.cache_db_path = cache_db_path
        self.logger = logging.getLogger(__name__)
        self._init_cache_db()

    def _init_cache_db(self) -> None:
        """Initialize the cache database schema."""
        with sqlite3.connect(self.cache_db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT,
                    etag TEXT,
                    last_modified TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cache_expires_at ON cache_entries(expires_at)
            """)
            conn.commit()

    def get(self, key: str) -> Optional[CacheEntry]:
        """Retrieve a cache entry by key."""
        with sqlite3.connect(self.cache_db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT key, data, created_at, expires_at, etag, last_modified
                FROM cache_entries
                WHERE key = ?
            """, (key,))

            row = cursor.fetchone()
            if not row:
                return None

            # Check if expired
            if row['expires_at']:
                expires_at = datetime.fromisoformat(row['expires_at'])
                if datetime.now(timezone.utc) > expires_at:
                    self.delete(key)
                    return None

            try:
                data = json.loads(row['data'])
            except json.JSONDecodeError:
                self.logger.warning(f"Invalid JSON in cache entry {key}, removing")
                self.delete(key)
                return None

            return CacheEntry(
                key=row['key'],
                data=data,
                created_at=datetime.fromisoformat(row['created_at']),
                expires_at=datetime.fromisoformat(row['expires_at']) if row['expires_at'] else None,
                etag=row['etag'],
                last_modified=row['last_modified']
            )

    def set(self, key: str, data: Any, ttl: Optional[int] = None,
            etag: Optional[str] = None, last_modified: Optional[str] = None) -> None:
        """Store a cache entry."""
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=ttl) if ttl else None

        with sqlite3.connect(self.cache_db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO cache_entries
                (key, data, created_at, expires_at, etag, last_modified)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                key,
                json.dumps(data),
                now.isoformat(),
                expires_at.isoformat() if expires_at else None,
                etag,
                last_modified
            ))
            conn.commit()

    def delete(self, key: str) -> bool:
        """Delete a cache entry."""
        with sqlite3.connect(self.cache_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
            conn.commit()
            return cursor.rowcount > 0

    def clear(self) -> None:
        """Clear all cache entries."""
        with sqlite3.connect(self.cache_db_path) as conn:
            conn.execute("DELETE FROM cache_entries")
            conn.commit()

    def cleanup_expired(self) -> int:
        """Remove expired entries and return count removed."""
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.cache_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM cache_entries
                WHERE expires_at IS NOT NULL AND expires_at < ?
            """, (now,))
            conn.commit()
            return cursor.rowcount


class InMemoryCacheProvider(CacheProvider):
    """In-memory cache provider for testing."""

    def __init__(self):
        """Initialize in-memory cache."""
        self._cache: Dict[str, CacheEntry] = {}
        self.logger = logging.getLogger(__name__)

    def get(self, key: str) -> Optional[CacheEntry]:
        """Retrieve a cache entry by key."""
        entry = self._cache.get(key)
        if not entry:
            return None

        # Check if expired
        if entry.expires_at and datetime.now(timezone.utc) > entry.expires_at:
            del self._cache[key]
            return None

        return entry

    def set(self, key: str, data: Any, ttl: Optional[int] = None,
            etag: Optional[str] = None, last_modified: Optional[str] = None) -> None:
        """Store a cache entry."""
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=ttl) if ttl else None

        self._cache[key] = CacheEntry(
            key=key,
            data=data,
            created_at=now,
            expires_at=expires_at,
            etag=etag,
            last_modified=last_modified
        )

    def delete(self, key: str) -> bool:
        """Delete a cache entry."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()

    def cleanup_expired(self) -> int:
        """Remove expired entries and return count removed."""
        now = datetime.now(timezone.utc)
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.expires_at and now > entry.expires_at
        ]

        for key in expired_keys:
            del self._cache[key]

        return len(expired_keys)


class APICache:
    """GitHub API response cache with ETag support."""

    def __init__(self, cache_provider: CacheProvider, default_ttl: int = 3600):
        """
        Initialize API cache.

        Args:
            cache_provider: Cache provider implementation
            default_ttl: Default time-to-live in seconds (default: 1 hour)
        """
        self.cache_provider = cache_provider
        self.default_ttl = default_ttl
        self.logger = logging.getLogger(__name__)

    def _generate_cache_key(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Generate a cache key for an API endpoint and parameters."""
        key_data = {"endpoint": endpoint}
        if params:
            key_data["params"] = sorted(params.items())

        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()[:16]

    def get_cached_response(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Get cached API response.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            Cached response data or None if not cached/expired
        """
        cache_key = self._generate_cache_key(endpoint, params)
        entry = self.cache_provider.get(cache_key)

        if entry:
            self.logger.debug(f"Cache hit for {endpoint}")
            return entry.data

        self.logger.debug(f"Cache miss for {endpoint}")
        return None

    def cache_response(self, endpoint: str, response_data: Dict[str, Any],
                      params: Optional[Dict[str, Any]] = None,
                      etag: Optional[str] = None,
                      last_modified: Optional[str] = None,
                      ttl: Optional[int] = None) -> None:
        """
        Cache an API response.

        Args:
            endpoint: API endpoint
            response_data: Response data to cache
            params: Query parameters
            etag: ETag header value
            last_modified: Last-Modified header value
            ttl: Time-to-live override
        """
        cache_key = self._generate_cache_key(endpoint, params)
        cache_ttl = ttl or self.default_ttl

        self.cache_provider.set(
            cache_key,
            response_data,
            ttl=cache_ttl,
            etag=etag,
            last_modified=last_modified
        )

        self.logger.debug(f"Cached response for {endpoint} (TTL: {cache_ttl}s)")

    def get_conditional_headers(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """
        Get conditional request headers (If-None-Match, If-Modified-Since).

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            Dictionary of conditional headers
        """
        cache_key = self._generate_cache_key(endpoint, params)
        entry = self.cache_provider.get(cache_key)

        headers = {}
        if entry:
            if entry.etag:
                headers["If-None-Match"] = entry.etag
            if entry.last_modified:
                headers["If-Modified-Since"] = entry.last_modified

        return headers

    def invalidate_cache(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> bool:
        """
        Invalidate cached entry for an endpoint.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            True if entry was removed, False if not found
        """
        cache_key = self._generate_cache_key(endpoint, params)
        return self.cache_provider.delete(cache_key)

    def cleanup_expired(self) -> int:
        """Remove expired cache entries."""
        return self.cache_provider.cleanup_expired()

    def clear_all(self) -> None:
        """Clear all cached entries."""
        self.cache_provider.clear()


class FileChangeCache:
    """Cache for local file change detection optimization."""

    def __init__(self, cache_provider: CacheProvider):
        """
        Initialize file change cache.

        Args:
            cache_provider: Cache provider implementation
        """
        self.cache_provider = cache_provider
        self.logger = logging.getLogger(__name__)

    def _generate_file_key(self, file_path: str) -> str:
        """Generate cache key for a file path."""
        return f"file:{hashlib.sha256(file_path.encode()).hexdigest()[:16]}"

    def _get_file_signature(self, file_path: Path) -> Dict[str, Any]:
        """
        Generate file signature for change detection.

        Args:
            file_path: Path to the file

        Returns:
            File signature with size, mtime, and content hash
        """
        if not file_path.exists():
            return {"exists": False}

        stat = file_path.stat()
        signature = {
            "exists": True,
            "size": stat.st_size,
            "mtime": stat.st_mtime,
            "mtime_ns": stat.st_mtime_ns
        }

        # For small files, include content hash
        if stat.st_size < 10240:  # 10KB threshold
            try:
                with open(file_path, 'rb') as f:
                    content_hash = hashlib.sha256(f.read()).hexdigest()
                signature["content_hash"] = content_hash
            except (IOError, OSError):
                pass

        return signature

    def has_file_changed(self, file_path: str) -> bool:
        """
        Check if a file has changed since last check.

        Args:
            file_path: Path to the file

        Returns:
            True if file has changed or is not cached, False otherwise
        """
        cache_key = self._generate_file_key(file_path)
        cached_entry = self.cache_provider.get(cache_key)

        current_signature = self._get_file_signature(Path(file_path))

        if not cached_entry:
            # File not cached, consider it changed
            self._update_file_signature(file_path, current_signature)
            return True

        cached_signature = cached_entry.data

        # Compare signatures
        if cached_signature != current_signature:
            self._update_file_signature(file_path, current_signature)
            return True

        return False

    def _update_file_signature(self, file_path: str, signature: Dict[str, Any]) -> None:
        """Update cached file signature."""
        cache_key = self._generate_file_key(file_path)
        # Cache file signatures for 24 hours
        self.cache_provider.set(cache_key, signature, ttl=86400)

    def invalidate_file(self, file_path: str) -> bool:
        """
        Invalidate cached entry for a file.

        Args:
            file_path: Path to the file

        Returns:
            True if entry was removed, False if not found
        """
        cache_key = self._generate_file_key(file_path)
        return self.cache_provider.delete(cache_key)

    def get_changed_files(self, file_paths: List[str]) -> List[str]:
        """
        Get list of files that have changed.

        Args:
            file_paths: List of file paths to check

        Returns:
            List of file paths that have changed
        """
        changed_files = []
        for file_path in file_paths:
            if self.has_file_changed(file_path):
                changed_files.append(file_path)
        return changed_files


def create_cache_provider(cache_type: str = "sqlite", **kwargs) -> CacheProvider:
    """
    Factory function to create cache providers.

    Args:
        cache_type: Type of cache provider ("sqlite", "memory")
        **kwargs: Additional arguments for cache provider

    Returns:
        Cache provider instance
    """
    if cache_type == "sqlite":
        cache_db_path = kwargs.get("cache_db_path", "md_manager_cache.db")
        return SQLiteCacheProvider(cache_db_path)
    elif cache_type == "memory":
        return InMemoryCacheProvider()
    else:
        raise ValueError(f"Unknown cache type: {cache_type}")