"""Tests for caching functionality."""

import json
import tempfile
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from md_manager.cache import (
    CacheEntry, SQLiteCacheProvider, InMemoryCacheProvider,
    APICache, FileChangeCache, create_cache_provider
)


class TestCacheEntry:
    """Test cases for CacheEntry dataclass."""

    def test_cache_entry_creation(self):
        """Test CacheEntry creation with all fields."""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=1)

        entry = CacheEntry(
            key="test-key",
            data={"test": "data"},
            created_at=now,
            expires_at=expires,
            etag="W/\"abc123\"",
            last_modified="Wed, 21 Oct 2015 07:28:00 GMT"
        )

        assert entry.key == "test-key"
        assert entry.data == {"test": "data"}
        assert entry.created_at == now
        assert entry.expires_at == expires
        assert entry.etag == "W/\"abc123\""
        assert entry.last_modified == "Wed, 21 Oct 2015 07:28:00 GMT"

    def test_cache_entry_minimal(self):
        """Test CacheEntry creation with minimal fields."""
        now = datetime.now(timezone.utc)

        entry = CacheEntry(
            key="test-key",
            data="simple data",
            created_at=now
        )

        assert entry.key == "test-key"
        assert entry.data == "simple data"
        assert entry.created_at == now
        assert entry.expires_at is None
        assert entry.etag is None
        assert entry.last_modified is None


