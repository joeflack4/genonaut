"""User management API routes."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from genonaut.api.dependencies import get_database_session
from genonaut.api.services.user_service import UserService
from genonaut.api.services.interaction_service import InteractionService
from genonaut.api.models.requests import (
    UserCreateRequest, 
    UserUpdateRequest, 
    UserPreferencesUpdateRequest,
    UserSearchRequest
)
from genonaut.api.models.responses import (
    UserResponse,
    UserListResponse,
    UserStatsResponse,
    UserActivityStatsResponse,
    InteractionListResponse,
    InteractionResponse,
    SuccessResponse,
)
from genonaut.api.exceptions import EntityNotFoundError, ValidationError, DatabaseError
from genonaut.db.schema import UserInteraction, ContentItem

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreateRequest,
    db: Session = Depends(get_database_session)
):
    """Create a new user."""
    service = UserService(db)
    try:
        user = service.create_user(
            username=user_data.username,
            email=user_data.email,
            preferences=user_data.preferences
        )
        return UserResponse.model_validate(user)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/search", response_model=UserListResponse)
async def search_users(
    active_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_database_session)
):
    """Search users with simple query parameters."""
    service = UserService(db)
    try:
        users = service.get_users(skip=skip, limit=limit, active_only=active_only)
        total = service.repository.count({'is_active': True} if active_only else None)
    except DatabaseError as exc:
        if "UndefinedTable" in str(exc):
            users = []
            total = 0
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

    return UserListResponse(
        items=[UserResponse.model_validate(user) for user in users],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post("/search", response_model=UserListResponse)
async def search_users_post(
    search_request: UserSearchRequest,
    db: Session = Depends(get_database_session)
):
    """Search users via POST payload."""

    service = UserService(db)
    try:
        if search_request.preferences_filter:
            users = service.search_users_by_preferences(search_request.preferences_filter)
            total = len(users)
        else:
            users = service.get_users(
                skip=search_request.skip,
                limit=search_request.limit,
                active_only=search_request.active_only,
            )
            total = service.repository.count(
                {'is_active': True} if search_request.active_only else None
            )
    except DatabaseError as exc:
        if "UndefinedTable" in str(exc):
            users = []
            total = 0
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

    return UserListResponse(
        items=[UserResponse.model_validate(user) for user in users],
        total=total,
        skip=search_request.skip,
        limit=search_request.limit,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_database_session)
):
    """Get user by ID."""
    service = UserService(db)
    try:
        user = service.get_user(user_id)
        return UserResponse.model_validate(user)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdateRequest,
    db: Session = Depends(get_database_session)
):
    """Update user information."""
    service = UserService(db)
    try:
        user = service.update_user(
            user_id=user_id,
            username=user_data.username,
            email=user_data.email,
            is_active=user_data.is_active
        )
        return UserResponse.model_validate(user)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.delete("/{user_id}", response_model=SuccessResponse)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_database_session)
):
    """Delete a user."""
    service = UserService(db)
    try:
        service.delete_user(user_id)
        return SuccessResponse(message=f"User {user_id} deleted successfully")
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{user_id}/preferences", response_model=UserResponse)
async def update_user_preferences(
    user_id: int,
    preferences_data: UserPreferencesUpdateRequest,
    db: Session = Depends(get_database_session)
):
    """Update user preferences."""
    service = UserService(db)
    try:
        user = service.update_user_preferences(user_id, preferences_data.preferences)
        return UserResponse.model_validate(user)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{user_id}/interactions", response_model=InteractionListResponse)
async def get_user_interactions(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_database_session)
):
    """List interactions for a specific user."""
    interaction_service = InteractionService(db)
    interactions = interaction_service.get_user_interactions(user_id, skip=skip, limit=limit)
    total = interaction_service.repository.count({'user_id': user_id})

    return InteractionListResponse(
        items=[InteractionResponse.model_validate(interaction) for interaction in interactions],
        total=total,
        skip=skip,
        limit=limit,
    )



@router.post("/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: int,
    db: Session = Depends(get_database_session)
):
    """Deactivate a user account."""
    service = UserService(db)
    try:
        user = service.deactivate_user(user_id)
        return UserResponse.model_validate(user)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: int,
    db: Session = Depends(get_database_session)
):
    """Activate a user account."""
    service = UserService(db)
    try:
        user = service.activate_user(user_id)
        return UserResponse.model_validate(user)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{user_id}/stats", response_model=UserActivityStatsResponse)
async def get_user_statistics(
    user_id: int,
    db: Session = Depends(get_database_session)
):
    """Get activity statistics for a specific user."""
    service = UserService(db)
    try:
        service.get_user(user_id)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    stats = service.get_user_statistics(user_id)
    return UserActivityStatsResponse(
        total_interactions=stats["total_interactions"],
        content_created=stats["content_created"],
        avg_rating_given=stats["avg_rating_given"],
    )


@router.get("/", response_model=UserListResponse)
async def get_users(
    search_params: UserSearchRequest = Depends(),
    db: Session = Depends(get_database_session)
):
    """Get list of users with optional filtering."""
    service = UserService(db)
    
    try:
        if search_params.preferences_filter:
            users = service.search_users_by_preferences(search_params.preferences_filter)
            total = len(users)
        else:
            users = service.get_users(
                skip=search_params.skip,
                limit=search_params.limit,
                active_only=search_params.active_only,
            )
            total = service.repository.count(
                {'is_active': True} if search_params.active_only else None
            )
    except DatabaseError as exc:
        if "UndefinedTable" in str(exc):
            users = []
            total = 0
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
    
    return UserListResponse(
        items=[UserResponse.model_validate(user) for user in users],
        total=total,
        skip=search_params.skip,
        limit=search_params.limit
    )


@router.get("/username/{username}", response_model=UserResponse)
async def get_user_by_username(
    username: str,
    db: Session = Depends(get_database_session)
):
    """Get user by username."""
    service = UserService(db)
    user = service.get_user_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"User with username '{username}' not found"
        )
    return UserResponse.model_validate(user)


@router.get("/email/{email}", response_model=UserResponse)
async def get_user_by_email(
    email: str,
    db: Session = Depends(get_database_session)
):
    """Get user by email."""
    service = UserService(db)
    user = service.get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"User with email '{email}' not found"
        )
    return UserResponse.model_validate(user)


@router.get("/stats/overview", response_model=UserStatsResponse)
async def get_user_stats(
    db: Session = Depends(get_database_session)
):
    """Get user statistics."""
    service = UserService(db)
    stats = service.get_user_stats()
    return UserStatsResponse(**stats)
