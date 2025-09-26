"""Error handling and user-friendly message service."""

import logging
import time
from typing import Dict, Any, Optional, List, Union
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Categories of errors for better handling."""
    CONNECTION = "connection"
    VALIDATION = "validation"
    PERMISSION = "permission"
    RESOURCE = "resource"
    SYSTEM = "system"
    GENERATION = "generation"


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorService:
    """Service for handling errors and generating user-friendly messages."""

    # Mapping of technical errors to user-friendly messages
    ERROR_MAPPINGS = {
        # ComfyUI Connection Errors
        "ComfyUIConnectionError": {
            "message": "Image generation service is temporarily unavailable. Please try again in a few minutes.",
            "category": ErrorCategory.CONNECTION,
            "severity": ErrorSeverity.MEDIUM,
            "retry": True,
            "retry_delay": 60
        },
        "ConnectionError": {
            "message": "Unable to connect to image generation service. Please check your connection and try again.",
            "category": ErrorCategory.CONNECTION,
            "severity": ErrorSeverity.MEDIUM,
            "retry": True,
            "retry_delay": 30
        },
        "Timeout": {
            "message": "Request timed out. The service may be busy. Please try again later.",
            "category": ErrorCategory.CONNECTION,
            "severity": ErrorSeverity.MEDIUM,
            "retry": True,
            "retry_delay": 120
        },
        "TimeoutError": {
            "message": "Request timed out. The service may be busy. Please try again later.",
            "category": ErrorCategory.CONNECTION,
            "severity": ErrorSeverity.MEDIUM,
            "retry": True,
            "retry_delay": 120
        },

        # ComfyUI Workflow Errors
        "ComfyUIWorkflowError": {
            "message": "Invalid generation parameters. Please check your settings and try again.",
            "category": ErrorCategory.VALIDATION,
            "severity": ErrorSeverity.LOW,
            "retry": False
        },
        "WorkflowValidationError": {
            "message": "Generation settings are not valid. Please adjust your parameters.",
            "category": ErrorCategory.VALIDATION,
            "severity": ErrorSeverity.LOW,
            "retry": False
        },

        # Model Errors
        "ModelNotFoundError": {
            "message": "Selected model is currently unavailable. Please choose a different model.",
            "category": ErrorCategory.RESOURCE,
            "severity": ErrorSeverity.LOW,
            "retry": False
        },
        "InvalidModelError": {
            "message": "Selected model is not compatible. Please choose a different model.",
            "category": ErrorCategory.RESOURCE,
            "severity": ErrorSeverity.LOW,
            "retry": False
        },

        # Validation Errors
        "ValidationError": {
            "message": "Invalid input provided. Please check your entries and try again.",
            "category": ErrorCategory.VALIDATION,
            "severity": ErrorSeverity.LOW,
            "retry": False
        },
        "ValueError": {
            "message": "Invalid input provided. Please check your entries and try again.",
            "category": ErrorCategory.VALIDATION,
            "severity": ErrorSeverity.LOW,
            "retry": False
        },
        "ParameterValidationError": {
            "message": "Generation parameters are out of valid range. Please adjust and try again.",
            "category": ErrorCategory.VALIDATION,
            "severity": ErrorSeverity.LOW,
            "retry": False
        },

        # Database Errors
        "DatabaseError": {
            "message": "A temporary database issue occurred. Please try again shortly.",
            "category": ErrorCategory.SYSTEM,
            "severity": ErrorSeverity.HIGH,
            "retry": True,
            "retry_delay": 30
        },
        "EntityNotFoundError": {
            "message": "Requested item was not found. It may have been removed or is no longer available.",
            "category": ErrorCategory.RESOURCE,
            "severity": ErrorSeverity.LOW,
            "retry": False
        },

        # Permission Errors
        "PermissionError": {
            "message": "You don't have permission to perform this action.",
            "category": ErrorCategory.PERMISSION,
            "severity": ErrorSeverity.LOW,
            "retry": False
        },
        "AuthenticationError": {
            "message": "Please log in to continue.",
            "category": ErrorCategory.PERMISSION,
            "severity": ErrorSeverity.LOW,
            "retry": False
        },

        # File Storage Errors
        "FileStorageError": {
            "message": "Unable to save generated images. Please try again.",
            "category": ErrorCategory.SYSTEM,
            "severity": ErrorSeverity.MEDIUM,
            "retry": True,
            "retry_delay": 60
        },
        "FileNotFoundError": {
            "message": "Requested file or resource was not found.",
            "category": ErrorCategory.RESOURCE,
            "severity": ErrorSeverity.LOW,
            "retry": False
        },
        "MemoryError": {
            "message": "System is out of memory. Please try again later.",
            "category": ErrorCategory.SYSTEM,
            "severity": ErrorSeverity.HIGH,
            "retry": True,
            "retry_delay": 120
        },
        "DiskSpaceError": {
            "message": "Insufficient storage space. Please try again later or contact support.",
            "category": ErrorCategory.SYSTEM,
            "severity": ErrorSeverity.HIGH,
            "retry": True,
            "retry_delay": 300
        },

        # Rate Limiting
        "RateLimitError": {
            "message": "Too many requests. Please wait a moment before trying again.",
            "category": ErrorCategory.RESOURCE,
            "severity": ErrorSeverity.LOW,
            "retry": True,
            "retry_delay": 60
        },
        "QuotaExceededError": {
            "message": "You have reached your generation limit. Please try again later or upgrade your account.",
            "category": ErrorCategory.RESOURCE,
            "severity": ErrorSeverity.LOW,
            "retry": True,
            "retry_delay": 3600
        }
    }

    def __init__(self):
        """Initialize error service."""
        self.error_counts = {}
        self.last_error_times = {}

    def handle_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle an error and return user-friendly information.

        Args:
            error: The exception that occurred
            context: Additional context about the error
            user_id: Optional user ID for tracking

        Returns:
            Dictionary with user-friendly error information
        """
        error_type = type(error).__name__
        error_message = str(error)
        timestamp = time.time()

        # Log the technical error
        self._log_technical_error(error, context, user_id)

        # Track error frequency
        self._track_error(error_type, user_id)

        # Get user-friendly error info
        error_info = self._get_error_info(error_type, error_message, context)

        # Add error tracking information
        error_info.update({
            "timestamp": timestamp,
            "error_id": self._generate_error_id(error_type, timestamp),
            "context": context or {}
        })

        return error_info

    def _get_error_info(
        self,
        error_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get user-friendly error information.

        Args:
            error_type: Type of error
            error_message: Original error message
            context: Additional context

        Returns:
            User-friendly error information
        """
        # Check for specific error patterns in message
        error_key = self._match_error_pattern(error_type, error_message)

        error_config = self.ERROR_MAPPINGS.get(error_key, {
            "message": "An unexpected error occurred. Please try again later.",
            "category": ErrorCategory.SYSTEM,
            "severity": ErrorSeverity.MEDIUM,
            "retry": True,
            "retry_delay": 60
        })

        return {
            "user_message": error_config["message"],
            "category": error_config["category"].value,
            "severity": error_config["severity"].value,
            "can_retry": error_config.get("retry", False),
            "retry_delay": error_config.get("retry_delay", 60),
            "technical_type": error_type
        }

    def _match_error_pattern(self, error_type: str, error_message: str) -> str:
        """Match error patterns to determine the most specific error type.

        Args:
            error_type: Exception type name
            error_message: Error message content

        Returns:
            Best matching error key
        """
        # Direct type match
        if error_type in self.ERROR_MAPPINGS:
            return error_type

        # Pattern matching in error messages
        error_message_lower = error_message.lower()

        if "connection" in error_message_lower or "connect" in error_message_lower:
            return "ConnectionError"
        elif "timeout" in error_message_lower:
            return "Timeout"
        elif "model" in error_message_lower and "not found" in error_message_lower:
            return "ModelNotFoundError"
        elif "validation" in error_message_lower or "invalid" in error_message_lower:
            return "ValidationError"
        elif "permission" in error_message_lower or "forbidden" in error_message_lower:
            return "PermissionError"
        elif "database" in error_message_lower or "db" in error_message_lower:
            return "DatabaseError"
        elif "disk" in error_message_lower and "space" in error_message_lower:
            return "DiskSpaceError"
        elif "rate limit" in error_message_lower or "too many" in error_message_lower:
            return "RateLimitError"

        # Return the original type as fallback
        return error_type

    def _log_technical_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]],
        user_id: Optional[str]
    ) -> None:
        """Log technical error details for debugging.

        Args:
            error: The exception
            context: Additional context
            user_id: Optional user ID
        """
        log_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "user_id": user_id,
            "context": context or {}
        }

        # Log with appropriate level based on error type
        error_type = type(error).__name__
        error_config = self.ERROR_MAPPINGS.get(error_type, {})
        severity = error_config.get("severity", ErrorSeverity.MEDIUM)

        if severity == ErrorSeverity.CRITICAL:
            logger.critical(f"Critical error occurred: {log_data}")
        elif severity == ErrorSeverity.HIGH:
            logger.error(f"High severity error: {log_data}")
        elif severity == ErrorSeverity.MEDIUM:
            logger.warning(f"Medium severity error: {log_data}")
        else:
            logger.info(f"Low severity error: {log_data}")

    def _track_error(self, error_type: str, user_id: Optional[str]) -> None:
        """Track error frequency for monitoring.

        Args:
            error_type: Type of error
            user_id: Optional user ID
        """
        now = time.time()
        key = f"{error_type}:{user_id}" if user_id else error_type

        # Track error count
        self.error_counts[key] = self.error_counts.get(key, 0) + 1
        self.last_error_times[key] = now

        # Log frequent errors
        if self.error_counts[key] > 5:
            logger.warning(f"Frequent error detected: {error_type} occurred {self.error_counts[key]} times for user {user_id}")

    def _generate_error_id(self, error_type: str, timestamp: float) -> str:
        """Generate a unique error ID for tracking.

        Args:
            error_type: Type of error
            timestamp: Error timestamp

        Returns:
            Unique error identifier
        """
        return f"{error_type}_{int(timestamp)}_{hash(str(timestamp)) % 10000:04d}"

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring.

        Returns:
            Dictionary with error statistics
        """
        now = time.time()
        recent_errors = {}
        total_errors = 0

        # Count recent errors (last hour)
        for key, last_time in self.last_error_times.items():
            if now - last_time <= 3600:  # 1 hour
                error_type = key.split(':')[0]
                recent_errors[error_type] = recent_errors.get(error_type, 0) + 1
                total_errors += self.error_counts[key]

        return {
            "recent_errors": recent_errors,
            "total_recent_count": total_errors,
            "unique_error_types": len(recent_errors),
            "most_common": max(recent_errors.items(), key=lambda x: x[1]) if recent_errors else None
        }

    def should_alert(self, error_type: str, threshold: int = 10) -> bool:
        """Check if error frequency warrants an alert.

        Args:
            error_type: Type of error to check
            threshold: Alert threshold

        Returns:
            True if alert should be sent
        """
        return self.error_counts.get(error_type, 0) >= threshold


# Global error service instance
_error_service = ErrorService()


def get_error_service() -> ErrorService:
    """Get the global error service instance."""
    return _error_service


def handle_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Convenience function to handle errors.

    Args:
        error: The exception that occurred
        context: Additional context about the error
        user_id: Optional user ID for tracking

    Returns:
        Dictionary with user-friendly error information
    """
    return _error_service.handle_error(error, context, user_id)