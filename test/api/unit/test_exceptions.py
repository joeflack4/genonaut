"""Unit tests for API exceptions."""

import pytest
from fastapi import status

from genonaut.api.exceptions import (
    GenonAutAPIException,
    EntityNotFoundError,
    ValidationError,
    DatabaseError,
    AuthenticationError,
    AuthorizationError
)


class TestGenonAutAPIException:
    """Test base API exception class."""
    
    def test_base_exception_inheritance(self):
        """Test that base exception inherits from HTTPException."""
        from fastapi import HTTPException
        assert issubclass(GenonAutAPIException, HTTPException)


class TestEntityNotFoundError:
    """Test EntityNotFoundError exception."""
    
    def test_entity_not_found_error_creation(self):
        """Test creating EntityNotFoundError with entity type and ID."""
        error = EntityNotFoundError("User", 123)
        assert error.status_code == status.HTTP_404_NOT_FOUND
        assert error.detail == "User with id 123 not found"
    
    def test_entity_not_found_error_inheritance(self):
        """Test that EntityNotFoundError inherits from GenonAutAPIException."""
        error = EntityNotFoundError("Content", 456)
        assert isinstance(error, GenonAutAPIException)
    
    def test_entity_not_found_error_different_types(self):
        """Test EntityNotFoundError with different entity types."""
        test_cases = [
            ("User", 1, "User with id 1 not found"),
            ("ContentItem", 999, "ContentItem with id 999 not found"),
            ("Recommendation", 42, "Recommendation with id 42 not found"),
            ("GenerationJob", 7, "GenerationJob with id 7 not found")
        ]
        
        for entity_type, entity_id, expected_detail in test_cases:
            error = EntityNotFoundError(entity_type, entity_id)
            assert error.detail == expected_detail
            assert error.status_code == status.HTTP_404_NOT_FOUND


class TestValidationError:
    """Test ValidationError exception."""
    
    def test_validation_error_creation(self):
        """Test creating ValidationError with custom message."""
        message = "Invalid input: username must be at least 3 characters"
        error = ValidationError(message)
        assert error.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert error.detail == message
    
    def test_validation_error_inheritance(self):
        """Test that ValidationError inherits from GenonAutAPIException."""
        error = ValidationError("Test validation error")
        assert isinstance(error, GenonAutAPIException)
    
    def test_validation_error_empty_message(self):
        """Test ValidationError with empty message."""
        error = ValidationError("")
        assert error.detail == ""
        assert error.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestDatabaseError:
    """Test DatabaseError exception."""
    
    def test_database_error_creation(self):
        """Test creating DatabaseError with custom message."""
        message = "Connection timeout"
        error = DatabaseError(message)
        assert error.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert error.detail == f"Database error: {message}"
    
    def test_database_error_inheritance(self):
        """Test that DatabaseError inherits from GenonAutAPIException."""
        error = DatabaseError("Test database error")
        assert isinstance(error, GenonAutAPIException)
    
    def test_database_error_message_formatting(self):
        """Test that DatabaseError prefixes message with 'Database error:'."""
        original_message = "Table does not exist"
        error = DatabaseError(original_message)
        assert error.detail == f"Database error: {original_message}"


class TestAuthenticationError:
    """Test AuthenticationError exception."""
    
    def test_authentication_error_default_message(self):
        """Test creating AuthenticationError with default message."""
        error = AuthenticationError()
        assert error.status_code == status.HTTP_401_UNAUTHORIZED
        assert error.detail == "Authentication failed"
    
    def test_authentication_error_custom_message(self):
        """Test creating AuthenticationError with custom message."""
        message = "Invalid API key"
        error = AuthenticationError(message)
        assert error.status_code == status.HTTP_401_UNAUTHORIZED
        assert error.detail == message
    
    def test_authentication_error_inheritance(self):
        """Test that AuthenticationError inherits from GenonAutAPIException."""
        error = AuthenticationError()
        assert isinstance(error, GenonAutAPIException)


class TestAuthorizationError:
    """Test AuthorizationError exception."""
    
    def test_authorization_error_default_message(self):
        """Test creating AuthorizationError with default message."""
        error = AuthorizationError()
        assert error.status_code == status.HTTP_403_FORBIDDEN
        assert error.detail == "Access denied"
    
    def test_authorization_error_custom_message(self):
        """Test creating AuthorizationError with custom message."""
        message = "Insufficient permissions to access this resource"
        error = AuthorizationError(message)
        assert error.status_code == status.HTTP_403_FORBIDDEN
        assert error.detail == message
    
    def test_authorization_error_inheritance(self):
        """Test that AuthorizationError inherits from GenonAutAPIException."""
        error = AuthorizationError()
        assert isinstance(error, GenonAutAPIException)


class TestExceptionStatusCodes:
    """Test that all exceptions have correct HTTP status codes."""
    
    def test_all_exception_status_codes(self):
        """Test that each exception type has the correct status code."""
        test_cases = [
            (EntityNotFoundError("Test", 1), status.HTTP_404_NOT_FOUND),
            (ValidationError("Test"), status.HTTP_422_UNPROCESSABLE_ENTITY),
            (DatabaseError("Test"), status.HTTP_500_INTERNAL_SERVER_ERROR),
            (AuthenticationError("Test"), status.HTTP_401_UNAUTHORIZED),
            (AuthorizationError("Test"), status.HTTP_403_FORBIDDEN)
        ]
        
        for exception, expected_status in test_cases:
            assert exception.status_code == expected_status, f"Wrong status code for {type(exception).__name__}"