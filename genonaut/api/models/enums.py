"""Enums and constants for the Genonaut API."""

from enum import Enum


class ContentType(str, Enum):
    """Content type enumeration."""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"


class InteractionType(str, Enum):
    """Interaction type enumeration."""
    VIEW = "view"
    LIKE = "like"
    SHARE = "share"
    DOWNLOAD = "download"
    BOOKMARK = "bookmark"
    COMMENT = "comment"
    RATE = "rate"


class JobStatus(str, Enum):
    """Generation job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobType(str, Enum):
    """Generation job type enumeration."""
    TEXT = "text_generation"
    IMAGE = "image_generation"
    VIDEO = "video_generation"
    AUDIO = "audio_generation"


class DatabaseEnvironment(str, Enum):
    """Database environment enumeration."""
    DEV = "dev"
    DEMO = "demo"
