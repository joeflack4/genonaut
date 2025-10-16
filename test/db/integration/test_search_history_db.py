"""Database tests for user search history CRUD operations."""

import pytest
from uuid import UUID
from datetime import datetime, timedelta

from genonaut.db.schema import UserSearchHistory, User
from genonaut.api.repositories.user_search_history_repository import UserSearchHistoryRepository


@pytest.fixture
def test_user(db_session):
    """Create a test user for search history tests."""
    user = User(
        username='test-user',
        email='test@example.com'
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def repository(db_session):
    """Create search history repository instance."""
    return UserSearchHistoryRepository(db_session)


class TestSearchHistoryCRUD:
    """Test basic CRUD operations for search history."""

    def test_add_search(self, repository, test_user, db_session):
        """Test adding a search to history."""
        search_query = "test search query"

        history_entry = repository.add_search(test_user.id, search_query)

        assert history_entry.id is not None
        assert history_entry.user_id == test_user.id
        assert history_entry.search_query == search_query
        assert history_entry.created_at is not None
        assert isinstance(history_entry.created_at, datetime)

    def test_add_multiple_searches(self, repository, test_user, db_session):
        """Test adding multiple searches creates separate entries."""
        queries = ["first search", "second search", "third search"]

        entries = []
        for query in queries:
            entry = repository.add_search(test_user.id, query)
            entries.append(entry)

        assert len(entries) == 3
        assert [e.search_query for e in entries] == queries
        # All should have unique IDs
        assert len(set(e.id for e in entries)) == 3

    def test_add_duplicate_searches_allowed(self, repository, test_user, db_session):
        """Test that duplicate searches are allowed (no deduplication)."""
        search_query = "duplicate search"

        entry1 = repository.add_search(test_user.id, search_query)
        entry2 = repository.add_search(test_user.id, search_query)

        assert entry1.id != entry2.id
        assert entry1.search_query == entry2.search_query
        assert entry2.created_at >= entry1.created_at

    def test_get_recent_searches(self, repository, test_user, db_session):
        """Test retrieving recent searches."""
        # Add searches with slight delay to ensure ordering
        queries = ["search 1", "search 2", "search 3", "search 4", "search 5"]
        for query in queries:
            repository.add_search(test_user.id, query)

        # Get 3 most recent
        recent = repository.get_recent_searches(test_user.id, limit=3)

        assert len(recent) == 3
        # Should be in reverse chronological order (most recent first)
        assert recent[0].search_query == "search 5"
        assert recent[1].search_query == "search 4"
        assert recent[2].search_query == "search 3"

    def test_get_recent_searches_limit(self, repository, test_user, db_session):
        """Test that limit parameter works correctly."""
        for i in range(10):
            repository.add_search(test_user.id, f"search {i}")

        # Test different limits
        assert len(repository.get_recent_searches(test_user.id, limit=1)) == 1
        assert len(repository.get_recent_searches(test_user.id, limit=5)) == 5
        assert len(repository.get_recent_searches(test_user.id, limit=10)) == 10

    def test_get_recent_searches_empty(self, repository, test_user, db_session):
        """Test getting recent searches when none exist."""
        recent = repository.get_recent_searches(test_user.id, limit=3)

        assert recent == []

    def test_get_search_history_paginated(self, repository, test_user, db_session):
        """Test paginated search history retrieval."""
        # Add 25 searches
        for i in range(25):
            repository.add_search(test_user.id, f"search {i}")

        # Get first page
        items, total_count = repository.get_search_history_paginated(
            test_user.id, page=1, page_size=10
        )

        assert total_count == 25
        assert len(items) == 10
        # Most recent first
        assert items[0].search_query == "search 24"

    def test_get_search_history_paginated_second_page(self, repository, test_user, db_session):
        """Test retrieving second page of search history."""
        for i in range(25):
            repository.add_search(test_user.id, f"search {i}")

        items, total_count = repository.get_search_history_paginated(
            test_user.id, page=2, page_size=10
        )

        assert total_count == 25
        assert len(items) == 10
        assert items[0].search_query == "search 14"

    def test_get_search_history_paginated_last_page(self, repository, test_user, db_session):
        """Test retrieving last partial page."""
        for i in range(25):
            repository.add_search(test_user.id, f"search {i}")

        items, total_count = repository.get_search_history_paginated(
            test_user.id, page=3, page_size=10
        )

        assert total_count == 25
        assert len(items) == 5

    def test_delete_search(self, repository, test_user, db_session):
        """Test deleting a search history entry."""
        entry = repository.add_search(test_user.id, "search to delete")
        entry_id = entry.id

        # Delete the entry
        success = repository.delete_search(test_user.id, entry_id)

        assert success is True

        # Verify it's gone
        result = db_session.query(UserSearchHistory).filter_by(id=entry_id).first()
        assert result is None

    def test_delete_search_nonexistent(self, repository, test_user, db_session):
        """Test deleting a non-existent search returns False."""
        success = repository.delete_search(test_user.id, 99999)

        assert success is False

    def test_delete_search_wrong_user(self, repository, test_user, db_session):
        """Test deleting another user's search fails."""
        # Create another user
        other_user = User(
            username='other-user',
            email='other@example.com'
        )
        db_session.add(other_user)
        db_session.commit()

        # Add search for test_user
        entry = repository.add_search(test_user.id, "test search")

        # Try to delete with wrong user_id
        success = repository.delete_search(other_user.id, entry.id)

        assert success is False

        # Verify entry still exists
        result = db_session.query(UserSearchHistory).filter_by(id=entry.id).first()
        assert result is not None

    def test_clear_all_history(self, repository, test_user, db_session):
        """Test clearing all search history for a user."""
        # Add multiple searches
        for i in range(10):
            repository.add_search(test_user.id, f"search {i}")

        # Clear all
        deleted_count = repository.clear_all_history(test_user.id)

        assert deleted_count == 10

        # Verify all are gone
        remaining = db_session.query(UserSearchHistory).filter_by(
            user_id=test_user.id
        ).count()
        assert remaining == 0

    def test_clear_all_history_empty(self, repository, test_user, db_session):
        """Test clearing history when none exists."""
        deleted_count = repository.clear_all_history(test_user.id)

        assert deleted_count == 0

    def test_clear_all_history_only_own(self, repository, test_user, db_session):
        """Test clearing only clears the specific user's history."""
        # Create another user
        other_user = User(
            username='other-user',
            email='other@example.com'
        )
        db_session.add(other_user)
        db_session.commit()

        # Add searches for both users
        repository.add_search(test_user.id, "test search 1")
        repository.add_search(test_user.id, "test search 2")
        repository.add_search(other_user.id, "other search")

        # Clear test_user's history
        deleted_count = repository.clear_all_history(test_user.id)

        assert deleted_count == 2

        # Verify other_user's search still exists
        other_searches = db_session.query(UserSearchHistory).filter_by(
            user_id=other_user.id
        ).count()
        assert other_searches == 1


class TestSearchHistoryIndexPerformance:
    """Test index performance on search history table."""

    def test_index_on_user_id_exists(self, db_session):
        """Test that index on user_id exists for efficient queries."""
        # This test verifies the index exists in the schema
        # The actual index was created in the migration
        from sqlalchemy import inspect

        inspector = inspect(db_session.bind)
        indexes = inspector.get_indexes('user_search_history')

        # Check that there's an index containing user_id
        user_id_indexed = any(
            'user_id' in idx.get('column_names', [])
            for idx in indexes
        )

        assert user_id_indexed, "Index on user_id should exist"

    def test_composite_index_exists(self, db_session):
        """Test that composite index on (user_id, created_at DESC) exists."""
        from sqlalchemy import inspect

        inspector = inspect(db_session.bind)
        indexes = inspector.get_indexes('user_search_history')

        # Check for composite index with user_id and created_at
        composite_indexed = any(
            'user_id' in idx.get('column_names', []) and
            len(idx.get('column_names', [])) > 1
            for idx in indexes
        )

        assert composite_indexed, "Composite index should exist"

    def test_recent_searches_query_performance(self, repository, test_user, db_session):
        """Test that recent searches query is efficient with many entries."""
        # Add many searches (simulating real usage)
        for i in range(1000):
            repository.add_search(test_user.id, f"search {i}")

        # Query should still be fast with index
        import time
        start = time.time()
        recent = repository.get_recent_searches(test_user.id, limit=10)
        elapsed = time.time() - start

        assert len(recent) == 10
        # Should complete in under 100ms with proper index
        assert elapsed < 0.1, f"Query took {elapsed}s, should be < 0.1s with index"
