"""Unit tests for TagService."""

import pytest
from uuid import uuid4
from unittest.mock import Mock, MagicMock, patch

from genonaut.api.services.tag_service import TagService
from genonaut.api.exceptions import EntityNotFoundError, ValidationError
from genonaut.db.schema import Tag, TagRating, User


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return Mock()


@pytest.fixture
def mock_repository():
    """Create mock tag repository."""
    return Mock()


@pytest.fixture
def mock_user_repository():
    """Create mock user repository."""
    return Mock()


@pytest.fixture
def service(mock_db, mock_repository, mock_user_repository):
    """Create TagService with mocked dependencies."""
    service = TagService(mock_db)
    service.repository = mock_repository
    service.user_repository = mock_user_repository
    return service


@pytest.fixture
def sample_tag():
    """Create sample tag."""
    return Tag(
        id=uuid4(),
        name="Test Tag",
        tag_metadata={}
    )


@pytest.fixture
def sample_user():
    """Create sample user."""
    return User(
        id=uuid4(),
        username="testuser",
        email="test@example.com",
        favorite_tag_ids=[]
    )


class TestTagServiceCRUD:
    """Test basic CRUD operations."""

    def test_get_tag_by_id_success(self, service, mock_repository, sample_tag):
        """Test successful tag retrieval by ID."""
        mock_repository.get_by_id.return_value = sample_tag

        result = service.get_tag_by_id(sample_tag.id)

        assert result == sample_tag
        mock_repository.get_by_id.assert_called_once_with(sample_tag.id)

    def test_get_tag_by_id_not_found(self, service, mock_repository):
        """Test tag not found raises exception."""
        tag_id = uuid4()
        mock_repository.get_by_id.return_value = None

        with pytest.raises(EntityNotFoundError):
            service.get_tag_by_id(tag_id)

    def test_get_tag_by_name_success(self, service, mock_repository, sample_tag):
        """Test successful tag retrieval by name."""
        mock_repository.get_by_name.return_value = sample_tag

        result = service.get_tag_by_name("Test Tag")

        assert result == sample_tag
        mock_repository.get_by_name.assert_called_once_with("Test Tag")

    def test_get_tag_by_name_not_found(self, service, mock_repository):
        """Test tag not found by name raises exception."""
        mock_repository.get_by_name.return_value = None

        with pytest.raises(EntityNotFoundError):
            service.get_tag_by_name("NonExistent")


class TestTagServiceHierarchy:
    """Test hierarchy operations."""

    def test_get_children(self, service, mock_repository, sample_tag):
        """Test getting children."""
        child1 = Tag(id=uuid4(), name="Child 1", tag_metadata={})
        child2 = Tag(id=uuid4(), name="Child 2", tag_metadata={})

        mock_repository.get_by_id.return_value = sample_tag
        mock_repository.get_children.return_value = [child1, child2]

        result = service.get_children(sample_tag.id)

        assert len(result) == 2
        mock_repository.get_children.assert_called_once_with(sample_tag.id)

    def test_get_children_tag_not_found(self, service, mock_repository):
        """Test getting children of non-existent tag."""
        tag_id = uuid4()
        mock_repository.get_by_id.return_value = None

        with pytest.raises(EntityNotFoundError):
            service.get_children(tag_id)

    def test_get_full_hierarchy(self, service, mock_repository, mock_db, sample_tag):
        """Test getting full hierarchy."""
        mock_repository.get_all.return_value = [sample_tag]
        mock_db.query.return_value.all.return_value = []
        mock_repository.get_hierarchy_statistics.return_value = {
            "totalNodes": 1,
            "totalRelationships": 0,
            "rootCategories": 1
        }

        result = service.get_full_hierarchy(include_ratings=False)

        assert "nodes" in result
        assert "metadata" in result
        assert len(result["nodes"]) == 1
        assert result["metadata"]["totalNodes"] == 1


