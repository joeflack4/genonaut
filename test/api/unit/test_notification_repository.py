"""Unit tests for NotificationRepository."""

import pytest
from datetime import datetime
from uuid import uuid4

from genonaut.api.repositories.notification_repository import NotificationRepository
from genonaut.db.schema import UserNotification, User
from genonaut.api.models.enums import NotificationType
from genonaut.api.exceptions import DatabaseError


@pytest.fixture
def test_user(test_db_session):
    """Create a test user."""
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
def notification_repository(test_db_session):
    """Create notification repository instance."""
    return NotificationRepository(test_db_session)


class TestNotificationRepository:
    """Tests for NotificationRepository."""

    def test_create_notification(self, notification_repository, test_user):
        """Test creating a notification."""
        notification_data = {
            'user_id': test_user.id,
            'title': 'Test Notification',
            'message': 'This is a test notification',
            'notification_type': NotificationType.JOB_COMPLETED.value,
            'read_status': False
        }

        notification = notification_repository.create(notification_data)

        assert notification.id is not None
        assert notification.user_id == test_user.id
        assert notification.title == 'Test Notification'
        assert notification.message == 'This is a test notification'
        assert notification.notification_type == NotificationType.JOB_COMPLETED.value
        assert notification.read_status is False
        assert notification.created_at is not None

    def test_get_user_notifications(self, notification_repository, test_user, test_db_session):
        """Test getting user notifications."""
        # Create multiple notifications
        for i in range(5):
            notification = UserNotification(
                user_id=test_user.id,
                title=f'Notification {i}',
                message=f'Message {i}',
                notification_type=NotificationType.JOB_COMPLETED.value,
                read_status=i % 2 == 0  # Every other one is read
            )
            test_db_session.add(notification)
        test_db_session.commit()

        # Get all notifications
        notifications = notification_repository.get_user_notifications(test_user.id, skip=0, limit=10)
        assert len(notifications) == 5

        # Get unread only
        unread = notification_repository.get_user_notifications(test_user.id, skip=0, limit=10, unread_only=True)
        assert len(unread) == 2  # Indices 1 and 3

    def test_get_unread_count(self, notification_repository, test_user, test_db_session):
        """Test getting unread notification count."""
        # Create notifications
        for i in range(3):
            notification = UserNotification(
                user_id=test_user.id,
                title=f'Notification {i}',
                message=f'Message {i}',
                notification_type=NotificationType.JOB_COMPLETED.value,
                read_status=i == 0  # Only first one is read
            )
            test_db_session.add(notification)
        test_db_session.commit()

        count = notification_repository.get_unread_count(test_user.id)
        assert count == 2

    def test_mark_as_read(self, notification_repository, test_user, test_db_session):
        """Test marking notification as read."""
        notification = UserNotification(
            user_id=test_user.id,
            title='Test',
            message='Test message',
            notification_type=NotificationType.JOB_COMPLETED.value,
            read_status=False
        )
        test_db_session.add(notification)
        test_db_session.commit()

        # Mark as read
        updated = notification_repository.mark_as_read(notification.id, test_user.id)

        assert updated is not None
        assert updated.read_status is True
        assert updated.read_at is not None

    def test_mark_all_as_read(self, notification_repository, test_user, test_db_session):
        """Test marking all notifications as read."""
        # Create unread notifications
        for i in range(3):
            notification = UserNotification(
                user_id=test_user.id,
                title=f'Notification {i}',
                message=f'Message {i}',
                notification_type=NotificationType.JOB_COMPLETED.value,
                read_status=False
            )
            test_db_session.add(notification)
        test_db_session.commit()

        count = notification_repository.mark_all_as_read(test_user.id)
        assert count == 3

        # Verify all are read
        unread_count = notification_repository.get_unread_count(test_user.id)
        assert unread_count == 0

    def test_delete_notification(self, notification_repository, test_user, test_db_session):
        """Test deleting a notification."""
        notification = UserNotification(
            user_id=test_user.id,
            title='Test',
            message='Test message',
            notification_type=NotificationType.JOB_COMPLETED.value
        )
        test_db_session.add(notification)
        test_db_session.commit()
        notification_id = notification.id

        # Delete notification
        deleted = notification_repository.delete_notification(notification_id, test_user.id)
        assert deleted is True

        # Verify it's gone
        notifications = notification_repository.get_user_notifications(test_user.id)
        assert len(notifications) == 0

    def test_get_by_type(self, notification_repository, test_user, test_db_session):
        """Test getting notifications by type."""
        # Create notifications of different types
        types = [NotificationType.JOB_COMPLETED, NotificationType.JOB_FAILED, NotificationType.JOB_COMPLETED]
        for notification_type in types:
            notification = UserNotification(
                user_id=test_user.id,
                title='Test',
                message='Test message',
                notification_type=notification_type.value
            )
            test_db_session.add(notification)
        test_db_session.commit()

        # Get completed notifications only
        completed = notification_repository.get_by_type(
            test_user.id,
            NotificationType.JOB_COMPLETED.value,
            skip=0,
            limit=10
        )
        assert len(completed) == 2

        # Get failed notifications only
        failed = notification_repository.get_by_type(
            test_user.id,
            NotificationType.JOB_FAILED.value,
            skip=0,
            limit=10
        )
        assert len(failed) == 1
