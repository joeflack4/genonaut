"""DB integration tests for content_tags trigger that syncs tags to item_metadata."""
import pytest
from sqlalchemy.orm import Session
from uuid import uuid4

from genonaut.db.schema import User, ContentItem, ContentItemAuto, Tag, ContentTag


def test_trigger_adds_tag_to_item_metadata_regular(db_session: Session):
    """Test that INSERT trigger adds tag name to item_metadata.tags for regular content."""
    # Create user
    user = User(
        id=uuid4(),
        username="testuser",
        email="test@example.com",
        preferences={}
    )
    db_session.add(user)
    db_session.commit()

    # Create content item with empty metadata
    content = ContentItem(
        title="Test Image",
        content_type="image",
        content_data="/test.png",
        path_thumb="/thumb.png",
        prompt="Test prompt",
        creator_id=user.id,
        item_metadata={},  # Empty metadata initially
        is_private=False,
        quality_score=0.5
    )
    db_session.add(content)
    db_session.commit()

    # Create tag
    tag = Tag(name="test-tag")
    db_session.add(tag)
    db_session.commit()

    # Add tag to content via content_tags (should trigger metadata update)
    content_tag = ContentTag(
        content_id=content.id,
        tag_id=tag.id,
        content_source='regular'
    )
    db_session.add(content_tag)
    db_session.commit()

    # Refresh content to get updated metadata
    db_session.refresh(content)

    # Verify tag was added to item_metadata.tags
    assert 'tags' in content.item_metadata
    assert isinstance(content.item_metadata['tags'], list)
    assert 'test-tag' in content.item_metadata['tags']


def test_trigger_adds_tag_to_item_metadata_auto(db_session: Session):
    """Test that INSERT trigger adds tag name to item_metadata.tags for auto content."""
    # Create user
    user = User(
        id=uuid4(),
        username="testuser",
        email="test@example.com",
        preferences={}
    )
    db_session.add(user)
    db_session.commit()

    # Create auto content item
    content = ContentItemAuto(
        title="Auto Generated",
        content_type="image",
        content_data="/auto.png",
        path_thumb="/auto_thumb.png",
        prompt="Auto prompt",
        creator_id=user.id,
        item_metadata={},
        is_private=False,
        quality_score=0.7
    )
    db_session.add(content)
    db_session.commit()

    # Create tag
    tag = Tag(name="auto-tag")
    db_session.add(tag)
    db_session.commit()

    # Add tag to auto content
    content_tag = ContentTag(
        content_id=content.id,
        tag_id=tag.id,
        content_source='auto'
    )
    db_session.add(content_tag)
    db_session.commit()

    # Refresh to get updated metadata
    db_session.refresh(content)

    # Verify tag was added
    assert 'tags' in content.item_metadata
    assert 'auto-tag' in content.item_metadata['tags']


def test_trigger_removes_tag_from_item_metadata(db_session: Session):
    """Test that DELETE trigger removes tag name from item_metadata.tags."""
    # Create user
    user = User(
        id=uuid4(),
        username="testuser",
        email="test@example.com",
        preferences={}
    )
    db_session.add(user)
    db_session.commit()

    # Create content with tag in metadata
    content = ContentItem(
        title="Test Image",
        content_type="image",
        content_data="/test.png",
        path_thumb="/thumb.png",
        prompt="Test prompt",
        creator_id=user.id,
        item_metadata={'tags': ['tag1', 'tag2', 'tag3']},
        is_private=False,
        quality_score=0.5
    )
    db_session.add(content)
    db_session.commit()

    # Create tags
    tag1 = Tag(name="tag1")
    tag2 = Tag(name="tag2")
    tag3 = Tag(name="tag3")
    db_session.add_all([tag1, tag2, tag3])
    db_session.commit()

    # Add content_tags
    ct1 = ContentTag(content_id=content.id, tag_id=tag1.id, content_source='regular')
    ct2 = ContentTag(content_id=content.id, tag_id=tag2.id, content_source='regular')
    ct3 = ContentTag(content_id=content.id, tag_id=tag3.id, content_source='regular')
    db_session.add_all([ct1, ct2, ct3])
    db_session.commit()

    # Delete tag2 from content_tags (should trigger metadata update)
    db_session.delete(ct2)
    db_session.commit()

    # Refresh content
    db_session.refresh(content)

    # Verify tag2 was removed from metadata.tags
    assert 'tags' in content.item_metadata
    assert 'tag1' in content.item_metadata['tags']
    assert 'tag2' not in content.item_metadata['tags']
    assert 'tag3' in content.item_metadata['tags']


def test_trigger_prevents_duplicate_tags_in_metadata(db_session: Session):
    """Test that trigger doesn't add duplicate tags to item_metadata.tags."""
    # Create user
    user = User(
        id=uuid4(),
        username="testuser",
        email="test@example.com",
        preferences={}
    )
    db_session.add(user)
    db_session.commit()

    # Create content with tag already in metadata
    content = ContentItem(
        title="Test Image",
        content_type="image",
        content_data="/test.png",
        path_thumb="/thumb.png",
        prompt="Test prompt",
        creator_id=user.id,
        item_metadata={'tags': ['existing-tag']},
        is_private=False,
        quality_score=0.5
    )
    db_session.add(content)
    db_session.commit()

    # Create tag
    tag = Tag(name="existing-tag")
    db_session.add(tag)
    db_session.commit()

    # Try to add the same tag again via content_tags
    content_tag = ContentTag(
        content_id=content.id,
        tag_id=tag.id,
        content_source='regular'
    )
    db_session.add(content_tag)
    db_session.commit()

    # Refresh content
    db_session.refresh(content)

    # Verify there's still only one instance of the tag
    assert content.item_metadata['tags'].count('existing-tag') == 1


def test_trigger_handles_multiple_tags(db_session: Session):
    """Test that triggers correctly handle multiple tag additions and deletions."""
    # Create user
    user = User(
        id=uuid4(),
        username="testuser",
        email="test@example.com",
        preferences={}
    )
    db_session.add(user)
    db_session.commit()

    # Create content
    content = ContentItem(
        title="Multi-tag Test",
        content_type="image",
        content_data="/test.png",
        path_thumb="/thumb.png",
        prompt="Test",
        creator_id=user.id,
        item_metadata={},
        is_private=False,
        quality_score=0.5
    )
    db_session.add(content)
    db_session.commit()

    # Create multiple tags
    tags = [
        Tag(name=f"tag{i}")
        for i in range(5)
    ]
    db_session.add_all(tags)
    db_session.commit()

    # Add all tags to content
    for tag in tags:
        ct = ContentTag(
            content_id=content.id,
            tag_id=tag.id,
            content_source='regular'
        )
        db_session.add(ct)
    db_session.commit()

    # Refresh and verify all tags are in metadata
    db_session.refresh(content)
    assert len(content.item_metadata['tags']) == 5
    for i in range(5):
        assert f"tag{i}" in content.item_metadata['tags']

    # Remove some tags
    cts_to_delete = db_session.query(ContentTag).filter(
        ContentTag.content_id == content.id,
        ContentTag.tag_id.in_([tags[1].id, tags[3].id])
    ).all()

    for ct in cts_to_delete:
        db_session.delete(ct)
    db_session.commit()

    # Refresh and verify correct tags remain
    db_session.refresh(content)
    assert len(content.item_metadata['tags']) == 3
    assert 'tag0' in content.item_metadata['tags']
    assert 'tag1' not in content.item_metadata['tags']
    assert 'tag2' in content.item_metadata['tags']
    assert 'tag3' not in content.item_metadata['tags']
    assert 'tag4' in content.item_metadata['tags']
