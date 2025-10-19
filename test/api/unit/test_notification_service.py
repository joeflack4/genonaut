"""Unit tests for NotificationService."""

import pytest
from uuid import uuid4

from genonaut.api.services.notification_service import NotificationService
from genonaut.db.schema import User, ContentItem, GenerationJob
from genonaut.api.models.enums import NotificationType
from genonaut.api.exceptions import EntityNotFoundError, ValidationError


@pytest.fixture
def test_user_with_notifications_enabled(test_db_session):
    """Create a test user with notifications enabled."""
    user = User(
        id=uuid4(),
        username="testuser",
        email="test@example.com",
        preferences={"notifications_enabled": True}
    )
    test_db_session.add(user)
    test_db_session.commit()
    return user


@pytest.fixture
def test_user_with_notifications_disabled(test_db_session):
    """Create a test user with notifications disabled."""
    user = User(
        id=uuid4(),
        username="testuser2",
        email="test2@example.com",
        preferences={"notifications_enabled": False}
    )
    test_db_session.add(user)
    test_db_session.commit()
    return user


@pytest.fixture
def notification_service(test_db_session):
    """Create notification service instance."""
    return NotificationService(test_db_session)


@pytest.fixture
def test_content_item(test_db_session, test_user_with_notifications_enabled):
    """Create a test content item for notifications."""
    content = ContentItem(
        title="Test Content",
        content_type="image",
        content_data="/path/to/test.jpg",
        creator_id=test_user_with_notifications_enabled.id,
        prompt="test prompt"
    )
    test_db_session.add(content)
    test_db_session.commit()
    test_db_session.refresh(content)
    return content


@pytest.fixture
def test_generation_job(test_db_session, test_user_with_notifications_enabled):
    """Create a test generation job for notifications."""
    job = GenerationJob(
        user_id=test_user_with_notifications_enabled.id,
        job_type="image",
        prompt="test prompt",
        params={"test": True},
        status="completed"
    )
    test_db_session.add(job)
    test_db_session.commit()
    test_db_session.refresh(job)
    return job


