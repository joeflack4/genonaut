"""Unit tests for NotificationService."""

import pytest
from uuid import uuid4

from genonaut.api.services.notification_service import NotificationService
from genonaut.db.schema import User
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

    def test_create_job_completion_notification(self, notification_service, test_user_with_notifications_enabled):
        """Test creating job completion notification."""
        notification = notification_service.create_job_completion_notification(
            user_id=test_user_with_notifications_enabled.id,
            job_id=123,
            content_id=456
        )

        assert notification is not None
        assert notification.title == "Generation Complete"
        assert notification.notification_type == NotificationType.JOB_COMPLETED.value
        assert notification.related_job_id == 123
        assert notification.related_content_id == 456

    def test_create_job_failure_notification(self, notification_service, test_user_with_notifications_enabled):
        """Test creating job failure notification."""
        notification = notification_service.create_job_failure_notification(
            user_id=test_user_with_notifications_enabled.id,
            job_id=123,
            error_message="Test error"
        )

        assert notification is not None
        assert notification.title == "Generation Failed"
        assert "Test error" in notification.message
        assert notification.notification_type == NotificationType.JOB_FAILED.value
        assert notification.related_job_id == 123

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
