"""Database tests for FlaggedContentRepository."""

import pytest
import sys
from pathlib import Path
from datetime import datetime
from sqlalchemy.exc import IntegrityError

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from genonaut.db.schema import Base, User, ContentItem, ContentItemAuto, FlaggedContent
from genonaut.api.repositories.flagged_content_repository import FlaggedContentRepository
from genonaut.api.models.requests import PaginationRequest
from genonaut.api.exceptions import EntityNotFoundError


class TestFlaggedContentRepository:
    """Test cases for FlaggedContentRepository."""

    @pytest.fixture(autouse=True)
    def setup_method(self, db_session):
        """Set up test database and session for each test."""
        # Use PostgreSQL test database (provided by conftest.py)
        self.session = db_session
        self.repository = FlaggedContentRepository(self.session)

        # Create test users
        self.user1 = User(
            username="testuser1",
            email="test1@example.com",
            preferences={}
        )
        self.user2 = User(
            username="testuser2",
            email="test2@example.com",
            preferences={}
        )

        self.session.add_all([self.user1, self.user2])
        self.session.commit()

        # Create test content items
        self.content1 = ContentItem(
            title="Test Content 1",
            content_type="text",
            content_data="Test content data",
            creator_id=self.user1.id,
            item_metadata={"prompt": "violence and hatred"},
            prompt="Test prompt"
        )
        self.content2 = ContentItem(
            title="Test Content 2",
            content_type="text",
            content_data="Test content data 2",
            creator_id=self.user2.id,
            item_metadata={"prompt": "peaceful scene"},
            prompt="Test prompt"
        )

        self.session.add_all([self.content1, self.content2])
        self.session.commit()

    def test_create_flagged_content(self):
        """Test creating a flagged content record."""
        flagged = self.repository.create(
            content_item_id=self.content1.id,
            content_item_auto_id=None,
            content_source='regular',
            flagged_text="violence and hatred",
            flagged_words=["violence", "hatred"],
            total_problem_words=2,
            total_words=3,
            problem_percentage=66.67,
            risk_score=75.5,
            creator_id=self.user1.id
        )

        assert flagged.id is not None
        assert flagged.content_item_id == self.content1.id
        assert flagged.content_source == 'regular'
        assert flagged.flagged_words == ["violence", "hatred"]
        assert flagged.total_problem_words == 2
        assert flagged.risk_score == 75.5
        assert flagged.reviewed is False

    def test_get_by_id(self):
        """Test retrieving flagged content by ID."""
        flagged = self.repository.create(
            content_item_id=self.content1.id,
            content_item_auto_id=None,
            content_source='regular',
            flagged_text="test",
            flagged_words=["violence"],
            total_problem_words=1,
            total_words=5,
            problem_percentage=20.0,
            risk_score=30.0,
            creator_id=self.user1.id
        )

        retrieved = self.repository.get_by_id(flagged.id)
        assert retrieved is not None
        assert retrieved.id == flagged.id
        assert retrieved.content_item_id == self.content1.id

    def test_get_by_id_not_found(self):
        """Test retrieving non-existent flagged content."""
        result = self.repository.get_by_id(99999)
        assert result is None

    def test_get_by_content_item(self):
        """Test retrieving flagged content by content item reference."""
        flagged = self.repository.create(
            content_item_id=self.content1.id,
            content_item_auto_id=None,
            content_source='regular',
            flagged_text="test",
            flagged_words=["violence"],
            total_problem_words=1,
            total_words=5,
            problem_percentage=20.0,
            risk_score=30.0,
            creator_id=self.user1.id
        )

        retrieved = self.repository.get_by_content_item(content_item_id=self.content1.id)
        assert retrieved is not None
        assert retrieved.id == flagged.id

    def test_get_paginated_no_filters(self):
        """Test paginated retrieval without filters."""
        # Create multiple flagged items
        for i in range(5):
            self.repository.create(
                content_item_id=self.content1.id if i % 2 == 0 else self.content2.id,
                content_item_auto_id=None,
                content_source='regular',
                flagged_text=f"test {i}",
                flagged_words=["violence"],
                total_problem_words=1,
                total_words=5,
                problem_percentage=20.0,
                risk_score=30.0 + i,
                creator_id=self.user1.id if i % 2 == 0 else self.user2.id
            )

        pagination = PaginationRequest(page=1, page_size=3)
        result = self.repository.get_paginated(pagination)

        assert result.pagination.total_count == 5
        assert len(result.items) == 3
        assert result.pagination.page == 1
        assert result.pagination.has_next is True

    def test_get_paginated_with_creator_filter(self):
        """Test paginated retrieval filtered by creator."""
        # Create flagged items for different creators
        for i in range(3):
            self.repository.create(
                content_item_id=self.content1.id,
                content_item_auto_id=None,
                content_source='regular',
                flagged_text=f"test {i}",
                flagged_words=["violence"],
                total_problem_words=1,
                total_words=5,
                problem_percentage=20.0,
                risk_score=30.0,
                creator_id=self.user1.id
            )

        for i in range(2):
            self.repository.create(
                content_item_id=self.content2.id,
                content_item_auto_id=None,
                content_source='regular',
                flagged_text=f"test {i}",
                flagged_words=["hatred"],
                total_problem_words=1,
                total_words=5,
                problem_percentage=20.0,
                risk_score=40.0,
                creator_id=self.user2.id
            )

        pagination = PaginationRequest(page=1, page_size=10)
        result = self.repository.get_paginated(
            pagination,
            creator_id=self.user1.id
        )

        assert result.pagination.total_count == 3
        assert all(item.creator_id == self.user1.id for item in result.items)

    def test_get_paginated_with_risk_score_filter(self):
        """Test paginated retrieval filtered by risk score range."""
        # Create items with different risk scores
        risk_scores = [25.0, 50.0, 75.0, 90.0]
        for score in risk_scores:
            self.repository.create(
                content_item_id=self.content1.id,
                content_item_auto_id=None,
                content_source='regular',
                flagged_text="test",
                flagged_words=["violence"],
                total_problem_words=1,
                total_words=5,
                problem_percentage=20.0,
                risk_score=score,
                creator_id=self.user1.id
            )

        pagination = PaginationRequest(page=1, page_size=10)
        result = self.repository.get_paginated(
            pagination,
            min_risk_score=50.0,
            max_risk_score=80.0
        )

        assert result.pagination.total_count == 2
        assert all(50.0 <= item.risk_score <= 80.0 for item in result.items)

    def test_get_paginated_with_reviewed_filter(self):
        """Test paginated retrieval filtered by review status."""
        # Create reviewed and unreviewed items
        flagged1 = self.repository.create(
            content_item_id=self.content1.id,
            content_item_auto_id=None,
            content_source='regular',
            flagged_text="test",
            flagged_words=["violence"],
            total_problem_words=1,
            total_words=5,
            problem_percentage=20.0,
            risk_score=30.0,
            creator_id=self.user1.id
        )

        flagged2 = self.repository.create(
            content_item_id=self.content2.id,
            content_item_auto_id=None,
            content_source='regular',
            flagged_text="test",
            flagged_words=["hatred"],
            total_problem_words=1,
            total_words=5,
            problem_percentage=20.0,
            risk_score=40.0,
            creator_id=self.user2.id
        )

        # Mark one as reviewed
        self.repository.update_review_status(
            flagged_content_id=flagged1.id,
            reviewed=True,
            reviewed_by=self.user1.id,
            notes="Checked"
        )

        pagination = PaginationRequest(page=1, page_size=10)
        result = self.repository.get_paginated(
            pagination,
            reviewed=False
        )

        assert result.pagination.total_count == 1
        assert result.items[0].id == flagged2.id

    def test_get_paginated_sorting(self):
        """Test paginated retrieval with different sorting options."""
        # Create items with different risk scores
        risk_scores = [75.0, 25.0, 50.0]
        for score in risk_scores:
            self.repository.create(
                content_item_id=self.content1.id,
                content_item_auto_id=None,
                content_source='regular',
                flagged_text="test",
                flagged_words=["violence"],
                total_problem_words=1,
                total_words=5,
                problem_percentage=20.0,
                risk_score=score,
                creator_id=self.user1.id
            )

        pagination = PaginationRequest(page=1, page_size=10)

        # Test descending sort by risk score
        result_desc = self.repository.get_paginated(
            pagination,
            sort_by='risk_score',
            sort_order='desc'
        )
        assert result_desc.items[0].risk_score == 75.0
        assert result_desc.items[2].risk_score == 25.0

        # Test ascending sort by risk score
        result_asc = self.repository.get_paginated(
            pagination,
            sort_by='risk_score',
            sort_order='asc'
        )
        assert result_asc.items[0].risk_score == 25.0
        assert result_asc.items[2].risk_score == 75.0

    def test_update_review_status(self):
        """Test updating review status of flagged content."""
        flagged = self.repository.create(
            content_item_id=self.content1.id,
            content_item_auto_id=None,
            content_source='regular',
            flagged_text="test",
            flagged_words=["violence"],
            total_problem_words=1,
            total_words=5,
            problem_percentage=20.0,
            risk_score=30.0,
            creator_id=self.user1.id
        )

        updated = self.repository.update_review_status(
            flagged_content_id=flagged.id,
            reviewed=True,
            reviewed_by=self.user1.id,
            notes="Approved after review"
        )

        assert updated.reviewed is True
        assert updated.reviewed_by == self.user1.id
        assert updated.reviewed_at is not None
        assert updated.notes == "Approved after review"

    def test_update_review_status_not_found(self):
        """Test updating review status of non-existent item."""
        with pytest.raises(EntityNotFoundError):
            self.repository.update_review_status(
                flagged_content_id=99999,
                reviewed=True,
                reviewed_by=self.user1.id
            )

    def test_delete_not_found(self):
        """Test deleting non-existent flagged content."""
        with pytest.raises(EntityNotFoundError):
            self.repository.delete(99999)

    def test_get_statistics(self):
        """Test retrieving statistics about flagged content."""
        # Create flagged items with varying properties
        self.repository.create(
            content_item_id=self.content1.id,
            content_item_auto_id=None,
            content_source='regular',
            flagged_text="test",
            flagged_words=["violence"],
            total_problem_words=1,
            total_words=5,
            problem_percentage=20.0,
            risk_score=80.0,
            creator_id=self.user1.id
        )

        flagged2 = self.repository.create(
            content_item_id=self.content2.id,
            content_item_auto_id=None,
            content_source='regular',
            flagged_text="test",
            flagged_words=["hatred"],
            total_problem_words=1,
            total_words=5,
            problem_percentage=20.0,
            risk_score=60.0,
            creator_id=self.user2.id
        )

        # Mark one as reviewed
        self.repository.update_review_status(
            flagged_content_id=flagged2.id,
            reviewed=True,
            reviewed_by=self.user1.id
        )

        stats = self.repository.get_statistics()

        assert stats['total_flagged'] == 2
        assert stats['unreviewed_count'] == 1
        assert stats['average_risk_score'] == 70.0
        assert stats['high_risk_count'] == 1  # Only one >= 75
        assert stats['by_source']['regular'] == 2
