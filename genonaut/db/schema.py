"""Database schema definitions for Genonaut recommender system.

This module contains SQLAlchemy models for the PostgreSQL database.
"""

from datetime import datetime
from typing import Optional, Union, Tuple
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float, Boolean,
    ForeignKey, JSON, UniqueConstraint, Index, event, func, literal_column, DDL,
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
    
    # Pagination optimization indexes
    __table_args__ = (
        Index("idx_users_created_at_desc", created_at.desc()),
        Index("idx_users_active_created", is_active, created_at.desc()),
        Index("idx_users_username_lower", func.lower(username)),  # For case-insensitive username searches
        Index("idx_users_email_lower", func.lower(email)),      # For case-insensitive email searches
    )


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
    
    # Full-text search configuration and pagination optimization indexes for PostgreSQL
    @declared_attr
    def __table_args__(cls):
        return (
            # Full-text search index
            Index(
                "ci_title_fts_idx",
                func.to_tsvector(
                    _fts_language_literal(),
                    func.coalesce(cls.title, ""),
                ),
                postgresql_using="gin",
                info={"postgres_only": True},
            ),
            # GiST trigram index for title similarity searches (CRITICAL for content similarity)
            Index(
                "idx_content_items_title_gist",
                cls.title,
                postgresql_using="gist",
                postgresql_ops={"title": "gist_trgm_ops"},
                info={"postgres_only": True},
            ),
            # Pagination optimization indexes
            Index("idx_content_items_created_at_desc", cls.created_at.desc()),
            Index("idx_content_items_creator_created", cls.creator_id, cls.created_at.desc()),
            Index("idx_content_items_quality_created", cls.quality_score.desc(), cls.created_at.desc()),
            Index("idx_content_items_type_created", cls.content_type, cls.created_at.desc()),
            Index("idx_content_items_public_created", cls.created_at.desc(), postgresql_where=cls.is_private == False),
            # GIN index for tags array operations (PostgreSQL only)
            Index("idx_content_items_tags_gin", cls.tags, postgresql_using="gin", info={"postgres_only": True}),
            # GIN index for metadata operations (PostgreSQL only)
            Index("idx_content_items_metadata_gin", cls.item_metadata, postgresql_using="gin", info={"postgres_only": True}),
        )


