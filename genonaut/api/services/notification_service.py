"""Notification service for business logic."""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from genonaut.db.schema import UserNotification, User
from genonaut.api.repositories.notification_repository import NotificationRepository
from genonaut.api.repositories.user_repository import UserRepository
from genonaut.api.models.enums import NotificationType
from genonaut.api.exceptions import EntityNotFoundError, ValidationError


class NotificationService:
    """Service for notification business logic."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = NotificationRepository(db)
        self.user_repository = UserRepository(db)

    def create_notification(
        self,
        user_id: UUID,
        title: str,
        message: str,
        notification_type: NotificationType,
        related_job_id: Optional[int] = None,
        related_content_id: Optional[int] = None
    ) -> UserNotification:
        """Create a new notification.

        Args:
            user_id: User ID to create notification for
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            related_job_id: Optional related generation job ID
            related_content_id: Optional related content item ID

        Returns:
            Created UserNotification instance

        Raises:
            EntityNotFoundError: If user not found
            ValidationError: If validation fails
        """
        # Verify user exists
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise EntityNotFoundError("User", str(user_id))

        # Check if user has notifications enabled
        preferences = user.preferences or {}
        if not preferences.get('notifications_enabled', False):
            # User has notifications disabled, don't create notification
            return None

        # Validate inputs
        if not title or not title.strip():
            raise ValidationError("Notification title cannot be empty")
        if not message or not message.strip():
            raise ValidationError("Notification message cannot be empty")

        # Create notification
        notification_data = {
            'user_id': user_id,
            'title': title.strip(),
            'message': message.strip(),
            'notification_type': notification_type.value if isinstance(notification_type, NotificationType) else notification_type,
            'related_job_id': related_job_id,
            'related_content_id': related_content_id,
            'read_status': False
        }

        return self.repository.create(notification_data)

    def get_user_notifications(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 10,
        unread_only: bool = False,
        notification_types: Optional[List[str]] = None
    ) -> List[UserNotification]:
        """Get paginated notifications for a user.

        Args:
            user_id: User ID to get notifications for
            skip: Number of records to skip
            limit: Maximum number of records to return
            unread_only: If True, only return unread notifications
            notification_types: Optional list of notification types to filter by

        Returns:
            List of UserNotification instances
        """
        return self.repository.get_user_notifications(
            user_id=user_id,
            skip=skip,
            limit=limit,
            unread_only=unread_only,
            notification_types=notification_types,
        )

    def count_user_notifications(
        self,
        user_id: UUID,
        unread_only: bool = False,
        notification_types: Optional[List[str]] = None
    ) -> int:
        """Count notifications for a user with optional filters.

        Args:
            user_id: User ID to count notifications for
            unread_only: If True, only count unread notifications
            notification_types: Optional list of notification types to filter by

        Returns:
            Count of matching notifications
        """
        return self.repository.count_user_notifications(
            user_id=user_id,
            unread_only=unread_only,
            notification_types=notification_types,
        )

    def get_unread_count(self, user_id: UUID) -> int:
        """Get count of unread notifications for a user.

        Args:
            user_id: User ID to count notifications for

        Returns:
            Count of unread notifications
        """
        return self.repository.get_unread_count(user_id)

    def get_notification(self, notification_id: int, user_id: UUID) -> UserNotification:
        """Get a notification for a user."""
        notification = self.repository.get_notification_for_user(notification_id, user_id)
        if not notification:
            raise EntityNotFoundError("Notification", notification_id)
        return notification

    def mark_notification_read(self, notification_id: int, user_id: UUID) -> UserNotification:
        """Mark a notification as read.

        Args:
            notification_id: Notification ID to mark as read
            user_id: User ID to verify ownership

        Returns:
            Updated UserNotification instance

        Raises:
            EntityNotFoundError: If notification not found or doesn't belong to user
        """
        notification = self.repository.mark_as_read(notification_id, user_id)
        if not notification:
            raise EntityNotFoundError("Notification", notification_id)
        return notification

    def mark_notification_unread(self, notification_id: int, user_id: UUID) -> UserNotification:
        """Mark a notification as unread."""
        notification = self.repository.mark_as_unread(notification_id, user_id)
        if not notification:
            raise EntityNotFoundError("Notification", notification_id)
        return notification

    def mark_all_read(self, user_id: UUID) -> int:
        """Mark all user notifications as read.

        Args:
            user_id: User ID to mark all notifications as read for

        Returns:
            Number of notifications marked as read
        """
        return self.repository.mark_all_as_read(user_id)

    def delete_notification(self, notification_id: int, user_id: UUID) -> bool:
        """Delete a notification.

        Args:
            notification_id: Notification ID to delete
            user_id: User ID to verify ownership

        Returns:
            True if deleted, False if not found

        Raises:
            EntityNotFoundError: If notification not found or doesn't belong to user
        """
        deleted = self.repository.delete_notification(notification_id, user_id)
        if not deleted:
            raise EntityNotFoundError("Notification", notification_id)
        return True

    def create_job_completion_notification(
        self,
        user_id: UUID,
        job_id: int,
        content_id: Optional[int] = None
    ) -> Optional[UserNotification]:
        """Helper to create a job completion notification.

        Args:
            user_id: User ID to create notification for
            job_id: Generation job ID
            content_id: Optional content item ID

        Returns:
            Created UserNotification instance or None if notifications disabled
        """
        return self.create_notification(
            user_id=user_id,
            title="Generation Complete",
            message="Your image generation has completed successfully!",
            notification_type=NotificationType.JOB_COMPLETED,
            related_job_id=job_id,
            related_content_id=content_id
        )

    def create_job_failure_notification(
        self,
        user_id: UUID,
        job_id: int,
        error_message: Optional[str] = None
    ) -> Optional[UserNotification]:
        """Helper to create a job failure notification.

        Args:
            user_id: User ID to create notification for
            job_id: Generation job ID
            error_message: Optional error message

        Returns:
            Created UserNotification instance or None if notifications disabled
        """
        message = "Your image generation failed."
        if error_message:
            message += f" Error: {error_message}"

        return self.create_notification(
            user_id=user_id,
            title="Generation Failed",
            message=message,
            notification_type=NotificationType.JOB_FAILED,
            related_job_id=job_id
        )

    def create_job_cancelled_notification(
        self,
        user_id: UUID,
        job_id: int
    ) -> Optional[UserNotification]:
        """Helper to create a job cancellation notification.

        Args:
            user_id: User ID to create notification for
            job_id: Generation job ID

        Returns:
            Created UserNotification instance or None if notifications disabled
        """
        return self.create_notification(
            user_id=user_id,
            title="Generation Cancelled",
            message="Your image generation was cancelled.",
            notification_type=NotificationType.JOB_CANCELLED,
            related_job_id=job_id
        )