class TestSQLiteCacheProvider:
    """Test cases for SQLiteCacheProvider."""

    @pytest.fixture
    def temp_cache_db(self):
        """Create temporary cache database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            yield f.name
        Path(f.name).unlink(missing_ok=True)

    @pytest.fixture
    def cache_provider(self, temp_cache_db):
        """SQLiteCacheProvider instance for testing."""
        return SQLiteCacheProvider(temp_cache_db)

    def test_cache_provider_initialization(self, temp_cache_db):
        """Test cache provider initialization creates database."""
        provider = SQLiteCacheProvider(temp_cache_db)
        assert Path(temp_cache_db).exists()

    def test_set_and_get_cache_entry(self, cache_provider):
        """Test storing and retrieving cache entries."""
        test_data = {"key": "value", "number": 42}

        cache_provider.set("test-key", test_data, ttl=3600)
        entry = cache_provider.get("test-key")

        assert entry is not None
        assert entry.key == "test-key"
        assert entry.data == test_data
        assert entry.expires_at is not None

    def test_get_nonexistent_entry(self, cache_provider):
        """Test retrieving non-existent cache entry."""
        entry = cache_provider.get("nonexistent-key")
        assert entry is None

    def test_entry_expiration(self, cache_provider):
        """Test that expired entries are automatically removed."""
        test_data = {"expired": True}

        # Set entry with very short TTL
        cache_provider.set("expiring-key", test_data, ttl=1)

        # Should exist immediately
        entry = cache_provider.get("expiring-key")
        assert entry is not None

        # Wait for expiration
        time.sleep(1.1)

        # Should be gone
        entry = cache_provider.get("expiring-key")
        assert entry is None

    def test_set_with_etag_and_last_modified(self, cache_provider):
        """Test storing cache entry with ETag and Last-Modified."""
        test_data = {"cached": "response"}
        etag = "W/\"abc123\""
        last_modified = "Wed, 21 Oct 2015 07:28:00 GMT"

        cache_provider.set("api-key", test_data, etag=etag, last_modified=last_modified)
        entry = cache_provider.get("api-key")

        assert entry is not None
        assert entry.etag == etag
        assert entry.last_modified == last_modified

    def test_delete_cache_entry(self, cache_provider):
        """Test deleting cache entries."""
        cache_provider.set("delete-me", {"data": "test"})

        # Ensure it exists
        assert cache_provider.get("delete-me") is not None

        # Delete it
        deleted = cache_provider.delete("delete-me")
        assert deleted is True

        # Should be gone
        assert cache_provider.get("delete-me") is None

    def test_delete_nonexistent_entry(self, cache_provider):
        """Test deleting non-existent entry."""
        deleted = cache_provider.delete("nonexistent")
        assert deleted is False

    def test_clear_cache(self, cache_provider):
        """Test clearing all cache entries."""
        cache_provider.set("key1", {"data": 1})
        cache_provider.set("key2", {"data": 2})

        # Ensure entries exist
        assert cache_provider.get("key1") is not None
        assert cache_provider.get("key2") is not None

        # Clear cache
        cache_provider.clear()

        # Should be gone
        assert cache_provider.get("key1") is None
        assert cache_provider.get("key2") is None

    def test_cleanup_expired(self, cache_provider):
        """Test cleanup of expired entries."""
        # Add some entries with different TTLs
        cache_provider.set("long-lived", {"data": 1}, ttl=3600)
        cache_provider.set("short-lived", {"data": 2}, ttl=1)

        time.sleep(1.1)

        # Cleanup expired entries
        removed_count = cache_provider.cleanup_expired()
        assert removed_count == 1

        # Check which entries remain
        assert cache_provider.get("long-lived") is not None
        assert cache_provider.get("short-lived") is None


class TestInMemoryCacheProvider:
    """Test cases for InMemoryCacheProvider."""

    @pytest.fixture
    def cache_provider(self):
        """InMemoryCacheProvider instance for testing."""
        return InMemoryCacheProvider()

    def test_set_and_get_cache_entry(self, cache_provider):
        """Test storing and retrieving cache entries."""
        test_data = {"memory": "cached"}

        cache_provider.set("mem-key", test_data, ttl=3600)
        entry = cache_provider.get("mem-key")

        assert entry is not None
        assert entry.key == "mem-key"
        assert entry.data == test_data

    def test_entry_expiration(self, cache_provider):
        """Test that expired entries are automatically removed."""
        cache_provider.set("expiring", {"data": "test"}, ttl=1)

        # Should exist immediately
        assert cache_provider.get("expiring") is not None

        # Wait for expiration
        time.sleep(1.1)

        # Should be gone
        assert cache_provider.get("expiring") is None

    def test_cleanup_expired(self, cache_provider):
        """Test cleanup of expired entries."""
        cache_provider.set("keep", {"data": 1}, ttl=3600)
        cache_provider.set("expire", {"data": 2}, ttl=1)

        time.sleep(1.1)

        removed_count = cache_provider.cleanup_expired()
        assert removed_count == 1
        assert cache_provider.get("keep") is not None
        assert cache_provider.get("expire") is None


class TestAPICache:
    """Test cases for APICache."""

    @pytest.fixture
    def cache_provider(self):
        """InMemoryCacheProvider for testing."""
        return InMemoryCacheProvider()

    @pytest.fixture
    def api_cache(self, cache_provider):
        """APICache instance for testing."""
        return APICache(cache_provider, default_ttl=3600)

    def test_cache_key_generation(self, api_cache):
        """Test cache key generation is consistent."""
        key1 = api_cache._generate_cache_key("/repos/owner/repo/issues")
        key2 = api_cache._generate_cache_key("/repos/owner/repo/issues")
        assert key1 == key2

        # Different endpoints should have different keys
        key3 = api_cache._generate_cache_key("/repos/owner/repo/pulls")
        assert key1 != key3

        # Same endpoint with different params should have different keys
        key4 = api_cache._generate_cache_key("/repos/owner/repo/issues", {"state": "open"})
        assert key1 != key4

    def test_cache_and_retrieve_response(self, api_cache):
        """Test caching and retrieving API responses."""
        endpoint = "/repos/owner/repo/issues"
        response_data = {"issues": [{"number": 1, "title": "Test Issue"}]}

        # Cache response
        api_cache.cache_response(endpoint, response_data)

        # Retrieve cached response
        cached_data = api_cache.get_cached_response(endpoint)
        assert cached_data == response_data

    def test_cache_miss(self, api_cache):
        """Test cache miss returns None."""
        cached_data = api_cache.get_cached_response("/nonexistent/endpoint")
        assert cached_data is None

    def test_cache_with_etag(self, api_cache):
        """Test caching with ETag support."""
        endpoint = "/repos/owner/repo/issues"
        response_data = {"issues": []}
        etag = "W/\"abc123\""

        api_cache.cache_response(endpoint, response_data, etag=etag)

        # Get conditional headers
        headers = api_cache.get_conditional_headers(endpoint)
        assert headers.get("If-None-Match") == etag

    def test_cache_with_last_modified(self, api_cache):
        """Test caching with Last-Modified support."""
        endpoint = "/repos/owner/repo/issues"
        response_data = {"issues": []}
        last_modified = "Wed, 21 Oct 2015 07:28:00 GMT"

        api_cache.cache_response(endpoint, response_data, last_modified=last_modified)

        headers = api_cache.get_conditional_headers(endpoint)
        assert headers.get("If-Modified-Since") == last_modified

    def test_invalidate_cache(self, api_cache):
        """Test cache invalidation."""
        endpoint = "/repos/owner/repo/issues"
        api_cache.cache_response(endpoint, {"data": "test"})

        # Ensure it's cached
        assert api_cache.get_cached_response(endpoint) is not None

        # Invalidate
        invalidated = api_cache.invalidate_cache(endpoint)
        assert invalidated is True

        # Should be gone
        assert api_cache.get_cached_response(endpoint) is None

    def test_cache_with_params(self, api_cache):
        """Test caching with query parameters."""
        endpoint = "/repos/owner/repo/issues"
        params = {"state": "open", "labels": "bug"}
        response_data = {"issues": [{"number": 1}]}

        api_cache.cache_response(endpoint, response_data, params=params)

        # Should get cached response with same params
        cached_data = api_cache.get_cached_response(endpoint, params)
        assert cached_data == response_data

        # Should not get cached response with different params
        cached_data = api_cache.get_cached_response(endpoint, {"state": "closed"})
        assert cached_data is None


class TestFileChangeCache:
    """Test cases for FileChangeCache."""

    @pytest.fixture
    def cache_provider(self):
        """InMemoryCacheProvider for testing."""
        return InMemoryCacheProvider()

    @pytest.fixture
    def file_cache(self, cache_provider):
        """FileChangeCache instance for testing."""
        return FileChangeCache(cache_provider)

    @pytest.fixture
    def temp_file(self):
        """Create temporary file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test File\n\nInitial content.")
            temp_path = f.name

        yield temp_path
        Path(temp_path).unlink(missing_ok=True)

    def test_file_signature_generation(self, file_cache, temp_file):
        """Test file signature generation."""
        signature = file_cache._get_file_signature(Path(temp_file))

        assert signature["exists"] is True
        assert "size" in signature
        assert "mtime" in signature
        assert "mtime_ns" in signature
        assert "content_hash" in signature  # Small file should have content hash

    def test_nonexistent_file_signature(self, file_cache):
        """Test signature for non-existent file."""
        signature = file_cache._get_file_signature(Path("/nonexistent/file.md"))
        assert signature == {"exists": False}

    def test_first_check_reports_change(self, file_cache, temp_file):
        """Test that first check of a file reports it as changed."""
        changed = file_cache.has_file_changed(temp_file)
        assert changed is True

    def test_unchanged_file_reports_no_change(self, file_cache, temp_file):
        """Test that unchanged file reports no change on second check."""
        # First check - should report changed
        file_cache.has_file_changed(temp_file)

        # Second check - should report no change
        changed = file_cache.has_file_changed(temp_file)
        assert changed is False

    def test_modified_file_reports_change(self, file_cache, temp_file):
        """Test that modified file reports change."""
        # Initial check
        file_cache.has_file_changed(temp_file)

        # Modify file
        time.sleep(0.01)  # Ensure different mtime
        with open(temp_file, 'a') as f:
            f.write("\n\nAdditional content.")

        # Should report changed
        changed = file_cache.has_file_changed(temp_file)
        assert changed is True

    def test_get_changed_files(self, file_cache, temp_file):
        """Test getting list of changed files."""
        # Create another temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Another File")
            temp_file2 = f.name

        try:
            file_paths = [temp_file, temp_file2]

            # First check - both should be changed
            changed_files = file_cache.get_changed_files(file_paths)
            assert len(changed_files) == 2
            assert temp_file in changed_files
            assert temp_file2 in changed_files

            # Second check - no changes
            changed_files = file_cache.get_changed_files(file_paths)
            assert len(changed_files) == 0

            # Modify one file
            time.sleep(0.01)
            with open(temp_file, 'a') as f:
                f.write("\n\nModified.")

            # Only one should be changed
            changed_files = file_cache.get_changed_files(file_paths)
            assert len(changed_files) == 1
            assert temp_file in changed_files

        finally:
            Path(temp_file2).unlink(missing_ok=True)

    def test_invalidate_file_cache(self, file_cache, temp_file):
        """Test invalidating file cache."""
        # Cache the file
        file_cache.has_file_changed(temp_file)

        # Invalidate
        invalidated = file_cache.invalidate_file(temp_file)
        assert invalidated is True

        # Next check should report changed
        changed = file_cache.has_file_changed(temp_file)
        assert changed is True


class TestCacheFactory:
    """Test cases for cache provider factory."""

    def test_create_sqlite_cache_provider(self):
        """Test creating SQLite cache provider."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            cache_db_path = f.name

        try:
            provider = create_cache_provider("sqlite", cache_db_path=cache_db_path)
            assert isinstance(provider, SQLiteCacheProvider)
            assert provider.cache_db_path == cache_db_path
        finally:
            Path(cache_db_path).unlink(missing_ok=True)

    def test_create_memory_cache_provider(self):
        """Test creating in-memory cache provider."""
        provider = create_cache_provider("memory")
        assert isinstance(provider, InMemoryCacheProvider)

    def test_create_default_sqlite_provider(self):
        """Test creating SQLite provider with default path."""
        provider = create_cache_provider("sqlite")
        assert isinstance(provider, SQLiteCacheProvider)
        assert provider.cache_db_path == "md_manager_cache.db"

    def test_create_unknown_cache_type(self):
        """Test creating cache provider with unknown type."""
        with pytest.raises(ValueError, match="Unknown cache type: redis"):
            create_cache_provider("redis")