class TestTagServiceRatings:
    """Test rating operations."""

    def test_rate_tag_success(self, service, mock_repository, mock_user_repository, sample_tag, sample_user):
        """Test successful tag rating."""
        rating_obj = TagRating(
            id=1,
            user_id=sample_user.id,
            tag_id=sample_tag.id,
            rating=4.5
        )

        mock_user_repository.get_by_id.return_value = sample_user
        mock_repository.get_by_id.return_value = sample_tag
        mock_repository.upsert_rating.return_value = rating_obj

        result = service.rate_tag(sample_user.id, sample_tag.id, 4.5)

        assert result.rating == 4.5
        mock_repository.upsert_rating.assert_called_once_with(
            sample_user.id, sample_tag.id, 4.5
        )

    def test_get_user_ratings_map(self, service, mock_repository, mock_user_repository, sample_tag, sample_user):
        """get_user_ratings_map returns a mapping of tag IDs to ratings."""
        rating_obj = TagRating(
            id=1,
            user_id=sample_user.id,
            tag_id=sample_tag.id,
            rating=3.5
        )

        mock_user_repository.get_by_id.return_value = sample_user
        mock_repository.get_user_ratings.return_value = [rating_obj]

        result = service.get_user_ratings_map(sample_user.id, [sample_tag.id])

        assert result == {sample_tag.id: 3.5}
        mock_repository.get_user_ratings.assert_called_once_with(sample_user.id, [sample_tag.id])

    def test_get_user_ratings_map_empty(self, service, mock_repository, mock_user_repository, sample_user):
        """get_user_ratings_map returns empty dict when no tag IDs provided."""
        result = service.get_user_ratings_map(sample_user.id, [])
        assert result == {}
        mock_repository.get_user_ratings.assert_not_called()

    def test_get_user_ratings_map_user_missing(self, service, mock_repository, mock_user_repository, sample_tag):
        """get_user_ratings_map raises when user not found."""
        mock_user_repository.get_by_id.return_value = None

        with pytest.raises(EntityNotFoundError):
            service.get_user_ratings_map(uuid4(), [sample_tag.id])

    def test_rate_tag_invalid_rating_too_low(self, service, sample_user, sample_tag):
        """Test rating validation - too low."""
        with pytest.raises(ValidationError):
            service.rate_tag(sample_user.id, sample_tag.id, 0.5)

    def test_rate_tag_invalid_rating_too_high(self, service, sample_user, sample_tag):
        """Test rating validation - too high."""
        with pytest.raises(ValidationError):
            service.rate_tag(sample_user.id, sample_tag.id, 5.5)

    def test_rate_tag_user_not_found(self, service, mock_user_repository, sample_tag):
        """Test rating with non-existent user."""
        user_id = uuid4()
        mock_user_repository.get_by_id.return_value = None

        with pytest.raises(EntityNotFoundError):
            service.rate_tag(user_id, sample_tag.id, 4.0)

    def test_rate_tag_tag_not_found(self, service, mock_repository, mock_user_repository, sample_user):
        """Test rating non-existent tag."""
        tag_id = uuid4()
        mock_user_repository.get_by_id.return_value = sample_user
        mock_repository.get_by_id.return_value = None

        with pytest.raises(EntityNotFoundError):
            service.rate_tag(sample_user.id, tag_id, 4.0)

    def test_delete_rating(self, service, mock_repository):
        """Test deleting a rating."""
        user_id = uuid4()
        tag_id = uuid4()
        mock_repository.delete_rating.return_value = True

        result = service.delete_rating(user_id, tag_id)

        assert result is True
        mock_repository.delete_rating.assert_called_once_with(user_id, tag_id)

    def test_get_user_rating(self, service, mock_repository, sample_user, sample_tag):
        """Test getting user's rating."""
        rating_obj = TagRating(
            id=1,
            user_id=sample_user.id,
            tag_id=sample_tag.id,
            rating=4.0
        )
        mock_repository.get_user_rating.return_value = rating_obj

        result = service.get_user_rating(sample_user.id, sample_tag.id)

        assert result == 4.0

    def test_get_user_rating_not_found(self, service, mock_repository):
        """Test getting non-existent rating."""
        mock_repository.get_user_rating.return_value = None

        result = service.get_user_rating(uuid4(), uuid4())

        assert result is None


