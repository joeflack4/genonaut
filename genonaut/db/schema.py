"""Database schema definitions for Genonaut recommender system.

This module contains SQLAlchemy models for the PostgreSQL database.
"""

from datetime import datetime
from typing import Optional, Union, Tuple
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float, Boolean,
    ForeignKey, JSON, UniqueConstraint, Index, event, func, literal_column,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship, declarative_base, declared_attr
from sqlalchemy.types import TypeDecorator
from sqlalchemy.engine import Engine
import uuid


class JSONColumn(TypeDecorator):
    """Database-agnostic JSON column that uses JSONB for PostgreSQL and JSON for others."""
    
    impl = JSON
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(JSON())


def create_gin_index_if_postgresql(index_name: str, column_name: str) -> Union[Index, None]:
    """Create a GIN index for PostgreSQL, return None for other databases."""
    try:
        # This will only work if we're using PostgreSQL
        return Index(
            index_name, 
            column_name, 
            postgresql_using='gin', 
            postgresql_ops={column_name: 'jsonb_path_ops'}
        )
    except Exception:
        # For non-PostgreSQL databases, return None
        return None


Base = declarative_base()

FTS_LANGUAGE = "english"


def _fts_language_literal() -> literal_column:
    """Return a literal SQL fragment for the configured full-text search language."""

    return literal_column(f"'{FTS_LANGUAGE}'")


class User(Base):
    """User model for storing user information and preferences.
    
    Attributes:
        id: Primary key
        username: Unique username
        email: User email address
        created_at: Timestamp when user was created
        updated_at: Timestamp when user was last updated
        preferences: JSON field for storing user preferences
        is_active: Whether the user account is active
    """
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    preferences = Column(JSONColumn, default=dict)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    content_items = relationship("ContentItem", back_populates="creator")
    auto_content_items = relationship("ContentItemAuto", back_populates="creator")
    interactions = relationship("UserInteraction", back_populates="user")
    recommendations = relationship("Recommendation", back_populates="user")
    
    # Table arguments - reserved for future indexes
    __table_args__ = ()


class ContentItemColumns:
    """Shared column definitions for content item style tables."""

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    content_type = Column(String(50), nullable=False, index=True)  # text, image, video, audio
    content_data = Column(Text, nullable=False)
    item_metadata = Column(JSONColumn, default=dict)
    creator_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    tags = Column(JSONColumn, default=list)
    quality_score = Column(Float, default=0.0)
    is_private = Column(Boolean, default=False, nullable=False)


class ContentItem(ContentItemColumns, Base):
    """Content item model for storing generated content.
    
    Attributes:
        id: Primary key
        title: Content title
        content_type: Type of content (text, image, video, audio)
        content_data: The actual content or reference to it
        item_metadata: Additional metadata about the content
        creator_id: Foreign key to the user who created/requested the content
        created_at: Timestamp when content was created
        tags: JSON array of tags associated with the content
        quality_score: Quality score assigned to the content
    """
    __tablename__ = 'content_items'
    
    # Relationships
    creator = relationship("User", back_populates="content_items")
    interactions = relationship("UserInteraction", back_populates="content_item")
    recommendations = relationship("Recommendation", back_populates="content_item")
    
    # Full-text search configuration for PostgreSQL
    @declared_attr
    def __table_args__(cls):
        return (
            Index(
                "ci_title_fts_idx",
                func.to_tsvector(
                    _fts_language_literal(),
                    func.coalesce(cls.title, ""),
                ),
                postgresql_using="gin",
                info={"postgres_only": True},
            ),
        )


class ContentItemAuto(ContentItemColumns, Base):
    """Content item model for automatically generated content.

    Starts with the same schema as ``ContentItem`` so we can extend it with
    automation-specific fields in future iterations.
    """

    __tablename__ = 'content_items_auto'

    # Relationships
    creator = relationship("User", back_populates="auto_content_items")

    # Full-text search configuration for PostgreSQL
    @declared_attr
    def __table_args__(cls):
        return (
            Index(
                "cia_title_fts_idx",
                func.to_tsvector(
                    _fts_language_literal(),
                    func.coalesce(cls.title, ""),
                ),
                postgresql_using="gin",
                info={"postgres_only": True},
            ),
        )


