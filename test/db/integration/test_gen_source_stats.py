"""Integration tests for GenSourceStats repository method.

IMPORTANT: These tests require a properly initialized database.
Run with: DB_NAME=genonaut_demo pytest test/db/integration/test_gen_source_stats.py
"""

import pytest
from uuid import uuid4
from datetime import datetime
from sqlalchemy import text

from genonaut.db.schema import (
    Base,
    User,
    ContentItem,
    ContentItemAuto,
    GenSourceStats,
    UserInteraction,
    GenerationJob,
)
from genonaut.api.repositories.content_repository import ContentRepository
from genonaut.api.exceptions import DatabaseError


@pytest.fixture(scope="function", autouse=True)
def ensure_gen_source_stats_table(db_session):
    """Ensure gen_source_stats table exists before running tests.

    This is a workaround for the known migration issue where migration 94c538597cde
    tries to ALTER the gen_source_stats table before it exists.
    """
    # Check if table exists
    result = db_session.execute(
        text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'gen_source_stats'
            );
        """)
    )
    table_exists = result.scalar()

    if not table_exists:
        # Create the table manually (without FK to avoid dependency issues)
        # Note: The FK will be added by migrations in a properly initialized DB
        db_session.execute(text("""
            CREATE TABLE IF NOT EXISTS gen_source_stats (
                id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                user_id UUID,
                source_type VARCHAR(10) NOT NULL,
                count INTEGER NOT NULL,
                updated_at TIMESTAMP NOT NULL
            );

            CREATE UNIQUE INDEX IF NOT EXISTS idx_gen_source_stats_community
            ON gen_source_stats (source_type) WHERE user_id IS NULL;

            CREATE UNIQUE INDEX IF NOT EXISTS idx_gen_source_stats_user_src
            ON gen_source_stats (user_id, source_type) WHERE user_id IS NOT NULL;
        """))
        db_session.commit()


@pytest.fixture(scope="function", autouse=True)
def clean_database(db_session):
    """Clean all data before each test to ensure isolation.

    These tests verify statistics computed from the ENTIRE database,
    so they need a completely clean slate. This fixture truncates all
    relevant tables before each test.
    """
    # Delete all tables in dependency order (children first, then parents)
    # Some tables don't have ORM models, so we use raw SQL

    # Level 1: Tables that reference content items or users (deepest children)
    db_session.execute(text("DELETE FROM bookmark_categories"))
    db_session.execute(text("DELETE FROM bookmarks"))
    db_session.execute(text("DELETE FROM content_items_ext"))
    db_session.execute(text("DELETE FROM content_items_auto_ext"))
    db_session.execute(text("DELETE FROM flagged_content"))
    db_session.execute(text("DELETE FROM route_analytics"))
    db_session.execute(text("DELETE FROM user_search_history"))
    db_session.execute(text("DELETE FROM user_notifications"))
    db_session.execute(text("DELETE FROM tag_ratings"))

    # Level 2: Tables specific to this test
    db_session.query(GenSourceStats).delete()
    db_session.query(UserInteraction).delete()
    db_session.query(GenerationJob).delete()

    # Level 3: Content tables (before users since users are creators)
    db_session.query(ContentItemAuto).delete()
    db_session.query(ContentItem).delete()

    # Level 4: Users (root level)
    db_session.query(User).delete()

    db_session.commit()

    yield

    # No cleanup needed - postgres_session fixture handles rollback


@pytest.fixture
def repository(db_session):
    """Create ContentRepository instance."""
    return ContentRepository(db_session)


@pytest.fixture
def sample_users(db_session):
    """Create sample users for testing.

    Note: No cleanup is needed because the postgres_session fixture provides
    automatic rollback via savepoints. Any data created during the test will be
    automatically rolled back after the test completes. Explicit deletes would
    bypass this protection and could delete seed data.
    """
    # Create users
    users = []
    for i in range(3):
        unique_suffix = uuid4().hex[:8]
        user = User(
            username=f"testuser-{i}-{unique_suffix}",
            email=f"test-{i}-{unique_suffix}@example.com",
        )
        db_session.add(user)
        users.append(user)

    db_session.commit()
    return users


@pytest.fixture
def sample_content(db_session, sample_users):
    """Create sample content items."""
    # User 0: 5 regular, 3 auto
    for i in range(5):
        item = ContentItem(
            title=f"Regular content {i}",
            content_type="image",
            content_data=f"/path/to/image{i}.jpg",
            prompt=f"Test prompt {i}",
            creator_id=sample_users[0].id,
            created_at=datetime.utcnow(),
        )
        db_session.add(item)

    for i in range(3):
        item = ContentItemAuto(
            title=f"Auto content {i}",
            content_type="image",
            content_data=f"/path/to/auto{i}.jpg",
            prompt=f"Test auto prompt {i}",
            creator_id=sample_users[0].id,
            created_at=datetime.utcnow(),
        )
        db_session.add(item)

    # User 1: 2 regular, 0 auto
    for i in range(2):
        item = ContentItem(
            title=f"User1 content {i}",
            content_type="image",
            content_data=f"/path/to/user1-{i}.jpg",
            prompt=f"User1 prompt {i}",
            creator_id=sample_users[1].id,
            created_at=datetime.utcnow(),
        )
        db_session.add(item)

    # User 2: 0 regular, 4 auto
    for i in range(4):
        item = ContentItemAuto(
            title=f"User2 auto {i}",
            content_type="image",
            content_data=f"/path/to/user2-auto{i}.jpg",
            prompt=f"User2 auto prompt {i}",
            creator_id=sample_users[2].id,
            created_at=datetime.utcnow(),
        )
        db_session.add(item)

    db_session.commit()


class TestRefreshGenSourceStats:
    """Test refresh_gen_source_stats repository method."""

    def test_refresh_gen_source_stats_empty_database(self, repository, db_session):
        """Test refreshing stats with no content.

        Note: The clean_database fixture already ensures we start with an empty database.
        """
        # Refresh
        count = repository.refresh_gen_source_stats()

        # Should return 0 stats created (no content exists)
        assert count == 0

        # Verify no stats were created
        stats = db_session.query(GenSourceStats).all()
        assert len(stats) == 0

    def test_refresh_gen_source_stats_community_stats(
        self, repository, db_session, sample_content, sample_users
    ):
        """Test that community stats (NULL user_id) are created correctly."""
        count = repository.refresh_gen_source_stats()

        # Get community stats (user_id is NULL)
        community_stats = (
            db_session.query(GenSourceStats)
            .filter(GenSourceStats.user_id.is_(None))
            .all()
        )

        # Should have 2 community stats: regular and auto
        assert len(community_stats) == 2

        # Find stats by source_type
        regular_stat = next(s for s in community_stats if s.source_type == "regular")
        auto_stat = next(s for s in community_stats if s.source_type == "auto")

        # Community regular: user0(5) + user1(2) = 7
        assert regular_stat.count == 7

        # Community auto: user0(3) + user2(4) = 7
        assert auto_stat.count == 7

    def test_refresh_gen_source_stats_per_user_stats(
        self, repository, db_session, sample_content, sample_users
    ):
        """Test that per-user stats are created correctly."""
        count = repository.refresh_gen_source_stats()

        # Get user-specific stats
        user_stats = (
            db_session.query(GenSourceStats)
            .filter(GenSourceStats.user_id.isnot(None))
            .all()
        )

        # Should have stats for users who created content
        # User 0: regular + auto = 2 stats
        # User 1: regular only = 1 stat
        # User 2: auto only = 1 stat
        # Total: 4 user stats
        assert len(user_stats) == 4

        # User 0 stats
        user0_stats = [s for s in user_stats if s.user_id == sample_users[0].id]
        assert len(user0_stats) == 2
        user0_regular = next(s for s in user0_stats if s.source_type == "regular")
        user0_auto = next(s for s in user0_stats if s.source_type == "auto")
        assert user0_regular.count == 5
        assert user0_auto.count == 3

        # User 1 stats
        user1_stats = [s for s in user_stats if s.user_id == sample_users[1].id]
        assert len(user1_stats) == 1
        assert user1_stats[0].source_type == "regular"
        assert user1_stats[0].count == 2

        # User 2 stats
        user2_stats = [s for s in user_stats if s.user_id == sample_users[2].id]
        assert len(user2_stats) == 1
        assert user2_stats[0].source_type == "auto"
        assert user2_stats[0].count == 4

    def test_refresh_gen_source_stats_total_count(
        self, repository, db_session, sample_content
    ):
        """Test that refresh returns correct total count."""
        count = repository.refresh_gen_source_stats()

        # Expected:
        # - 2 community stats (regular, auto)
        # - 4 user stats (user0: 2, user1: 1, user2: 1)
        # Total: 6
        assert count == 6

        # Verify actual count in database
        stats = db_session.query(GenSourceStats).all()
        assert len(stats) == 6

    def test_refresh_gen_source_stats_idempotency(
        self, repository, db_session, sample_content
    ):
        """Test that multiple refreshes produce same results."""
        # First refresh
        count1 = repository.refresh_gen_source_stats()
        stats1 = db_session.query(GenSourceStats).all()

        # Second refresh
        count2 = repository.refresh_gen_source_stats()
        stats2 = db_session.query(GenSourceStats).all()

        # Should produce same results
        assert count1 == count2
        assert len(stats1) == len(stats2)

        # Verify counts match
        for stat in stats2:
            if stat.user_id is None:
                # Community stat
                matching = [
                    s
                    for s in stats1
                    if s.user_id is None and s.source_type == stat.source_type
                ]
                assert len(matching) == 1
                assert matching[0].count == stat.count
            else:
                # User stat
                matching = [
                    s
                    for s in stats1
                    if s.user_id == stat.user_id and s.source_type == stat.source_type
                ]
                assert len(matching) == 1
                assert matching[0].count == stat.count

    def test_refresh_gen_source_stats_after_content_change(
        self, repository, db_session, sample_content, sample_users
    ):
        """Test that refresh picks up changes in content counts."""
        # Initial refresh
        count1 = repository.refresh_gen_source_stats()

        # Add more content for user 0
        for i in range(3):
            item = ContentItem(
                title=f"New content {i}",
                content_type="image",
                content_data=f"/path/to/new{i}.jpg",
                prompt=f"New prompt {i}",
                creator_id=sample_users[0].id,
                created_at=datetime.utcnow(),
            )
            db_session.add(item)
        db_session.commit()

        # Refresh again
        count2 = repository.refresh_gen_source_stats()

        # Get user 0's regular stat
        user0_regular = (
            db_session.query(GenSourceStats)
            .filter(
                GenSourceStats.user_id == sample_users[0].id,
                GenSourceStats.source_type == "regular",
            )
            .first()
        )

        # Should now have 5 + 3 = 8
        assert user0_regular.count == 8

        # Community regular should also increase: 7 + 3 = 10
        community_regular = (
            db_session.query(GenSourceStats)
            .filter(
                GenSourceStats.user_id.is_(None),
                GenSourceStats.source_type == "regular",
            )
            .first()
        )
        assert community_regular.count == 10

    def test_refresh_gen_source_stats_updated_at(
        self, repository, db_session, sample_content
    ):
        """Test that updated_at timestamp is set."""
        repository.refresh_gen_source_stats()

        stats = db_session.query(GenSourceStats).all()

        # All stats should have updated_at timestamp
        for stat in stats:
            assert stat.updated_at is not None
            assert isinstance(stat.updated_at, datetime)

    def test_refresh_gen_source_stats_unique_constraints(
        self, repository, db_session, sample_content, sample_users
    ):
        """Test that unique constraints are respected."""
        # Refresh twice
        repository.refresh_gen_source_stats()
        repository.refresh_gen_source_stats()

        # Get all stats
        stats = db_session.query(GenSourceStats).all()

        # Check no duplicates exist
        # For community stats
        community_regular_count = (
            db_session.query(GenSourceStats)
            .filter(
                GenSourceStats.user_id.is_(None),
                GenSourceStats.source_type == "regular",
            )
            .count()
        )
        assert community_regular_count == 1

        community_auto_count = (
            db_session.query(GenSourceStats)
            .filter(
                GenSourceStats.user_id.is_(None), GenSourceStats.source_type == "auto"
            )
            .count()
        )
        assert community_auto_count == 1

        # For user stats
        for user in sample_users:
            user_regular_count = (
                db_session.query(GenSourceStats)
                .filter(
                    GenSourceStats.user_id == user.id,
                    GenSourceStats.source_type == "regular",
                )
                .count()
            )
            # Should be 0 or 1
            assert user_regular_count in [0, 1]

            user_auto_count = (
                db_session.query(GenSourceStats)
                .filter(
                    GenSourceStats.user_id == user.id,
                    GenSourceStats.source_type == "auto",
                )
                .count()
            )
            # Should be 0 or 1
            assert user_auto_count in [0, 1]

    def test_refresh_gen_source_stats_only_creates_nonzero(
        self, repository, db_session, sample_users
    ):
        """Test that only non-zero stats are created."""
        # Create content for only one user, only regular content
        item = ContentItem(
            title="Single item",
            content_type="image",
            content_data="/path/to/single.jpg",
            prompt="Single prompt",
            creator_id=sample_users[0].id,
            created_at=datetime.utcnow(),
        )
        db_session.add(item)
        db_session.commit()

        # Refresh
        count = repository.refresh_gen_source_stats()

        # Should have:
        # - 1 community regular stat (count=1)
        # - 1 user0 regular stat (count=1)
        # - 0 auto stats (no auto content)
        # Total: 2
        assert count == 2

        stats = db_session.query(GenSourceStats).all()
        assert len(stats) == 2

        # Verify all stats have count > 0
        for stat in stats:
            assert stat.count > 0
            assert stat.source_type == "regular"

    def test_refresh_gen_source_stats_no_users_with_content(
        self, repository, db_session
    ):
        """Test refreshing when users exist but have no content.

        Note: The clean_database fixture already ensures we start with an empty database.
        """
        user = User(
            username=f"testuser-{uuid4().hex[:8]}",
            email=f"test-{uuid4().hex[:8]}@example.com",
        )
        db_session.add(user)
        db_session.commit()

        # Refresh
        count = repository.refresh_gen_source_stats()

        # Should have 0 stats (no content)
        assert count == 0

        stats = db_session.query(GenSourceStats).all()
        assert len(stats) == 0