class TestNotificationService:
    """Tests for NotificationService."""

    def test_create_notification(self, notification_service, test_user_with_notifications_enabled):
        """Test creating a notification."""
        notification = notification_service.create_notification(
            user_id=test_user_with_notifications_enabled.id,
            title="Test Notification",
            message="This is a test",
            notification_type=NotificationType.JOB_COMPLETED
        )

        assert notification is not None
        assert notification.title == "Test Notification"
        assert notification.message == "This is a test"
        assert notification.notification_type == NotificationType.JOB_COMPLETED.value

    def test_create_notification_user_disabled(self, notification_service, test_user_with_notifications_disabled):
        """Test creating notification when user has notifications disabled."""
        notification = notification_service.create_notification(
            user_id=test_user_with_notifications_disabled.id,
            title="Test Notification",
            message="This is a test",
            notification_type=NotificationType.JOB_COMPLETED
        )

        assert notification is None

    def test_create_notification_invalid_user(self, notification_service):
        """Test creating notification for non-existent user."""
        with pytest.raises(EntityNotFoundError):
            notification_service.create_notification(
                user_id=uuid4(),
                title="Test",
                message="Test message",
                notification_type=NotificationType.JOB_COMPLETED
            )

    def test_create_notification_empty_title(self, notification_service, test_user_with_notifications_enabled):
        """Test creating notification with empty title."""
        with pytest.raises(ValidationError):
            notification_service.create_notification(
                user_id=test_user_with_notifications_enabled.id,
                title="",
                message="Test message",
                notification_type=NotificationType.JOB_COMPLETED
            )

    def test_create_notification_empty_message(self, notification_service, test_user_with_notifications_enabled):
        """Test creating notification with empty message."""
        with pytest.raises(ValidationError):
            notification_service.create_notification(
                user_id=test_user_with_notifications_enabled.id,
                title="Test",
                message="",
                notification_type=NotificationType.JOB_COMPLETED
            )

    def test_create_job_completion_notification(self, notification_service, test_user_with_notifications_enabled, test_generation_job, test_content_item):
        """Test creating job completion notification."""
        notification = notification_service.create_job_completion_notification(
            user_id=test_user_with_notifications_enabled.id,
            job_id=test_generation_job.id,
            content_id=test_content_item.id
        )

        assert notification is not None
        assert notification.title == "Generation Complete"
        assert notification.notification_type == NotificationType.JOB_COMPLETED.value
        assert notification.related_job_id == test_generation_job.id
        assert notification.related_content_id == test_content_item.id

    def test_get_user_notifications_filtered(self, notification_service, test_user_with_notifications_enabled):
        """Test listing notifications with type filters."""
        # Create notifications of different types
        notification_service.create_notification(
            user_id=test_user_with_notifications_enabled.id,
            title="Completed",
            message="Completed message",
            notification_type=NotificationType.JOB_COMPLETED,
        )
        notification_service.create_notification(
            user_id=test_user_with_notifications_enabled.id,
            title="Failed",
            message="Failed message",
            notification_type=NotificationType.JOB_FAILED,
        )

        notifications = notification_service.get_user_notifications(
            user_id=test_user_with_notifications_enabled.id,
            notification_types=[NotificationType.JOB_COMPLETED.value],
        )

        assert len(notifications) == 1
        assert notifications[0].notification_type == NotificationType.JOB_COMPLETED.value

    def test_count_user_notifications(self, notification_service, test_user_with_notifications_enabled):
        """Test counting notifications with filters."""
        notification_service.create_notification(
            user_id=test_user_with_notifications_enabled.id,
            title="Completed",
            message="Completed message",
            notification_type=NotificationType.JOB_COMPLETED,
        )
        notification_service.create_notification(
            user_id=test_user_with_notifications_enabled.id,
            title="Failed",
            message="Failed message",
            notification_type=NotificationType.JOB_FAILED,
        )

        total = notification_service.count_user_notifications(test_user_with_notifications_enabled.id)
        filtered = notification_service.count_user_notifications(
            test_user_with_notifications_enabled.id,
            notification_types=[NotificationType.JOB_COMPLETED.value],
        )

        assert total == 2
        assert filtered == 1

    def test_get_notification(self, notification_service, test_user_with_notifications_enabled):
        """Test retrieving a single notification by ID."""
        notification = notification_service.create_notification(
            user_id=test_user_with_notifications_enabled.id,
            title="Detail",
            message="Detail message",
            notification_type=NotificationType.SYSTEM,
        )

        fetched = notification_service.get_notification(notification.id, test_user_with_notifications_enabled.id)
        assert fetched.id == notification.id
        assert fetched.notification_type == NotificationType.SYSTEM.value

    def test_get_notification_not_found(self, notification_service, test_user_with_notifications_enabled):
        """Test retrieving notification that does not exist."""
        with pytest.raises(EntityNotFoundError):
            notification_service.get_notification(99999, test_user_with_notifications_enabled.id)

    def test_create_job_failure_notification(self, notification_service, test_user_with_notifications_enabled, test_generation_job):
        """Test creating job failure notification."""
        notification = notification_service.create_job_failure_notification(
            user_id=test_user_with_notifications_enabled.id,
            job_id=test_generation_job.id,
            error_message="Test error"
        )

        assert notification is not None
        assert notification.title == "Generation Failed"
        assert "Test error" in notification.message
        assert notification.notification_type == NotificationType.JOB_FAILED.value
        assert notification.related_job_id == test_generation_job.id

    def test_mark_notification_read(self, notification_service, test_user_with_notifications_enabled):
        """Test marking notification as read."""
        notification = notification_service.create_notification(
            user_id=test_user_with_notifications_enabled.id,
            title="Test",
            message="Test message",
            notification_type=NotificationType.JOB_COMPLETED
        )

        updated = notification_service.mark_notification_read(notification.id, test_user_with_notifications_enabled.id)
        assert updated.read_status is True
        assert updated.read_at is not None

    def test_mark_notification_unread(self, notification_service, test_user_with_notifications_enabled):
        """Test marking notification as unread."""
        notification = notification_service.create_notification(
            user_id=test_user_with_notifications_enabled.id,
            title="Test",
            message="Test message",
            notification_type=NotificationType.JOB_COMPLETED
        )

        updated_read = notification_service.mark_notification_read(notification.id, test_user_with_notifications_enabled.id)
        assert updated_read.read_status is True

        updated_unread = notification_service.mark_notification_unread(notification.id, test_user_with_notifications_enabled.id)
        assert updated_unread.read_status is False
        assert updated_unread.read_at is None

    def test_mark_notification_read_not_found(self, notification_service, test_user_with_notifications_enabled):
        """Test marking non-existent notification as read."""
        with pytest.raises(EntityNotFoundError):
            notification_service.mark_notification_read(99999, test_user_with_notifications_enabled.id)

    def test_mark_all_read(self, notification_service, test_user_with_notifications_enabled):
        """Test marking all notifications as read."""
        # Create multiple notifications
        for i in range(3):
            notification_service.create_notification(
                user_id=test_user_with_notifications_enabled.id,
                title=f"Test {i}",
                message=f"Message {i}",
                notification_type=NotificationType.JOB_COMPLETED
            )

        count = notification_service.mark_all_read(test_user_with_notifications_enabled.id)
        assert count == 3

        # Verify
        unread_count = notification_service.get_unread_count(test_user_with_notifications_enabled.id)
        assert unread_count == 0

    def test_delete_notification(self, notification_service, test_user_with_notifications_enabled):
        """Test deleting a notification."""
        notification = notification_service.create_notification(
            user_id=test_user_with_notifications_enabled.id,
            title="Test",
            message="Test message",
            notification_type=NotificationType.JOB_COMPLETED
        )

        deleted = notification_service.delete_notification(notification.id, test_user_with_notifications_enabled.id)
        assert deleted is True

    def test_delete_notification_not_found(self, notification_service, test_user_with_notifications_enabled):
        """Test deleting non-existent notification."""
        with pytest.raises(EntityNotFoundError):
            notification_service.delete_notification(99999, test_user_with_notifications_enabled.id)