class UserInteraction(Base):
    """User interaction model for tracking user engagement with content.
    
    Attributes:
        id: Primary key
        user_id: Foreign key to the user
        content_item_id: Foreign key to the content item
        interaction_type: Type of interaction (view, like, share, download, etc.)
        rating: Optional rating given by the user (1-5 scale)
        duration: Duration of interaction in seconds (for view interactions)
        created_at: Timestamp when interaction occurred
        interaction_metadata: Additional interaction metadata
    """
    __tablename__ = 'user_interactions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    content_item_id = Column(Integer, ForeignKey('content_items.id'), nullable=False, index=True)
    interaction_type = Column(String(50), nullable=False, index=True)  # view, like, share, download, etc.
    rating = Column(Integer, nullable=True)  # 1-5 scale
    duration = Column(Integer, nullable=True)  # seconds
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    interaction_metadata = Column(JSONColumn, default=dict)
    
    # Relationships
    user = relationship("User", back_populates="interactions")
    content_item = relationship("ContentItem", back_populates="interactions")
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('user_id', 'content_item_id', 'interaction_type', 'created_at', 
                        name='unique_user_content_interaction'),
    )


class Recommendation(Base):
    """Recommendation model for storing AI-generated recommendations.
    
    Attributes:
        id: Primary key
        user_id: Foreign key to the user receiving the recommendation
        content_item_id: Foreign key to the recommended content item
        recommendation_score: Confidence score of the recommendation (0-1)
        algorithm_version: Version of the recommendation algorithm used
        created_at: Timestamp when recommendation was generated
        is_served: Whether the recommendation was actually served to the user
        rec_metadata: Additional recommendation metadata
    """
    __tablename__ = 'recommendations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    content_item_id = Column(Integer, ForeignKey('content_items.id'), nullable=False, index=True)
    recommendation_score = Column(Float, nullable=False)  # 0-1 confidence score
    algorithm_version = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_served = Column(Boolean, default=False, nullable=False)
    served_at = Column(DateTime, nullable=True)
    rec_metadata = Column(JSONColumn, default=dict)
    
    # Relationships
    user = relationship("User", back_populates="recommendations")
    content_item = relationship("ContentItem", back_populates="recommendations")
    
    # Constraints and indexes
    __table_args__ = ()


class GenerationJob(Base):
    """Generation job model for tracking content generation requests.
    
    Attributes:
        id: Primary key
        user_id: Foreign key to the user who requested the generation
        job_type: Type of generation job (text, image, video, audio)
        prompt: The prompt used for generation
        parameters: Generation parameters (model, temperature, etc.)
        status: Job status (pending, running, completed, failed, cancelled)
        result_content_id: Foreign key to the generated content item
        created_at: Timestamp when job was created
        started_at: Timestamp when job processing started
        completed_at: Timestamp when job was completed
        error_message: Error message if job failed
    """
    __tablename__ = 'generation_jobs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    job_type = Column(String(50), nullable=False, index=True)  # text, image, video, audio
    prompt = Column(Text, nullable=False)
    parameters = Column(JSONColumn, default=dict)
    status = Column(String(20), default='pending', nullable=False, index=True)  # pending, running, completed, failed, cancelled
    result_content_id = Column(Integer, ForeignKey('content_items.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    result_content = relationship("ContentItem", foreign_keys=[result_content_id])
    
    # Full-text search configuration for PostgreSQL
    __table_args__ = (
        Index(
            "gj_prompt_fts_idx",
            func.to_tsvector(
                _fts_language_literal(),
                func.coalesce(prompt, ""),
            ),
            postgresql_using="gin",
            info={"postgres_only": True},
        ),
    )


def _strip_non_postgres_indexes(metadata, connection, **_) -> None:
    """Temporarily remove PostgreSQL-only indexes when using other dialects."""

    if connection.dialect.name == "postgresql":
        return

    for table in metadata.tables.values():
        pending = table.info.setdefault("_postgres_only_indexes", set())
        for index in list(table.indexes):
            if index.info.get("postgres_only"):
                table.indexes.remove(index)
                pending.add(index)


def _restore_non_postgres_indexes(metadata, _connection, **_) -> None:
    """Restore PostgreSQL-only indexes after temporary removal."""

    for table in metadata.tables.values():
        pending = table.info.pop("_postgres_only_indexes", None)
        if pending:
            table.indexes.update(pending)


event.listen(Base.metadata, "before_create", _strip_non_postgres_indexes)
event.listen(Base.metadata, "after_create", _restore_non_postgres_indexes)
event.listen(Base.metadata, "before_drop", _strip_non_postgres_indexes)
event.listen(Base.metadata, "after_drop", _restore_non_postgres_indexes)
