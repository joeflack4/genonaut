"""Notification API routes."""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from genonaut.api.services.notification_service import NotificationService
from genonaut.api.models.requests import NotificationCreateRequest, NotificationListRequest
from genonaut.api.models.responses import (
    NotificationResponse,
    NotificationListResponse,
    UnreadCountResponse,
    SuccessResponse,
)
from genonaut.api.dependencies import get_database_session
from genonaut.api.exceptions import EntityNotFoundError, ValidationError

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


@router.get("/", response_model=NotificationListResponse)
def list_user_notifications(
    user_id: UUID,
    skip: int = 0,
    limit: int = 10,
    unread_only: bool = False,
    db: Session = Depends(get_database_session)
):
    """List notifications for a user.

    Args:
        user_id: User ID to get notifications for
        skip: Number of records to skip
        limit: Maximum number of records to return
        unread_only: Only return unread notifications
        db: Database session

    Returns:
        NotificationListResponse with paginated notifications
    """
    service = NotificationService(db)
    notifications = service.get_user_notifications(user_id, skip, limit, unread_only)

    # Get total count
    total = len(service.get_user_notifications(user_id, 0, 10000, unread_only))

    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in notifications],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{notification_id}", response_model=NotificationResponse)
def get_notification(
    notification_id: int,
    user_id: UUID,
    db: Session = Depends(get_database_session)
):
    """Get a single notification by ID.

    Args:
        notification_id: Notification ID
        user_id: User ID to verify ownership
        db: Database session

    Returns:
        NotificationResponse

    Raises:
        HTTPException: If notification not found
    """
    service = NotificationService(db)
    notifications = service.get_user_notifications(user_id, 0, 1000)
    notification = next((n for n in notifications if n.id == notification_id), None)

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification {notification_id} not found"
        )

    return NotificationResponse.model_validate(notification)


@router.get("/unread/count", response_model=UnreadCountResponse)
def get_unread_count(
    user_id: UUID,
    db: Session = Depends(get_database_session)
):
    """Get count of unread notifications for a user.

    Args:
        user_id: User ID to count notifications for
        db: Database session

    Returns:
        UnreadCountResponse with count
    """
    service = NotificationService(db)
    count = service.get_unread_count(user_id)

    return UnreadCountResponse(unread_count=count)


@router.put("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: int,
    user_id: UUID,
    db: Session = Depends(get_database_session)
):
    """Mark a notification as read.

    Args:
        notification_id: Notification ID
        user_id: User ID to verify ownership
        db: Database session

    Returns:
        Updated NotificationResponse

    Raises:
        HTTPException: If notification not found
    """
    service = NotificationService(db)

    try:
        notification = service.mark_notification_read(notification_id, user_id)
        return NotificationResponse.model_validate(notification)
    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/read-all", response_model=SuccessResponse)
def mark_all_read(
    user_id: UUID,
    db: Session = Depends(get_database_session)
):
    """Mark all user notifications as read.

    Args:
        user_id: User ID to mark all notifications as read for
        db: Database session

    Returns:
        SuccessResponse with count of notifications marked
    """
    service = NotificationService(db)
    count = service.mark_all_read(user_id)

    return SuccessResponse(
        success=True,
        message=f"Marked {count} notifications as read"
    )


@router.delete("/{notification_id}", response_model=SuccessResponse)
def delete_notification(
    notification_id: int,
    user_id: UUID,
    db: Session = Depends(get_database_session)
):
    """Delete a notification.

    Args:
        notification_id: Notification ID
        user_id: User ID to verify ownership
        db: Database session

    Returns:
        SuccessResponse

    Raises:
        HTTPException: If notification not found
    """
    service = NotificationService(db)

    try:
        service.delete_notification(notification_id, user_id)
        return SuccessResponse(
            success=True,
            message=f"Notification {notification_id} deleted successfully"
        )
    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
def create_notification(
    request: NotificationCreateRequest,
    db: Session = Depends(get_database_session)
):
    """Create a new notification (admin/system use).

    Args:
        request: Notification creation request
        db: Database session

    Returns:
        Created NotificationResponse

    Raises:
        HTTPException: If user not found or validation fails
    """
    service = NotificationService(db)

    try:
        notification = service.create_notification(
            user_id=request.user_id,
            title=request.title,
            message=request.message,
            notification_type=request.notification_type,
            related_job_id=request.related_job_id,
            related_content_id=request.related_content_id
        )

        if notification is None:
            # User has notifications disabled
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has notifications disabled"
            )

        return NotificationResponse.model_validate(notification)
    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
