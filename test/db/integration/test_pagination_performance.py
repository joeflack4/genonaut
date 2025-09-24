"""Performance tests for pagination optimization with database integration."""

import pytest
import time
from datetime import datetime, timedelta
from typing import List
from uuid import uuid4
from sqlalchemy.orm import Session

from genonaut.db.schema import User, ContentItem, UserInteraction, Recommendation, GenerationJob
from genonaut.api.repositories.content_repository import ContentRepository
from genonaut.api.repositories.user_repository import UserRepository
from genonaut.api.models.requests import PaginationRequest


class TestPaginationPerformance:
    """Performance tests for pagination with real database."""

    @pytest.fixture
    def sample_users(self, db_session: Session) -> List[User]:
        """Create sample users for testing."""
        users = []
        for i in range(100):
            user = User(
                username=f"user_{i:03d}",
                email=f"user{i:03d}@example.com",
                created_at=datetime.utcnow() - timedelta(days=i),
                is_active=i % 10 != 0  # 90% active users
            )
            db_session.add(user)
            users.append(user)

        db_session.commit()
        return users

    @pytest.fixture
    def sample_content(self, db_session: Session, sample_users: List[User]) -> List[ContentItem]:
        """Create sample content for testing."""
        content_items = []
        for i in range(1000):
            user = sample_users[i % len(sample_users)]
            content = ContentItem(
                title=f"Content Item {i:04d}",
                content_type=["text", "image", "video", "audio"][i % 4],
                content_data=f"Sample content data for item {i}",
                creator_id=user.id,
                created_at=datetime.utcnow() - timedelta(hours=i),
                quality_score=0.1 + (i % 10) * 0.1,  # Scores from 0.1 to 1.0
                is_private=i % 5 == 0  # 20% private content
            )
            db_session.add(content)
            content_items.append(content)

        db_session.commit()
        return content_items

    @pytest.fixture
    def sample_interactions(self, db_session: Session, sample_users: List[User],
                           sample_content: List[ContentItem]) -> List[UserInteraction]:
        """Create sample user interactions for testing."""
        interactions = []
        for i in range(2000):
            user = sample_users[i % len(sample_users)]
            content = sample_content[i % len(sample_content)]
            interaction = UserInteraction(
                user_id=user.id,
                content_item_id=content.id,
                interaction_type=["view", "like", "share", "download"][i % 4],
                rating=(i % 5) + 1 if i % 3 == 0 else None,  # Some interactions have ratings
                created_at=datetime.utcnow() - timedelta(minutes=i)
            )
            db_session.add(interaction)
            interactions.append(interaction)

        db_session.commit()
        return interactions

    def test_content_pagination_performance_by_creator(self, db_session: Session,
                                                     sample_users: List[User],
                                                     sample_content: List[ContentItem]):
        """Test pagination performance for content by creator queries."""
        repository = ContentRepository(db_session)
        creator_id = sample_users[0].id

        pagination_request = PaginationRequest(page=1, page_size=50)

        # Time the paginated query
        start_time = time.time()
        result = repository.get_by_creator_paginated(creator_id, pagination_request)
        end_time = time.time()

        query_time = end_time - start_time

        # Assertions
        assert len(result.items) > 0
        assert result.pagination.total_count > 0
        assert query_time < 0.1  # Should complete in less than 100ms with indexes

        # Test that all items belong to the correct creator
        for item in result.items:
            assert item.creator_id == creator_id

    def test_content_pagination_performance_public_only(self, db_session: Session,
                                                       sample_content: List[ContentItem]):
        """Test pagination performance for public content queries."""
        repository = ContentRepository(db_session)

        pagination_request = PaginationRequest(page=1, page_size=50)

        # Time the paginated query
        start_time = time.time()
        result = repository.get_public_content_paginated(pagination_request)
        end_time = time.time()

        query_time = end_time - start_time

        # Assertions
        assert len(result.items) > 0
        assert result.pagination.total_count > 0
        assert query_time < 0.1  # Should complete in less than 100ms with partial index

        # Test that all items are public
        for item in result.items:
            assert item.is_private is False

    def test_content_pagination_performance_by_quality(self, db_session: Session,
                                                      sample_content: List[ContentItem]):
        """Test pagination performance for top-rated content queries."""
        repository = ContentRepository(db_session)

        pagination_request = PaginationRequest(page=1, page_size=50)

        # Time the paginated query
        start_time = time.time()
        result = repository.get_top_rated_paginated(pagination_request)
        end_time = time.time()

        query_time = end_time - start_time

        # Assertions
        assert len(result.items) > 0
        assert result.pagination.total_count > 0
        assert query_time < 0.1  # Should complete in less than 100ms with quality index

        # Test that items are ordered by quality score (descending)
        if len(result.items) > 1:
            for i in range(len(result.items) - 1):
                assert result.items[i].quality_score >= result.items[i + 1].quality_score

    @pytest.mark.skip(reason="Data scaling tests - Performance/stress testing (see scratchpads/issues/by_priority/low/data-scaling-tests.md)")
    def test_user_pagination_performance_active_only(self, db_session: Session,
                                                    sample_users: List[User]):
        """Test pagination performance for active users queries."""
        repository = UserRepository(db_session)

        pagination_request = PaginationRequest(page=1, page_size=20)

        # Time the paginated query
        start_time = time.time()
        result = repository.get_active_users_paginated(pagination_request)
        end_time = time.time()

        query_time = end_time - start_time

        # Assertions
        assert len(result.items) > 0
        assert result.pagination.total_count > 0
        assert query_time < 0.05  # Should be very fast with is_active + created_at index

        # Test that all users are active
        for user in result.items:
            assert user.is_active is True

    def test_pagination_performance_large_offset(self, db_session: Session,
                                                sample_content: List[ContentItem]):
        """Test pagination performance with large offset values."""
        repository = ContentRepository(db_session)

        # Test pagination at page 10 (offset 450 with page_size=50)
        pagination_request = PaginationRequest(page=10, page_size=50)

        # Time the paginated query
        start_time = time.time()
        result = repository.get_paginated(pagination_request)
        end_time = time.time()

        query_time = end_time - start_time

        # Assertions
        assert len(result.items) > 0
        assert result.pagination.page == 10
        assert query_time < 0.15  # Should still be reasonably fast with indexes

    def test_pagination_performance_with_cursor(self, db_session: Session,
                                              sample_content: List[ContentItem]):
        """Test cursor-based pagination performance."""
        repository = ContentRepository(db_session)

        # First, get a page to establish cursor
        first_page = PaginationRequest(page=1, page_size=50, sort_field="created_at")
        first_result = repository.get_paginated(first_page)

        # Use cursor from first page if available
        if first_result.pagination.next_cursor:
            cursor_pagination = PaginationRequest(
                cursor=first_result.pagination.next_cursor,
                page_size=50,
                sort_field="created_at"
            )

            # Time the cursor-based query
            start_time = time.time()
            cursor_result = repository.get_paginated(cursor_pagination)
            end_time = time.time()

            query_time = end_time - start_time

            # Assertions
            assert len(cursor_result.items) > 0
            assert query_time < 0.1  # Cursor pagination should be fast

            # Verify no overlap with first page
            first_ids = {item.id for item in first_result.items}
            cursor_ids = {item.id for item in cursor_result.items}
            assert len(first_ids.intersection(cursor_ids)) == 0

    def test_bulk_pagination_consistency(self, db_session: Session,
                                       sample_content: List[ContentItem]):
        """Test that pagination results are consistent across multiple queries."""
        repository = ContentRepository(db_session)

        # Get first 3 pages
        all_items = []
        for page_num in range(1, 4):
            pagination_request = PaginationRequest(page=page_num, page_size=50)
            result = repository.get_paginated(pagination_request)
            all_items.extend(result.items)

        # Verify no duplicates across pages
        item_ids = [item.id for item in all_items]
        assert len(item_ids) == len(set(item_ids)), "Found duplicate items across pages"

        # Verify consistent ordering (created_at DESC by default)
        for i in range(len(all_items) - 1):
            assert all_items[i].created_at >= all_items[i + 1].created_at

    def test_filter_pagination_performance(self, db_session: Session,
                                         sample_content: List[ContentItem]):
        """Test pagination performance with filters applied."""
        repository = ContentRepository(db_session)

        # Test pagination with content_type filter
        pagination_request = PaginationRequest(page=1, page_size=25)
        filters = {"content_type": "text"}

        # Time the filtered paginated query
        start_time = time.time()
        result = repository.get_paginated(pagination_request, filters=filters)
        end_time = time.time()

        query_time = end_time - start_time

        # Assertions
        assert len(result.items) > 0
        assert result.pagination.total_count > 0
        assert query_time < 0.1  # Should be fast with content_type + created_at index

        # Verify filter is applied
        for item in result.items:
            assert item.content_type == "text"

    def test_count_query_performance(self, db_session: Session,
                                   sample_content: List[ContentItem]):
        """Test that count queries are optimized."""
        repository = ContentRepository(db_session)

        # Test regular count
        start_time = time.time()
        total_count = repository.count()
        end_time = time.time()

        count_time = end_time - start_time

        # Assertions
        assert total_count > 0
        assert count_time < 0.05  # Count should be very fast

        # Test filtered count
        start_time = time.time()
        filtered_count = repository.count({"is_private": False})
        end_time = time.time()

        filtered_count_time = end_time - start_time

        # Assertions
        assert filtered_count > 0
        assert filtered_count_time < 0.05  # Filtered count should also be fast

    def test_pagination_memory_efficiency(self, db_session: Session,
                                        sample_content: List[ContentItem]):
        """Test that pagination doesn't load unnecessary data into memory."""
        repository = ContentRepository(db_session)

        # Test small page size to ensure we're not loading everything
        pagination_request = PaginationRequest(page=1, page_size=5)

        result = repository.get_paginated(pagination_request)

        # Should only get 5 items, not all content
        assert len(result.items) == 5
        assert result.pagination.total_count > 5  # But total count should be higher

    @pytest.mark.slow
    @pytest.mark.skip(reason="Data scaling tests - Performance/stress testing (see scratchpads/issues/by_priority/low/data-scaling-tests.md)")
    def test_large_dataset_pagination_performance(self, db_session: Session):
        """Test pagination performance with a larger dataset."""
        # This test would create 10,000+ records to test real-world performance
        # Skip by default to avoid slow test runs

        # Create many users
        users = []
        for i in range(100):
            user = User(
                username=f"perf_user_{i:05d}",
                email=f"perf{i:05d}@example.com",
                created_at=datetime.utcnow() - timedelta(days=i % 365)
            )
            db_session.add(user)
            users.append(user)

        # Create many content items
        for i in range(10000):
            content = ContentItem(
                title=f"Performance Test Content {i:05d}",
                content_type=["text", "image", "video", "audio"][i % 4],
                content_data=f"Large dataset test content {i}",
                creator_id=users[i % len(users)].id,
                created_at=datetime.utcnow() - timedelta(hours=i % (24 * 30)),
                quality_score=(i % 100) / 100.0,
                is_private=i % 10 == 0
            )
            db_session.add(content)

        db_session.commit()

        repository = ContentRepository(db_session)

        # Test pagination at various points in the dataset
        test_pages = [1, 50, 100, 150, 200]  # Test different offsets

        for page_num in test_pages:
            pagination_request = PaginationRequest(page=page_num, page_size=50)

            start_time = time.time()
            result = repository.get_paginated(pagination_request)
            end_time = time.time()

            query_time = end_time - start_time

            # Even with large dataset, queries should complete quickly with proper indexes
            assert query_time < 0.5, f"Page {page_num} took {query_time:.3f}s - too slow!"
            assert len(result.items) > 0
            assert result.pagination.total_count >= 10000