"""Retry logic service with exponential backoff for ComfyUI operations."""

import asyncio
import logging
import random
import time
from typing import Any, Callable, Dict, List, Optional, Type, Union
from functools import wraps
from enum import Enum

logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """Retry strategies available."""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_INTERVAL = "fixed_interval"


class RetryableError(Exception):
    """Base class for errors that should trigger retries."""
    pass


class NonRetryableError(Exception):
    """Base class for errors that should NOT trigger retries."""
    pass


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
        retryable_exceptions: Optional[List[Type[Exception]]] = None,
        non_retryable_exceptions: Optional[List[Type[Exception]]] = None
    ):
        """Initialize retry configuration.

        Args:
            max_attempts: Maximum number of retry attempts
            base_delay: Base delay in seconds
            max_delay: Maximum delay between retries
            exponential_base: Base for exponential backoff
            jitter: Whether to add random jitter to delays
            strategy: Retry strategy to use
            retryable_exceptions: List of exceptions that should trigger retries
            non_retryable_exceptions: List of exceptions that should NOT trigger retries
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.strategy = strategy
        self.retryable_exceptions = retryable_exceptions or []
        self.non_retryable_exceptions = non_retryable_exceptions or []


class RetryService:
    """Service for handling retries with various strategies."""

    # Default retryable exceptions for ComfyUI operations
    DEFAULT_RETRYABLE_EXCEPTIONS = [
        ConnectionError,
        TimeoutError,
        OSError,  # Network-related OS errors
    ]

    # Default non-retryable exceptions
    DEFAULT_NON_RETRYABLE_EXCEPTIONS = [
        ValueError,  # Invalid parameters
        TypeError,   # Type errors
        KeyError,    # Missing keys
    ]

    def __init__(self):
        """Initialize retry service."""
        self.retry_stats = {}

    def create_config(
        self,
        operation_type: str,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0
    ) -> RetryConfig:
        """Create retry configuration for specific operation types.

        Args:
            operation_type: Type of operation (e.g., "comfyui_connection", "file_upload")
            max_attempts: Maximum retry attempts
            base_delay: Base delay in seconds
            max_delay: Maximum delay

        Returns:
            RetryConfig instance
        """
        # Customize based on operation type
        if operation_type == "comfyui_connection":
            return RetryConfig(
                max_attempts=3,
                base_delay=2.0,
                max_delay=30.0,
                retryable_exceptions=self.DEFAULT_RETRYABLE_EXCEPTIONS + [
                    # Add ComfyUI-specific retryable exceptions - avoid circular import by using string matching
                ],
                non_retryable_exceptions=self.DEFAULT_NON_RETRYABLE_EXCEPTIONS
            )
        elif operation_type == "file_operations":
            return RetryConfig(
                max_attempts=2,
                base_delay=0.5,
                max_delay=10.0,
                retryable_exceptions=[OSError, IOError],
                non_retryable_exceptions=[ValueError, TypeError, PermissionError]
            )
        elif operation_type == "database_operations":
            return RetryConfig(
                max_attempts=2,
                base_delay=1.0,
                max_delay=5.0,
                strategy=RetryStrategy.LINEAR_BACKOFF,
                retryable_exceptions=[ConnectionError],
                non_retryable_exceptions=self.DEFAULT_NON_RETRYABLE_EXCEPTIONS
            )
        else:
            return RetryConfig(
                max_attempts=max_attempts,
                base_delay=base_delay,
                max_delay=max_delay
            )

    def should_retry(self, exception: Exception, config: RetryConfig) -> bool:
        """Determine if an exception should trigger a retry.

        Args:
            exception: The exception that occurred
            config: Retry configuration

        Returns:
            True if should retry, False otherwise
        """
        # Check non-retryable exceptions first
        for non_retryable in config.non_retryable_exceptions:
            if isinstance(exception, non_retryable):
                logger.debug(f"Not retrying due to non-retryable exception: {type(exception).__name__}")
                return False

        # Check retryable exceptions
        if config.retryable_exceptions:
            for retryable in config.retryable_exceptions:
                if isinstance(exception, retryable):
                    logger.debug(f"Will retry due to retryable exception: {type(exception).__name__}")
                    return True

            # Check for ComfyUI-specific retryable exceptions by class name
            # (avoids circular import issues)
            exception_class_name = type(exception).__name__
            if exception_class_name in ['ComfyUIConnectionError', 'ComfyUIWorkflowError']:
                logger.debug(f"Will retry due to ComfyUI-specific retryable exception: {exception_class_name}")
                return True

            return False  # Not in retryable list

        # Default: retry on common transient errors
        for default_retryable in self.DEFAULT_RETRYABLE_EXCEPTIONS:
            if isinstance(exception, default_retryable):
                return True

        return False

    def calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """Calculate delay for the next retry attempt.

        Args:
            attempt: Current attempt number (0-based)
            config: Retry configuration

        Returns:
            Delay in seconds
        """
        if config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = config.base_delay * (config.exponential_base ** attempt)
        elif config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = config.base_delay * (attempt + 1)
        else:  # FIXED_INTERVAL
            delay = config.base_delay

        # Apply maximum delay limit
        delay = min(delay, config.max_delay)

        # Add jitter to prevent thundering herd
        if config.jitter:
            jitter_range = delay * 0.1  # 10% jitter
            delay += random.uniform(-jitter_range, jitter_range)

        return max(0, delay)

    def retry_sync(
        self,
        func: Callable,
        config: RetryConfig,
        operation_name: str = "unknown",
        *args,
        **kwargs
    ) -> Any:
        """Execute a function with retry logic (synchronous).

        Args:
            func: Function to execute
            config: Retry configuration
            operation_name: Name of operation for logging
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Last exception if all retries failed
        """
        last_exception = None
        start_time = time.time()

        for attempt in range(config.max_attempts):
            try:
                result = func(*args, **kwargs)

                # Log successful retry
                if attempt > 0:
                    duration = time.time() - start_time
                    logger.info(f"Operation '{operation_name}' succeeded on attempt {attempt + 1} after {duration:.2f}s")
                    self._record_retry_success(operation_name, attempt + 1, duration)

                return result

            except Exception as e:
                last_exception = e

                # Check if we should retry
                if not self.should_retry(e, config):
                    logger.debug(f"Not retrying operation '{operation_name}' due to non-retryable error: {type(e).__name__}")
                    break

                # Check if we have more attempts
                if attempt >= config.max_attempts - 1:
                    logger.warning(f"Operation '{operation_name}' failed after {config.max_attempts} attempts")
                    break

                # Calculate delay and wait
                delay = self.calculate_delay(attempt, config)
                logger.warning(f"Operation '{operation_name}' failed on attempt {attempt + 1}, retrying in {delay:.2f}s: {str(e)}")

                if delay > 0:
                    time.sleep(delay)

        # Record final failure
        total_duration = time.time() - start_time
        self._record_retry_failure(operation_name, config.max_attempts, total_duration, last_exception)

        # Raise the last exception
        raise last_exception

    async def retry_async(
        self,
        func: Callable,
        config: RetryConfig,
        operation_name: str = "unknown",
        *args,
        **kwargs
    ) -> Any:
        """Execute a function with retry logic (asynchronous).

        Args:
            func: Async function to execute
            config: Retry configuration
            operation_name: Name of operation for logging
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Last exception if all retries failed
        """
        last_exception = None
        start_time = time.time()

        for attempt in range(config.max_attempts):
            try:
                result = await func(*args, **kwargs)

                # Log successful retry
                if attempt > 0:
                    duration = time.time() - start_time
                    logger.info(f"Async operation '{operation_name}' succeeded on attempt {attempt + 1} after {duration:.2f}s")
                    self._record_retry_success(operation_name, attempt + 1, duration)

                return result

            except Exception as e:
                last_exception = e

                # Check if we should retry
                if not self.should_retry(e, config):
                    logger.debug(f"Not retrying async operation '{operation_name}' due to non-retryable error: {type(e).__name__}")
                    break

                # Check if we have more attempts
                if attempt >= config.max_attempts - 1:
                    logger.warning(f"Async operation '{operation_name}' failed after {config.max_attempts} attempts")
                    break

                # Calculate delay and wait
                delay = self.calculate_delay(attempt, config)
                logger.warning(f"Async operation '{operation_name}' failed on attempt {attempt + 1}, retrying in {delay:.2f}s: {str(e)}")

                if delay > 0:
                    await asyncio.sleep(delay)

        # Record final failure
        total_duration = time.time() - start_time
        self._record_retry_failure(operation_name, config.max_attempts, total_duration, last_exception)

        # Raise the last exception
        raise last_exception

    def _record_retry_success(self, operation_name: str, attempts: int, duration: float) -> None:
        """Record successful retry for statistics.

        Args:
            operation_name: Name of operation
            attempts: Number of attempts taken
            duration: Total duration
        """
        if operation_name not in self.retry_stats:
            self.retry_stats[operation_name] = {
                "successes": 0,
                "failures": 0,
                "total_attempts": 0,
                "total_duration": 0.0,
                "avg_attempts": 0.0
            }

        stats = self.retry_stats[operation_name]
        stats["successes"] += 1
        stats["total_attempts"] += attempts
        stats["total_duration"] += duration
        stats["avg_attempts"] = stats["total_attempts"] / (stats["successes"] + stats["failures"])

    def _record_retry_failure(
        self,
        operation_name: str,
        attempts: int,
        duration: float,
        last_exception: Optional[Exception]
    ) -> None:
        """Record failed retry for statistics.

        Args:
            operation_name: Name of operation
            attempts: Number of attempts taken
            duration: Total duration
            last_exception: Final exception
        """
        if operation_name not in self.retry_stats:
            self.retry_stats[operation_name] = {
                "successes": 0,
                "failures": 0,
                "total_attempts": 0,
                "total_duration": 0.0,
                "avg_attempts": 0.0
            }

        stats = self.retry_stats[operation_name]
        stats["failures"] += 1
        stats["total_attempts"] += attempts
        stats["total_duration"] += duration
        stats["avg_attempts"] = stats["total_attempts"] / (stats["successes"] + stats["failures"])

        logger.error(f"Final failure for operation '{operation_name}' after {attempts} attempts in {duration:.2f}s: {str(last_exception)}")

    def get_retry_statistics(self) -> Dict[str, Any]:
        """Get retry statistics for monitoring.

        Returns:
            Dictionary with retry statistics
        """
        return dict(self.retry_stats)

    def clear_statistics(self) -> None:
        """Clear retry statistics."""
        self.retry_stats.clear()


# Global retry service instance
_retry_service = RetryService()


def get_retry_service() -> RetryService:
    """Get the global retry service instance."""
    return _retry_service


def with_retry(
    operation_type: str = "default",
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0
):
    """Decorator to add retry logic to functions.

    Args:
        operation_type: Type of operation for custom configuration
        max_attempts: Maximum retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay

    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retry_service = get_retry_service()
            config = retry_service.create_config(
                operation_type, max_attempts, base_delay, max_delay
            )
            return retry_service.retry_sync(
                func, config, func.__name__, *args, **kwargs
            )
        return wrapper
    return decorator


def with_async_retry(
    operation_type: str = "default",
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0
):
    """Decorator to add retry logic to async functions.

    Args:
        operation_type: Type of operation for custom configuration
        max_attempts: Maximum retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay

    Returns:
        Decorated async function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retry_service = get_retry_service()
            config = retry_service.create_config(
                operation_type, max_attempts, base_delay, max_delay
            )
            return await retry_service.retry_async(
                func, config, func.__name__, *args, **kwargs
            )
        return wrapper
    return decorator