class ContentItemAuto(ContentItemColumns, Base):
    """Content item model for automatically generated content.

    Starts with the same schema as ``ContentItem`` so we can extend it with
    automation-specific fields in future iterations.
    """

    __tablename__ = 'content_items_auto'

    # Relationships
    creator = relationship("User", back_populates="auto_content_items")

    # Full-text search configuration and pagination optimization indexes for PostgreSQL
    @declared_attr
    def __table_args__(cls):
        return (
            # Full-text search index
            Index(
                "cia_title_fts_idx",
                func.to_tsvector(
                    _fts_language_literal(),
                    func.coalesce(cls.title, ""),
                ),
                postgresql_using="gin",
                info={"postgres_only": True},
            ),
            # GiST trigram index for title similarity searches (CRITICAL for content similarity)
            Index(
                "idx_content_items_auto_title_gist",
                cls.title,
                postgresql_using="gist",
                postgresql_ops={"title": "gist_trgm_ops"},
                info={"postgres_only": True},
            ),
            # Pagination optimization indexes
            Index("idx_content_items_auto_created_at_desc", cls.created_at.desc()),
            Index("idx_content_items_auto_creator_created", cls.creator_id, cls.created_at.desc()),
            Index("idx_content_items_auto_quality_created", cls.quality_score.desc(), cls.created_at.desc()),
            Index("idx_content_items_auto_type_created", cls.content_type, cls.created_at.desc()),
            Index("idx_content_items_auto_public_created", cls.created_at.desc(), postgresql_where=cls.is_private == False),
            # GIN index for tags array operations (PostgreSQL only)
            Index("idx_content_items_auto_tags_gin", cls.tags, postgresql_using="gin", info={"postgres_only": True}),
            # GIN index for metadata operations (PostgreSQL only)
            Index("idx_content_items_auto_metadata_gin", cls.item_metadata, postgresql_using="gin", info={"postgres_only": True}),
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
    
    # Constraints and pagination optimization indexes
    __table_args__ = (
        UniqueConstraint('user_id', 'content_item_id', 'interaction_type', 'created_at',
                        name='unique_user_content_interaction'),
        # Pagination optimization indexes
        Index("idx_user_interactions_created_at_desc", created_at.desc()),
        Index("idx_user_interactions_user_created", user_id, created_at.desc()),
        Index("idx_user_interactions_content_created", content_item_id, created_at.desc()),
        Index("idx_user_interactions_type_created", interaction_type, created_at.desc()),
        Index("idx_user_interactions_user_type_created", user_id, interaction_type, created_at.desc()),
        # Index for rating-based queries
        Index("idx_user_interactions_rating_created", rating.desc(), created_at.desc(), postgresql_where=rating.is_not(None)),
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
    
    # Pagination optimization indexes
    __table_args__ = (
        Index("idx_recommendations_created_at_desc", created_at.desc()),
        Index("idx_recommendations_user_created", user_id, created_at.desc()),
        Index("idx_recommendations_content_created", content_item_id, created_at.desc()),
        Index("idx_recommendations_score_created", recommendation_score.desc(), created_at.desc()),
        Index("idx_recommendations_user_score_created", user_id, recommendation_score.desc(), created_at.desc()),
        # Index for served recommendations
        Index("idx_recommendations_served_created", is_served, created_at.desc()),
        Index("idx_recommendations_user_served_created", user_id, is_served, created_at.desc()),
        # Index for algorithm version analysis
        Index("idx_recommendations_algorithm_created", algorithm_version, created_at.desc()),
    )


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
    
    # Full-text search configuration and pagination optimization indexes for PostgreSQL
    __table_args__ = (
        # Full-text search index
        Index(
            "gj_prompt_fts_idx",
            func.to_tsvector(
                _fts_language_literal(),
                func.coalesce(prompt, ""),
            ),
            postgresql_using="gin",
            info={"postgres_only": True},
        ),
        # GiST trigram index for prompt similarity searches (HIGHEST PRIORITY - billions of rows)
        Index(
            "idx_generation_jobs_prompt_gist",
            prompt,
            postgresql_using="gist",
            postgresql_ops={"prompt": "gist_trgm_ops"},
            info={"postgres_only": True},
        ),
        # Pagination optimization indexes
        Index("idx_generation_jobs_created_at_desc", created_at.desc()),
        Index("idx_generation_jobs_user_created", user_id, created_at.desc()),
        Index("idx_generation_jobs_status_created", status, created_at.desc()),
        Index("idx_generation_jobs_type_created", job_type, created_at.desc()),
        Index("idx_generation_jobs_user_status_created", user_id, status, created_at.desc()),
        Index("idx_generation_jobs_user_type_created", user_id, job_type, created_at.desc()),
        # Index for job queue management
        Index("idx_generation_jobs_status_created_priority", status, created_at.asc(), postgresql_where=status.in_(['pending', 'running'])),
        # Index for completed job analytics
        Index("idx_generation_jobs_completed_at_desc", completed_at.desc(), postgresql_where=completed_at.is_not(None)),
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


def ensure_pg_trgm_extension(engine) -> None:
    """Ensure pg_trgm extension is installed (PostgreSQL only).

    This function can be called during database initialization to ensure
    the trigram extension is available before creating indexes.
    Safe to call multiple times (idempotent).
    """
    if engine.dialect.name == "postgresql":
        from sqlalchemy import text
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))


def ensure_trigram_indexes(engine) -> None:
    """Ensure all trigram indexes are created (PostgreSQL only).

    This function creates all GiST trigram indexes defined in the models.
    Safe to call multiple times (idempotent).
    """
    if engine.dialect.name == "postgresql":
        # Get all tables that have trigram indexes
        for table in Base.metadata.tables.values():
            for index in table.indexes:
                # Check if this is a GiST trigram index
                if (hasattr(index, 'kwargs') and
                    index.kwargs.get('postgresql_using') == 'gist' and
                    index.kwargs.get('postgresql_ops') and
                    any('gist_trgm_ops' in str(op) for op in index.kwargs.get('postgresql_ops', {}).values())):
                    try:
                        index.create(bind=engine, checkfirst=True)
                    except Exception as e:
                        # Log but don't fail - the index might already exist or be created by other means
                        print(f"Note: Could not create trigram index {index.name}: {e}")


class AvailableModel(Base):
    """Available AI models for ComfyUI generation.

    Attributes:
        id: Primary key
        name: Display name of the model
        type: Type of model (checkpoint, lora)
        file_path: Path to the model file
        description: Optional description of the model
        is_active: Whether the model is available for use
        created_at: Timestamp when model was added
        updated_at: Timestamp when model was last updated
    """
    __tablename__ = 'available_models'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    type = Column(String(20), nullable=False, index=True)  # checkpoint, lora
    file_path = Column(String(512), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Optimization indexes
    __table_args__ = (
        Index("idx_available_models_type_active", type, is_active),
        Index("idx_available_models_active_name", is_active, name),
        UniqueConstraint('name', 'type', name='uq_model_name_type'),
    )


class ComfyUIGenerationRequest(Base):
    """ComfyUI-specific generation requests.

    Attributes:
        id: Primary key
        user_id: Foreign key to the user who requested the generation
        prompt: Positive prompt for generation
        negative_prompt: Negative prompt for generation (optional)
        checkpoint_model: Name of the checkpoint model to use
        lora_models: JSON array of LoRA models with their strengths
        width: Image width
        height: Image height
        batch_size: Number of images to generate
        sampler_params: JSON object with KSampler parameters
        status: Generation status
        comfyui_prompt_id: ComfyUI workflow prompt ID
        output_paths: JSON array of generated image file paths
        thumbnail_paths: JSON array of thumbnail file paths
        created_at: Timestamp when request was created
        updated_at: Timestamp when request was last updated
        started_at: Timestamp when generation started
        completed_at: Timestamp when generation completed
        error_message: Error message if generation failed
    """
    __tablename__ = 'comfyui_generation_requests'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    prompt = Column(Text, nullable=False)
    negative_prompt = Column(Text, nullable=True)
    checkpoint_model = Column(String(255), nullable=False)
    lora_models = Column(JSONColumn, default=list)  # [{"name": str, "strength_model": float, "strength_clip": float}]
    width = Column(Integer, nullable=False, default=512)
    height = Column(Integer, nullable=False, default=512)
    batch_size = Column(Integer, nullable=False, default=1)
    sampler_params = Column(JSONColumn, default=dict)  # {seed, steps, cfg, sampler_name, scheduler, denoise}
    status = Column(String(20), default='pending', nullable=False, index=True)  # pending, processing, completed, failed, cancelled
    comfyui_prompt_id = Column(String(255), nullable=True, unique=True, index=True)
    output_paths = Column(JSONColumn, default=list)  # Array of generated image file paths
    thumbnail_paths = Column(JSONColumn, default=list)  # Array of thumbnail file paths
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])

    # Full-text search and optimization indexes
    __table_args__ = (
        # Full-text search index for prompts
        Index(
            "cgr_prompt_fts_idx",
            func.to_tsvector(
                _fts_language_literal(),
                func.coalesce(prompt, "") + ' ' + func.coalesce(negative_prompt, ""),
            ),
            postgresql_using="gin",
            info={"postgres_only": True},
        ),
        # GiST trigram index for prompt similarity searches (CRITICAL - billions of rows expected)
        Index(
            "idx_comfyui_gen_prompt_gist",
            prompt,
            postgresql_using="gist",
            postgresql_ops={"prompt": "gist_trgm_ops"},
            info={"postgres_only": True},
        ),
        # GiST trigram index for negative prompt similarity searches
        Index(
            "idx_comfyui_gen_negative_prompt_gist",
            negative_prompt,
            postgresql_using="gist",
            postgresql_ops={"negative_prompt": "gist_trgm_ops"},
            info={"postgres_only": True},
        ),
        # Pagination optimization indexes
        Index("idx_comfyui_gen_created_at_desc", created_at.desc()),
        Index("idx_comfyui_gen_user_created", user_id, created_at.desc()),
        Index("idx_comfyui_gen_status_created", status, created_at.desc()),
        Index("idx_comfyui_gen_user_status_created", user_id, status, created_at.desc()),
        # Index for queue management
        Index("idx_comfyui_gen_status_created_priority", status, created_at.asc(),
              postgresql_where=status.in_(['pending', 'processing'])),
        # Index for completed generation analytics
        Index("idx_comfyui_gen_completed_at_desc", completed_at.desc(),
              postgresql_where=completed_at.is_not(None)),
    )


