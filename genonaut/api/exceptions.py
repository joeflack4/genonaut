"""Custom exceptions for the Genonaut API."""

from typing import Any, Dict, Optional

from fastapi import HTTPException, status


class GenonAutAPIException(HTTPException):
    """Base exception for Genonaut API."""
    pass


class EntityNotFoundError(GenonAutAPIException):
    """Raised when a requested entity is not found."""
    
    def __init__(self, entity_type: str, entity_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity_type} with id {entity_id} not found"
        )


class ValidationError(GenonAutAPIException):
    """Raised when request validation fails."""
    
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=message
        )


class DatabaseError(GenonAutAPIException):
    """Raised when database operations fail."""
    
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {message}"
        )


class AuthenticationError(GenonAutAPIException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message
        )


class AuthorizationError(GenonAutAPIException):
    """Raised when authorization fails."""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message
        )


class StatementTimeoutError(Exception):
    """Raised when a database statement exceeds the configured timeout."""

    def __init__(
        self,
        message: str,
        *,
        timeout: str,
        query: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[BaseException] = None,
    ) -> None:
        super().__init__(message)
        self.timeout = timeout
        self.query = query
        self.context = context or {}
        self.original_error = original_error
