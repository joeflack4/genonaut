"""Centralized logging configuration for md_manager."""

import logging
import os
import sys
from typing import Optional


def setup_logging(level: Optional[str] = None, format_type: str = "standard") -> None:
    """
    Set up logging configuration for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
               Defaults to INFO, can be overridden with MD_MANAGER_LOG_LEVEL env var
        format_type: Type of log format ("standard", "detailed", "json")
    """
    # Determine log level
    if level is None:
        level = os.getenv('MD_MANAGER_LOG_LEVEL', 'INFO').upper()

    # Validate log level
    numeric_level = getattr(logging, level, None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {level}')

    # Choose format based on type
    formats = {
        "standard": "%(levelname)s: %(message)s",
        "detailed": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "json": '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}'
    }

    log_format = formats.get(format_type, formats["standard"])

    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ],
        force=True  # Override any existing configuration
    )

    # Set specific logger levels for noisy libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def enable_debug_logging() -> None:
    """Enable debug-level logging for troubleshooting."""
    setup_logging(level="DEBUG", format_type="detailed")

    # Also enable debug for our modules specifically
    loggers = [
        "md_manager.github_client",
        "md_manager.github_sync",
        "md_manager.local_sync",
        "md_manager.bidirectional_sync",
        "md_manager.cache",
        "md_manager.sync_state"
    ]

    for logger_name in loggers:
        logging.getLogger(logger_name).setLevel(logging.DEBUG)


def log_function_call(func):
    """Decorator to log function calls at debug level."""
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.debug(f"{func.__name__} failed with error: {e}")
            raise
    return wrapper


class ProgressLogger:
    """Helper class for logging progress of long-running operations."""

    def __init__(self, logger: logging.Logger, operation_name: str, total_items: int):
        self.logger = logger
        self.operation_name = operation_name
        self.total_items = total_items
        self.processed_items = 0
        self.last_logged_percent = -1

    def update(self, increment: int = 1, item_name: Optional[str] = None):
        """Update progress and log if needed."""
        self.processed_items += increment
        percent = int((self.processed_items / self.total_items) * 100) if self.total_items > 0 else 0

        # Log every 10% or at specific milestones
        should_log = (
            percent >= self.last_logged_percent + 10 or
            self.processed_items == self.total_items or
            percent in [1, 5, 25, 50, 75, 90, 95, 99]
        )

        if should_log:
            message = f"{self.operation_name}: {self.processed_items}/{self.total_items} ({percent}%)"
            if item_name:
                message += f" - {item_name}"
            self.logger.info(message)
            self.last_logged_percent = percent

    def complete(self, message: Optional[str] = None):
        """Log completion."""
        final_message = message or f"{self.operation_name} completed: {self.processed_items}/{self.total_items}"
        self.logger.info(final_message)


def log_api_request(logger: logging.Logger, method: str, url: str, status_code: int,
                   response_time: float, rate_limit_remaining: Optional[int] = None):
    """Log GitHub API request details."""
    message = f"API {method} {url} -> {status_code} ({response_time:.2f}s)"
    if rate_limit_remaining is not None:
        message += f" [Rate limit: {rate_limit_remaining} remaining]"

    if status_code >= 400:
        logger.warning(message)
    else:
        logger.debug(message)


def log_file_operation(logger: logging.Logger, operation: str, file_path: str,
                      success: bool = True, error: Optional[str] = None):
    """Log file operation details."""
    if success:
        logger.debug(f"File {operation}: {file_path}")
    else:
        logger.error(f"File {operation} failed: {file_path} - {error}")


def log_sync_statistics(logger: logging.Logger, stats: dict, operation_type: str):
    """Log synchronization statistics."""
    logger.info(f"{operation_type} Statistics:")
    for key, value in stats.items():
        if key.endswith('_time') and isinstance(value, (int, float)):
            logger.info(f"  {key}: {value:.2f}s")
        else:
            logger.info(f"  {key}: {value}")