class TestTagServiceFavorites:
    """Test favorites operations."""

    def test_get_user_favorites(self, service, mock_user_repository, mock_repository, sample_user, sample_tag):
        """Test getting user's favorites."""
        sample_user.favorite_tag_ids = [sample_tag.id]
        mock_user_repository.get_by_id.return_value = sample_user
        mock_repository.get_by_ids.return_value = [sample_tag]

        result = service.get_user_favorites(sample_user.id)

        assert len(result) == 1
        assert result[0] == sample_tag

    def test_get_user_favorites_empty(self, service, mock_user_repository, sample_user):
        """Test getting favorites when user has none."""
        sample_user.favorite_tag_ids = []
        mock_user_repository.get_by_id.return_value = sample_user

        result = service.get_user_favorites(sample_user.id)

        assert len(result) == 0

    def test_get_user_favorites_user_not_found(self, service, mock_user_repository):
        """Test getting favorites for non-existent user."""
        mock_user_repository.get_by_id.return_value = None

        with pytest.raises(EntityNotFoundError):
            service.get_user_favorites(uuid4())

    def test_add_favorite(self, service, mock_user_repository, mock_repository, mock_db, sample_user, sample_tag):
        """Test adding tag to favorites."""
        sample_user.favorite_tag_ids = []
        mock_user_repository.get_by_id.return_value = sample_user
        mock_repository.get_by_id.return_value = sample_tag

        result = service.add_favorite(sample_user.id, sample_tag.id)

        assert str(sample_tag.id) in sample_user.favorite_tag_ids
        mock_db.commit.assert_called_once()

    def test_add_favorite_already_exists(self, service, mock_user_repository, mock_repository, mock_db, sample_user, sample_tag):
        """Test adding tag that's already favorited."""
        sample_user.favorite_tag_ids = [str(sample_tag.id)]
        mock_user_repository.get_by_id.return_value = sample_user
        mock_repository.get_by_id.return_value = sample_tag

        result = service.add_favorite(sample_user.id, sample_tag.id)

        # Should not add duplicate
        assert sample_user.favorite_tag_ids.count(str(sample_tag.id)) == 1
        # No commit should be called since there are no changes
        mock_db.commit.assert_not_called()

    def test_remove_favorite(self, service, mock_user_repository, mock_db, sample_user, sample_tag):
        """Test removing tag from favorites."""
        sample_user.favorite_tag_ids = [str(sample_tag.id)]
        mock_user_repository.get_by_id.return_value = sample_user

        result = service.remove_favorite(sample_user.id, sample_tag.id)

        assert str(sample_tag.id) not in sample_user.favorite_tag_ids
        mock_db.commit.assert_called_once()

    def test_remove_favorite_not_in_list(self, service, mock_user_repository, mock_db, sample_user, sample_tag):
        """Test removing tag that's not in favorites."""
        sample_user.favorite_tag_ids = []
        mock_user_repository.get_by_id.return_value = sample_user

        result = service.remove_favorite(sample_user.id, sample_tag.id)

        # Should not error, and should not call commit since there are no changes
        mock_db.commit.assert_not_called()

    def test_is_favorite_true(self, service, mock_user_repository, sample_user, sample_tag):
        """Test checking if tag is favorited - true case."""
        sample_user.favorite_tag_ids = [str(sample_tag.id)]
        mock_user_repository.get_by_id.return_value = sample_user

        result = service.is_favorite(sample_user.id, sample_tag.id)

        assert result is True

    def test_is_favorite_false(self, service, mock_user_repository, sample_user, sample_tag):
        """Test checking if tag is favorited - false case."""
        sample_user.favorite_tag_ids = []
        mock_user_repository.get_by_id.return_value = sample_user

        result = service.is_favorite(sample_user.id, sample_tag.id)

        assert result is False


class TestTagServiceStatistics:
    """Test statistics operations."""

    def test_get_hierarchy_statistics(self, service, mock_repository):
        """Test getting hierarchy statistics."""
        expected_stats = {
            "totalNodes": 100,
            "totalRelationships": 95,
            "rootCategories": 5
        }
        mock_repository.get_hierarchy_statistics.return_value = expected_stats

        result = service.get_hierarchy_statistics()

        assert result == expected_stats
        mock_repository.get_hierarchy_statistics.assert_called_once()


class TestTagServiceGetTagDetail:
    """Test get_tag_detail method."""

    def test_get_tag_detail_with_user(self, service, mock_repository, sample_tag, sample_user):
        """Test getting tag detail with user context."""
        parent_tag = Tag(id=uuid4(), name="Parent", tag_metadata={})
        child_tag = Tag(id=uuid4(), name="Child", tag_metadata={})
        rating_obj = TagRating(id=1, user_id=sample_user.id, tag_id=sample_tag.id, rating=4.5)

        mock_repository.get_by_id.return_value = sample_tag
        mock_repository.get_parents.return_value = [parent_tag]
        mock_repository.get_children.return_value = [child_tag]
        mock_repository.get_tag_average_rating.return_value = (4.2, 10)
        mock_repository.get_user_rating.return_value = rating_obj
        sample_user.favorite_tag_ids = [sample_tag.id]
        service.user_repository.get_by_id.return_value = sample_user

        result = service.get_tag_detail(sample_tag.id, sample_user.id)

        assert result["tag"] == sample_tag
        assert len(result["parents"]) == 1
        assert len(result["children"]) == 1
        assert result["average_rating"] == 4.2
        assert result["rating_count"] == 10
        assert result["user_rating"] == 4.5
        assert result["is_favorite"] is True

    def test_get_tag_detail_without_user(self, service, mock_repository, sample_tag):
        """Test getting tag detail without user context."""
        mock_repository.get_by_id.return_value = sample_tag
        mock_repository.get_parents.return_value = []
        mock_repository.get_children.return_value = []
        mock_repository.get_tag_average_rating.return_value = (4.2, 10)

        result = service.get_tag_detail(sample_tag.id, user_id=None)

        assert result["tag"] == sample_tag
        assert result["user_rating"] is None
        assert result["is_favorite"] is None