class FlaggedContent(Base):
    """Flagged content model for tracking content with problematic words.

    Tracks content items that contain words from a configurable danger word list,
    with risk metrics and admin review capabilities.

    Attributes:
        id: Primary key
        content_item_id: Foreign key to content_items (nullable, either this or content_item_auto_id)
        content_item_auto_id: Foreign key to content_items_auto (nullable, either this or content_item_id)
        content_source: Source type ('regular' or 'auto')
        flagged_text: The actual text that was flagged (prompt/content)
        flagged_words: JSON array of problem words found in the content
        total_problem_words: Count of problem word occurrences (with duplicates)
        total_words: Total word count in the flagged text
        problem_percentage: Percentage of words that are problematic (0-100)
        risk_score: Calculated risk score (0-100) based on various metrics
        creator_id: Foreign key to user who created the content (denormalized for filtering)
        flagged_at: Timestamp when content was flagged
        reviewed: Whether an admin has reviewed this flagged item
        reviewed_at: Timestamp when review occurred
        reviewed_by: Foreign key to user who reviewed (admin)
        notes: Admin notes about the flagged content
    """
    __tablename__ = 'flagged_content'

    id = Column(Integer, primary_key=True, autoincrement=True)
    content_item_id = Column(Integer, ForeignKey('content_items.id', ondelete='CASCADE'), nullable=True, index=True)
    content_item_auto_id = Column(Integer, ForeignKey('content_items_auto.id', ondelete='CASCADE'), nullable=True, index=True)
    content_source = Column(String(20), nullable=False, index=True)  # 'regular' or 'auto'
    flagged_text = Column(Text, nullable=False)
    flagged_words = Column(JSONColumn, default=list, nullable=False)  # Array of problem words found
    total_problem_words = Column(Integer, nullable=False, default=0)
    total_words = Column(Integer, nullable=False, default=0)
    problem_percentage = Column(Float, nullable=False, default=0.0)
    risk_score = Column(Float, nullable=False, default=0.0)
    creator_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    flagged_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    reviewed = Column(Boolean, default=False, nullable=False, index=True)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    content_item = relationship("ContentItem", foreign_keys=[content_item_id])
    content_item_auto = relationship("ContentItemAuto", foreign_keys=[content_item_auto_id])
    creator = relationship("User", foreign_keys=[creator_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    # Indexes for efficient querying and pagination
    __table_args__ = (
        # Pagination optimization indexes
        Index("idx_flagged_content_risk_score_desc", risk_score.desc()),
        Index("idx_flagged_content_flagged_at_desc", flagged_at.desc()),
        Index("idx_flagged_content_creator_flagged", creator_id, flagged_at.desc()),
        Index("idx_flagged_content_source_flagged", content_source, flagged_at.desc()),
        Index("idx_flagged_content_reviewed_flagged", reviewed, flagged_at.desc()),
        Index("idx_flagged_content_risk_flagged", risk_score.desc(), flagged_at.desc()),
        # Index for unreviewed high-risk items
        Index("idx_flagged_content_unreviewed_high_risk", risk_score.desc(),
              postgresql_where=(reviewed == False)),
        # GIN index for flagged words array operations
        Index("idx_flagged_content_words_gin", flagged_words, postgresql_using="gin", info={"postgres_only": True}),
    )


# Event listeners for PostgreSQL-specific functionality
event.listen(Base.metadata, "before_create", _strip_non_postgres_indexes)
event.listen(Base.metadata, "after_create", _restore_non_postgres_indexes)
event.listen(Base.metadata, "before_drop", _strip_non_postgres_indexes)
event.listen(Base.metadata, "after_drop", _restore_non_postgres_indexes)

# Ensure pg_trgm extension is installed before creating any tables/indexes (PostgreSQL only)
# This is required for GiST trigram indexes to work
event.listen(
    Base.metadata,
    "before_create",
    DDL("CREATE EXTENSION IF NOT EXISTS pg_trgm").execute_if(dialect="postgresql")
)
