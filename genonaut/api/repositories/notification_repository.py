"""Notification repository for database operations."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc

from genonaut.db.schema import UserNotification
from genonaut.api.repositories.base import BaseRepository
from genonaut.api.exceptions import DatabaseError


class NotificationRepository(BaseRepository[UserNotification, Dict[str, Any], Dict[str, Any]]):
    """Repository for UserNotification entity operations."""

    def __init__(self, db: Session):
        super().__init__(db, UserNotification)

    def get_user_notifications(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 10,
        unread_only: bool = False
    ) -> List[UserNotification]:
        """Get paginated notifications for a user.

        Args:
            user_id: User ID to get notifications for
            skip: Number of records to skip
            limit: Maximum number of records to return
            unread_only: If True, only return unread notifications

        Returns:
            List of UserNotification instances

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            query = self.db.query(UserNotification).filter(
                UserNotification.user_id == user_id
            )

            if unread_only:
                query = query.filter(UserNotification.read_status == False)

            return query.order_by(desc(UserNotification.created_at)).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get user notifications for {user_id}: {str(e)}")

    def get_unread_count(self, user_id: UUID) -> int:
        """Get count of unread notifications for a user.

        Args:
            user_id: User ID to count notifications for

        Returns:
            Count of unread notifications

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return self.db.query(UserNotification).filter(
                UserNotification.user_id == user_id,
                UserNotification.read_status == False
            ).count()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get unread count for {user_id}: {str(e)}")

    def mark_as_read(self, notification_id: int, user_id: UUID) -> Optional[UserNotification]:
        """Mark a notification as read.

        Args:
            notification_id: Notification ID to mark as read
            user_id: User ID to verify ownership

        Returns:
            Updated UserNotification instance or None if not found

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            notification = self.db.query(UserNotification).filter(
                UserNotification.id == notification_id,
                UserNotification.user_id == user_id
            ).first()

            if notification and not notification.read_status:
                notification.read_status = True
                notification.read_at = datetime.utcnow()
                self.db.commit()
                self.db.refresh(notification)

            return notification
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to mark notification {notification_id} as read: {str(e)}")

    def mark_all_as_read(self, user_id: UUID) -> int:
        """Mark all user notifications as read.

        Args:
            user_id: User ID to mark all notifications as read for

        Returns:
            Number of notifications marked as read

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            count = self.db.query(UserNotification).filter(
                UserNotification.user_id == user_id,
                UserNotification.read_status == False
            ).update({
                'read_status': True,
                'read_at': datetime.utcnow()
            })
            self.db.commit()
            return count
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to mark all notifications as read for {user_id}: {str(e)}")

    def delete_notification(self, notification_id: int, user_id: UUID) -> bool:
        """Delete a notification.

        Args:
            notification_id: Notification ID to delete
            user_id: User ID to verify ownership

        Returns:
            True if deleted, False if not found

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            notification = self.db.query(UserNotification).filter(
                UserNotification.id == notification_id,
                UserNotification.user_id == user_id
            ).first()

            if notification:
                self.db.delete(notification)
                self.db.commit()
                return True

            return False
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to delete notification {notification_id}: {str(e)}")

    def get_by_type(
        self,
        user_id: UUID,
        notification_type: str,
        skip: int = 0,
        limit: int = 10
    ) -> List[UserNotification]:
        """Get notifications by type for a user.

        Args:
            user_id: User ID to get notifications for
            notification_type: Type of notification to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of UserNotification instances

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return self.db.query(UserNotification).filter(
                UserNotification.user_id == user_id,
                UserNotification.notification_type == notification_type
            ).order_by(desc(UserNotification.created_at)).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get notifications by type for {user_id}: {str(e)}")
