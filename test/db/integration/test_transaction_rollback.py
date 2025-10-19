"""
Database integration tests for transaction rollback on errors.

Tests that database transactions properly rollback when errors occur.
"""
import pytest
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone
from uuid import uuid4
from genonaut.db.schema import User, ContentItem, Tag


@pytest.mark.db_integration
def test_transaction_rollback_on_integrity_error(db_session):
    """Test that transaction rolls back on integrity constraint violation.

    Note: With PostgreSQL, we need to use an explicit savepoint before
    error-prone operations to avoid rolling back the entire transaction.
    """
    # Create a test tag
    tag1 = Tag(name="test_tag_1", tag_metadata={})
    db_session.add(tag1)
    db_session.commit()

    initial_count = db_session.query(Tag).count()

    # Try to create tag with duplicate name (should fail due to unique constraint)
    # Use explicit savepoint to isolate the error
    savepoint = db_session.begin_nested()
    try:
        tag2 = Tag(name="test_tag_1", tag_metadata={})  # Duplicate name
        db_session.add(tag2)
        db_session.commit()
    except IntegrityError:
        # Roll back to the savepoint (not the entire transaction)
        savepoint.rollback()

    # Count should remain unchanged after rollback
    final_count = db_session.query(Tag).count()
    assert final_count == initial_count


@pytest.mark.db_integration
def test_transaction_rollback_preserves_data(db_session):
    """Test that rolled back transactions don't affect existing data.

    Note: With PostgreSQL, we need to use an explicit savepoint before
    error-prone operations to avoid rolling back the entire transaction.
    """
    # Create initial tag
    tag = Tag(
        name="test_tag",
        tag_metadata={"description": "test description"}
    )

    db_session.add(tag)
    db_session.commit()

    initial_tag_count = db_session.query(Tag).count()

    # Start a transaction that will fail
    # Use explicit savepoint to isolate the error
    savepoint = db_session.begin_nested()
    try:
        # Add some operations
        new_tag = Tag(
            name="new_tag",
            tag_metadata={"description": "new description"}
        )
        db_session.add(new_tag)

        # Force an error by trying to add duplicate
        duplicate_tag = Tag(
            name="test_tag",  # Duplicate name (should fail due to unique constraint)
            tag_metadata={"description": "duplicate"}
        )
        db_session.add(duplicate_tag)

        db_session.commit()

    except Exception:
        # Roll back to the savepoint (not the entire transaction)
        savepoint.rollback()

    # Original data should still be intact
    final_tag_count = db_session.query(Tag).count()

    # After rollback, only the original tag should exist
    assert final_tag_count == initial_tag_count


@pytest.mark.db_integration
def test_explicit_rollback(db_session):
    """Test explicit transaction rollback."""
    # Create a test user
    user = User(id=uuid4(), username="testuser", email="test@example.com", preferences={})
    db_session.add(user)
    db_session.commit()

    initial_count = db_session.query(ContentItem).count()

    # Add an item but don't commit
    content = ContentItem(
        title="Temp Content",
        content_type="image",
        content_data="/test/temp.png",
        path_thumb="/thumb_temp.png",
        prompt="test",
        creator_id=user.id,
        item_metadata={},
        is_private=False,
        quality_score=0.5
    )

    db_session.add(content)

    # Explicitly roll back
    db_session.rollback()

    # Item should not exist in database
    final_count = db_session.query(ContentItem).count()
    assert final_count == initial_count


@pytest.mark.db_integration
def test_nested_transaction_rollback(db_session):
    """Test that nested transactions (savepoints) work correctly."""
    # Create a test user
    user = User(id=uuid4(), username="testuser", email="test@example.com", preferences={})
    db_session.add(user)
    db_session.commit()

    initial_count = db_session.query(ContentItem).count()

    # Create outer transaction
    content1 = ContentItem(
        title="Content 1",
        content_type="image",
        content_data="/test/content1.png",
        path_thumb="/thumb1.png",
        prompt="test",
        creator_id=user.id,
        item_metadata={},
        is_private=False,
        quality_score=0.8
    )

    db_session.add(content1)

    # Create a savepoint (nested transaction)
    savepoint = db_session.begin_nested()

    try:
        content2 = ContentItem(
            title="Content 2",
            content_type="image",
            content_data="/test/content2.png",
            path_thumb="/thumb2.png",
            prompt="test",
            creator_id=user.id,
            item_metadata={},
            is_private=False,
            quality_score=0.7
        )

        db_session.add(content2)

        # Roll back to savepoint
        savepoint.rollback()

    except Exception:
        pass

    # Commit outer transaction
    db_session.commit()

    # Only content1 should exist
    final_count = db_session.query(ContentItem).count()
    assert final_count == initial_count + 1


@pytest.mark.db_integration
def test_rollback_after_query_error(db_session):
    """Test that session can recover after a query error."""
    from sqlalchemy import text

    # Execute an invalid query
    try:
        db_session.execute(text("SELECT * FROM nonexistent_table"))
    except Exception:
        db_session.rollback()

    # Session should be usable after rollback
    count = db_session.query(ContentItem).count()
    assert count >= 0  # Should succeed
