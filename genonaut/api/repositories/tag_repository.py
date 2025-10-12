"""Tag repository for database operations.

Handles tag queries including polyhierarchical relationships, ratings, and favorites.
"""

from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from sqlalchemy import func, and_, or_, text, case
from sqlalchemy.orm import Session, aliased
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from genonaut.db.schema import Tag, TagParent, TagRating, User
from genonaut.api.repositories.base import BaseRepository
from genonaut.api.models.requests import PaginationRequest
from genonaut.api.models.responses import PaginatedResponse, PaginationMeta
from genonaut.api.exceptions import DatabaseError


class TagRepository(BaseRepository[Tag, Dict[str, Any], Dict[str, Any]]):
    """Repository for Tag entity operations.

    Supports polyhierarchical tag relationships where tags can have multiple parents.
    """

    def __init__(self, db: Session):
        super().__init__(db, Tag)

    def get_by_id(self, tag_id: UUID) -> Optional[Tag]:
        """Get tag by unique identifier."""
        try:
            return self.db.query(Tag).filter(Tag.id == tag_id).first()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get tag by id {tag_id}: {str(e)}")

    def get_by_name(self, name: str) -> Optional[Tag]:
        """Get tag by name.

        Args:
            name: Tag name to search for

        Returns:
            Tag instance or None if not found

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return self.db.query(Tag).filter(Tag.name == name).first()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get tag by name {name}: {str(e)}")

    def get_all(self) -> List[Tag]:
        """Return all tags ordered by name."""
        try:
            return (
                self.db.query(Tag)
                .order_by(Tag.name)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get all tags: {str(e)}")

    def get_by_names(self, names: List[str]) -> List[Tag]:
        """Get multiple tags by their names.

        Args:
            names: List of tag names to search for

        Returns:
            List of matching tags

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return self.db.query(Tag).filter(Tag.name.in_(names)).all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get tags by names: {str(e)}")

    def get_by_ids(self, tag_ids: List[UUID]) -> List[Tag]:
        """Get multiple tags by their IDs.

        Args:
            tag_ids: List of tag UUIDs to search for

        Returns:
            List of matching tags

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return self.db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get tags by IDs: {str(e)}")

    def get_root_tags(self) -> List[Tag]:
        """Get all root tags (tags with no parents).

        Returns:
            List of root tags ordered by name

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return (
                self.db.query(Tag)
                .outerjoin(TagParent, Tag.id == TagParent.tag_id)
                .filter(TagParent.tag_id == None)
                .order_by(Tag.name)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get root tags: {str(e)}")

    def get_children(self, tag_id: UUID) -> List[Tag]:
        """Get direct children of a tag.

        Args:
            tag_id: UUID of the parent tag

        Returns:
            List of child tags ordered by name

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return (
                self.db.query(Tag)
                .join(TagParent, Tag.id == TagParent.tag_id)
                .filter(TagParent.parent_id == tag_id)
                .order_by(Tag.name)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get children for tag {tag_id}: {str(e)}")

    def get_parents(self, tag_id: UUID) -> List[Tag]:
        """Get direct parents of a tag.

        Args:
            tag_id: UUID of the child tag

        Returns:
            List of parent tags ordered by name

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return (
                self.db.query(Tag)
                .join(TagParent, Tag.id == TagParent.parent_id)
                .filter(TagParent.tag_id == tag_id)
                .order_by(Tag.name)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get parents for tag {tag_id}: {str(e)}")

    def get_descendants(self, tag_id: UUID, max_depth: int = 10) -> List[Tuple[Tag, int]]:
        """Get all descendants of a tag recursively.

        Args:
            tag_id: UUID of the parent tag
            max_depth: Maximum recursion depth (prevents infinite loops)

        Returns:
            List of tuples (Tag, depth) ordered by depth and name

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Use recursive CTE for descendants
            cte = text("""
                WITH RECURSIVE descendants AS (
                    -- Base case: direct children
                    SELECT tp.tag_id as descendant_id, 1 as depth
                    FROM tag_parents tp
                    WHERE tp.parent_id = :parent_tag_id

                    UNION

                    -- Recursive case: children of children
                    SELECT tp.tag_id, d.depth + 1
                    FROM tag_parents tp
                    JOIN descendants d ON tp.parent_id = d.descendant_id
                    WHERE d.depth < :max_depth
                )
                SELECT DISTINCT t.id, t.name, t.tag_metadata, t.created_at, t.updated_at, d.depth
                FROM descendants d
                JOIN tags t ON t.id = d.descendant_id
                ORDER BY d.depth, t.name
            """)

            result = self.db.execute(cte, {"parent_tag_id": str(tag_id), "max_depth": max_depth})

            # Convert result to Tag objects with depth
            tags_with_depth = []
            for row in result:
                tag = Tag(
                    id=row.id,
                    name=row.name,
                    tag_metadata=row.tag_metadata,
                    created_at=row.created_at,
                    updated_at=row.updated_at
                )
                tags_with_depth.append((tag, row.depth))

            return tags_with_depth
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get descendants for tag {tag_id}: {str(e)}")

    def get_ancestors(self, tag_id: UUID, max_depth: int = 10) -> List[Tuple[Tag, int]]:
        """Get all ancestors of a tag recursively.

        Args:
            tag_id: UUID of the child tag
            max_depth: Maximum recursion depth (prevents infinite loops)

        Returns:
            List of tuples (Tag, depth) ordered by depth and name

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Use recursive CTE for ancestors
            cte = text("""
                WITH RECURSIVE ancestors AS (
                    -- Base case: direct parents
                    SELECT tp.parent_id as ancestor_id, 1 as depth
                    FROM tag_parents tp
                    WHERE tp.tag_id = :child_tag_id

                    UNION

                    -- Recursive case: parents of parents
                    SELECT tp.parent_id, a.depth + 1
                    FROM tag_parents tp
                    JOIN ancestors a ON tp.tag_id = a.ancestor_id
                    WHERE a.depth < :max_depth
                )
                SELECT DISTINCT t.id, t.name, t.tag_metadata, t.created_at, t.updated_at, a.depth
                FROM ancestors a
                JOIN tags t ON t.id = a.ancestor_id
                ORDER BY a.depth, t.name
            """)

            result = self.db.execute(cte, {"child_tag_id": str(tag_id), "max_depth": max_depth})

            # Convert result to Tag objects with depth
            tags_with_depth = []
            for row in result:
                tag = Tag(
                    id=row.id,
                    name=row.name,
                    tag_metadata=row.tag_metadata,
                    created_at=row.created_at,
                    updated_at=row.updated_at
                )
                tags_with_depth.append((tag, row.depth))

            return tags_with_depth
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get ancestors for tag {tag_id}: {str(e)}")

    def search_tags(self, query: str, pagination: PaginationRequest) -> PaginatedResponse:
        """Search tags by name.

        Args:
            query: Search query string
            pagination: Pagination parameters

        Returns:
            Paginated response with matching tags

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Build query
            db_query = self.db.query(Tag)

            # Apply search filter (case-insensitive LIKE)
            if query:
                db_query = db_query.filter(Tag.name.ilike(f"%{query}%"))

            # Get total count
            total = db_query.count()

            # Apply pagination and ordering
            tags = (
                db_query
                .order_by(Tag.name)
                .offset((pagination.page - 1) * pagination.page_size)
                .limit(pagination.page_size)
                .all()
            )

            # Build pagination metadata
            has_next = (pagination.page * pagination.page_size) < total
            has_previous = pagination.page > 1

            pagination_meta = PaginationMeta(
                page=pagination.page,
                page_size=pagination.page_size,
                total_count=total,
                has_next=has_next,
                has_previous=has_previous
            )

            return PaginatedResponse(items=tags, pagination=pagination_meta)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to search tags: {str(e)}")

    def get_all_paginated(self, pagination: PaginationRequest, sort: str = "name-asc") -> PaginatedResponse:
        """Get all tags with pagination.

        Args:
            pagination: Pagination parameters
            sort: Sort order specifier. Supported values:
                name-asc, name-desc, created-asc, created-desc,
                updated-asc, updated-desc

        Returns:
            Paginated response with tags

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            sort_key = (sort or "name-asc").lower()
            ordering_map = {
                "name-asc": Tag.name.asc(),
                "name-desc": Tag.name.desc(),
                "created-asc": Tag.created_at.asc(),
                "created-desc": Tag.created_at.desc(),
                "updated-asc": Tag.updated_at.asc(),
                "updated-desc": Tag.updated_at.desc(),
                # Backwards compatibility keys
                "name": Tag.name.asc(),
                "created_at": Tag.created_at.desc(),
                "updated_at": Tag.updated_at.desc(),
            }

            order_clause = ordering_map.get(sort_key, Tag.name.asc())

            db_query = self.db.query(Tag)
            total = db_query.count()

            tags = (
                db_query
                .order_by(order_clause)
                .offset((pagination.page - 1) * pagination.page_size)
                .limit(pagination.page_size)
                .all()
            )

            # Build pagination metadata
            has_next = (pagination.page * pagination.page_size) < total
            has_previous = pagination.page > 1

            pagination_meta = PaginationMeta(
                page=pagination.page,
                page_size=pagination.page_size,
                total_count=total,
                has_next=has_next,
                has_previous=has_previous
            )

            return PaginatedResponse(items=tags, pagination=pagination_meta)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get paginated tags: {str(e)}")

    # Rating Methods

    def get_user_rating(self, user_id: UUID, tag_id: UUID) -> Optional[TagRating]:
        """Get user's rating for a tag.

        Args:
            user_id: UUID of the user
            tag_id: UUID of the tag

        Returns:
            TagRating instance or None if not found

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return (
                self.db.query(TagRating)
                .filter(and_(TagRating.user_id == user_id, TagRating.tag_id == tag_id))
                .first()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get user rating: {str(e)}")

    def get_user_ratings(self, user_id: UUID, tag_ids: List[UUID]) -> List[TagRating]:
        """Get user's ratings for multiple tags.

        Args:
            user_id: UUID of the user
            tag_ids: List of tag UUIDs

        Returns:
            List of TagRating instances

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return (
                self.db.query(TagRating)
                .filter(and_(TagRating.user_id == user_id, TagRating.tag_id.in_(tag_ids)))
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get user ratings: {str(e)}")

    def upsert_rating(self, user_id: UUID, tag_id: UUID, rating: float) -> TagRating:
        """Create or update a tag rating.

        Args:
            user_id: UUID of the user
            tag_id: UUID of the tag
            rating: Rating value (1.0-5.0)

        Returns:
            Created or updated TagRating instance

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            existing = self.get_user_rating(user_id, tag_id)

            if existing:
                # Update existing rating
                existing.rating = rating
                self.db.commit()
                self.db.refresh(existing)
                return existing
            else:
                # Create new rating
                new_rating = TagRating(
                    user_id=user_id,
                    tag_id=tag_id,
                    rating=rating
                )
                self.db.add(new_rating)
                self.db.commit()
                self.db.refresh(new_rating)
                return new_rating
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to upsert rating: {str(e)}")

    def delete_rating(self, user_id: UUID, tag_id: UUID) -> bool:
        """Delete a tag rating.

        Args:
            user_id: UUID of the user
            tag_id: UUID of the tag

        Returns:
            True if rating was deleted, False if not found

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            rating = self.get_user_rating(user_id, tag_id)
            if rating:
                self.db.delete(rating)
                self.db.commit()
                return True
            return False
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to delete rating: {str(e)}")

    def get_tag_average_rating(self, tag_id: UUID) -> Tuple[float, int]:
        """Get average rating for a tag.

        Args:
            tag_id: UUID of the tag

        Returns:
            Tuple of (average_rating, rating_count)

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            result = (
                self.db.query(
                    func.coalesce(func.avg(TagRating.rating), 0.0).label('avg_rating'),
                    func.count(TagRating.id).label('rating_count')
                )
                .filter(TagRating.tag_id == tag_id)
                .first()
            )
            return (float(result.avg_rating), int(result.rating_count))
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get tag average rating: {str(e)}")

    def get_tags_with_ratings(self, tag_ids: List[UUID]) -> Dict[UUID, Tuple[float, int]]:
        """Get average ratings for multiple tags.

        Args:
            tag_ids: List of tag UUIDs

        Returns:
            Dictionary mapping tag_id to (average_rating, rating_count)

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            results = (
                self.db.query(
                    TagRating.tag_id,
                    func.avg(TagRating.rating).label('avg_rating'),
                    func.count(TagRating.id).label('rating_count')
                )
                .filter(TagRating.tag_id.in_(tag_ids))
                .group_by(TagRating.tag_id)
                .all()
            )

            return {
                row.tag_id: (float(row.avg_rating), int(row.rating_count))
                for row in results
            }
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get tags with ratings: {str(e)}")

    def get_tags_sorted_by_rating(
        self,
        pagination: PaginationRequest,
        min_ratings: int = 1,
        order: str = "desc"
    ) -> PaginatedResponse:
        """Get tags sorted by average rating.

        Args:
            pagination: Pagination parameters
            min_ratings: Minimum number of ratings required
            order: Sort order, either "asc" or "desc"

        Returns:
            Paginated response with tags sorted by rating

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            rating_stats = (
                self.db.query(
                    TagRating.tag_id.label('tag_id'),
                    func.avg(TagRating.rating).label('avg_rating'),
                    func.count(TagRating.id).label('rating_count')
                )
                .group_by(TagRating.tag_id)
                .subquery()
            )

            rated_or_unrated_filter = func.coalesce(rating_stats.c.rating_count, 0) >= min_ratings

            db_query = (
                self.db.query(
                    Tag,
                    rating_stats.c.avg_rating,
                    func.coalesce(rating_stats.c.rating_count, 0).label('rating_count')
                )
                .outerjoin(rating_stats, Tag.id == rating_stats.c.tag_id)
                .filter(or_(rating_stats.c.rating_count.is_(None), rated_or_unrated_filter))
            )

            total = db_query.count()

            rated_first = case(
                (rating_stats.c.avg_rating.is_(None), 1),
                else_=0
            )

            if order.lower() == "asc":
                order_clause = (
                    rated_first.asc(),
                    rating_stats.c.avg_rating.asc(),
                    Tag.name.asc(),
                )
            else:
                order_clause = (
                    rated_first.asc(),
                    rating_stats.c.avg_rating.desc(),
                    Tag.name.asc(),
                )

            results = (
                db_query
                .order_by(*order_clause)
                .offset((pagination.page - 1) * pagination.page_size)
                .limit(pagination.page_size)
                .all()
            )

            tags = [row[0] for row in results]

            has_next = (pagination.page * pagination.page_size) < total
            has_previous = pagination.page > 1

            pagination_meta = PaginationMeta(
                page=pagination.page,
                page_size=pagination.page_size,
                total_count=total,
                has_next=has_next,
                has_previous=has_previous
            )

            return PaginatedResponse(items=tags, pagination=pagination_meta)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get tags sorted by rating: {str(e)}")

    # Statistics Methods

    def get_hierarchy_statistics(self) -> Dict[str, int]:
        """Get global hierarchy statistics.

        Returns:
            Dictionary with statistics (total_nodes, total_relationships, root_categories)

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            total_nodes = self.db.query(func.count(Tag.id)).scalar()
            total_relationships = self.db.query(func.count(TagParent.tag_id)).scalar()

            # Count root tags
            root_count = (
                self.db.query(func.count(Tag.id))
                .outerjoin(TagParent, Tag.id == TagParent.tag_id)
                .filter(TagParent.tag_id == None)
                .scalar()
            )

            return {
                "totalNodes": int(total_nodes or 0),
                "totalRelationships": int(total_relationships or 0),
                "rootCategories": int(root_count or 0)
            }
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get hierarchy statistics: {str(e)}")
