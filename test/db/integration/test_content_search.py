"""Database tests for content search functionality."""

import pytest
from uuid import UUID

from genonaut.db.schema import User, ContentItem, ContentItemAuto
from genonaut.api.models.requests import PaginationRequest
from genonaut.api.services.content_service import ContentService
from genonaut.api.services.search_parser import parse_search_query


@pytest.fixture
def test_user(db_session):
    """Create a test user for content tests."""
    user = User(
        username='test-user',
        email='test@example.com'
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def content_items(db_session, test_user):
    """Create test content items with various titles and prompts."""
    items = [
        ContentItem(
            creator_id=test_user.id,
                content_type="image",
                content_data="path/to/test.jpg",
            title="My cute cat playing",
            prompt="A photo of a cute cat playing with a ball",
            quality_score=0.8
        ),
        ContentItem(
            creator_id=test_user.id,
                content_type="image",
                content_data="path/to/test.jpg",
            title="Beautiful sunset",
            prompt="A beautiful sunset over the ocean",
            quality_score=0.9
        ),
        ContentItem(
            creator_id=test_user.id,
                content_type="image",
                content_data="path/to/test.jpg",
            title="Cat in the garden",
            prompt="A cat sitting in a beautiful garden",
            quality_score=0.7
        ),
        ContentItem(
            creator_id=test_user.id,
                content_type="image",
                content_data="path/to/test.jpg",
            title="Dog playing fetch",
            prompt="A happy dog playing fetch in the park",
            quality_score=0.85
        ),
        ContentItem(
            creator_id=test_user.id,
                content_type="image",
                content_data="path/to/test.jpg",
            title="The black cat mystery",
            prompt="A mysterious black cat in the moonlight",
            quality_score=0.75
        ),
    ]

    for item in items:
        db_session.add(item)

    db_session.commit()
    for item in items:
        db_session.refresh(item)

    return items


@pytest.fixture
def auto_content_items(db_session, test_user):
    """Create test auto-generated content items."""
    items = [
        ContentItemAuto(
            creator_id=test_user.id,
                content_type="image",
                content_data="path/to/test.jpg",
            title="Auto: Cat portrait",
            prompt="An artistic cat portrait with dramatic lighting",
            quality_score=0.8
        ),
        ContentItemAuto(
            creator_id=test_user.id,
                content_type="image",
                content_data="path/to/test.jpg",
            title="Auto: Ocean waves",
            prompt="Crashing ocean waves at sunset",
            quality_score=0.9
        ),
    ]

    for item in items:
        db_session.add(item)

    db_session.commit()
    for item in items:
        db_session.refresh(item)

    return items


@pytest.fixture
def content_service(db_session):
    """Create content service instance."""
    return ContentService(db_session)


class TestSimpleWordSearch:
    """Test simple word-based search (no quotes)."""

    def test_search_single_word_in_title(self, content_service, test_user, content_items):
        """Test searching for a single word that appears in titles."""
        result = content_service.get_unified_content_paginated(
            pagination=PaginationRequest(page=1, page_size=10),
            user_id=test_user.id,
            search_term="cat"
        )

        items = result["items"]
        assert len(items) == 3  # Three items have "cat" in title or prompt
        titles = [item["title"] for item in items]
        assert any("cat" in title.lower() for title in titles)

    def test_search_single_word_in_prompt(self, content_service, test_user, content_items):
        """Test searching for a word that only appears in prompts."""
        result = content_service.get_unified_content_paginated(
            pagination=PaginationRequest(page=1, page_size=10),
            user_id=test_user.id,
            search_term="ocean"
        )

        items = result["items"]
        assert len(items) == 1
        assert "ocean" in items[0]["prompt"].lower()

    def test_search_multiple_words_and_logic(self, content_service, test_user, content_items):
        """Test that multiple words use AND logic (all must match)."""
        result = content_service.get_unified_content_paginated(
            pagination=PaginationRequest(page=1, page_size=10),
            user_id=test_user.id,
            search_term="cat playing"  # Both words must appear
        )

        items = result["items"]
        # Only "My cute cat playing" has both words
        assert len(items) == 1
        assert "cat" in items[0]["title"].lower()
        assert "playing" in items[0]["title"].lower()

    def test_search_case_insensitive(self, content_service, test_user, content_items):
        """Test that search is case insensitive."""
        # Search with different cases
        result1 = content_service.get_unified_content_paginated(
            pagination=PaginationRequest(page=1, page_size=10),
            user_id=test_user.id,
            search_term="CAT"
        )

        result2 = content_service.get_unified_content_paginated(
            pagination=PaginationRequest(page=1, page_size=10),
            user_id=test_user.id,
            search_term="cat"
        )

        result3 = content_service.get_unified_content_paginated(
            pagination=PaginationRequest(page=1, page_size=10),
            user_id=test_user.id,
            search_term="CaT"
        )

        # All should return same results
        assert len(result1["items"]) == len(result2["items"]) == len(result3["items"])

    def test_search_no_results(self, content_service, test_user, content_items):
        """Test search with no matching results."""
        result = content_service.get_unified_content_paginated(
            pagination=PaginationRequest(page=1, page_size=10),
            user_id=test_user.id,
            search_term="nonexistent"
        )

        assert len(result["items"]) == 0
        assert result["pagination"]["total_count"] == 0


class TestQuotedPhraseSearch:
    """Test search with quoted phrases for exact matching."""

    def test_search_exact_phrase(self, content_service, test_user, content_items):
        """Test searching for an exact phrase in quotes."""
        result = content_service.get_unified_content_paginated(
            pagination=PaginationRequest(page=1, page_size=10),
            user_id=test_user.id,
            search_term='"black cat"'
        )

        items = result["items"]
        assert len(items) == 1
        # Should find "The black cat mystery"
        assert "black cat" in items[0]["title"].lower()

    def test_search_phrase_partial_match_fails(self, content_service, test_user, content_items):
        """Test that partial phrase match doesn't count."""
        # "cat black" (reversed) should not match "black cat"
        result = content_service.get_unified_content_paginated(
            pagination=PaginationRequest(page=1, page_size=10),
            user_id=test_user.id,
            search_term='"cat black"'
        )

        # Should find nothing (phrase must be exact)
        assert len(result["items"]) == 0

    def test_search_phrase_in_prompt(self, content_service, test_user, content_items):
        """Test exact phrase search in prompts."""
        result = content_service.get_unified_content_paginated(
            pagination=PaginationRequest(page=1, page_size=10),
            user_id=test_user.id,
            search_term='"playing with a ball"'
        )

        items = result["items"]
        assert len(items) == 1
        assert "playing with a ball" in items[0]["prompt"].lower()

    def test_search_multiple_phrases(self, content_service, test_user, content_items):
        """Test search with multiple quoted phrases (AND logic)."""
        # Add an item that has both phrases
        from genonaut.db.schema import ContentItem
        item = ContentItem(
            creator_id=test_user.id,
                content_type="image",
                content_data="path/to/test.jpg",
            title="Test item",
            prompt="A cute cat and a happy dog playing together",
            quality_score=0.8
        )
        content_service.db.add(item)
        content_service.db.commit()

        result = content_service.get_unified_content_paginated(
            pagination=PaginationRequest(page=1, page_size=10),
            user_id=test_user.id,
            search_term='"cute cat" "happy dog"'
        )

        items = result["items"]
        assert len(items) == 1
        assert "cute cat" in items[0]["prompt"].lower()
        assert "happy dog" in items[0]["prompt"].lower()


class TestMixedQuotedUnquotedSearch:
    """Test search combining quoted phrases and unquoted words."""

    def test_mixed_phrase_and_word(self, content_service, test_user, content_items):
        """Test combining quoted phrase with unquoted word."""
        result = content_service.get_unified_content_paginated(
            pagination=PaginationRequest(page=1, page_size=10),
            user_id=test_user.id,
            search_term='"black cat" mystery'
        )

        items = result["items"]
        assert len(items) == 1
        # Must have both "black cat" phrase and "mystery" word
        item_text = (items[0]["title"] + " " + items[0]["prompt"]).lower()
        assert "black cat" in item_text
        assert "mystery" in item_text

    def test_mixed_word_and_phrase_order_independent(self, content_service, test_user, content_items):
        """Test that order of quoted/unquoted doesn't matter."""
        result1 = content_service.get_unified_content_paginated(
            pagination=PaginationRequest(page=1, page_size=10),
            user_id=test_user.id,
            search_term='"black cat" mystery'
        )

        result2 = content_service.get_unified_content_paginated(
            pagination=PaginationRequest(page=1, page_size=10),
            user_id=test_user.id,
            search_term='mystery "black cat"'
        )

        # Both should return same results
        assert len(result1["items"]) == len(result2["items"])


class TestSearchInTitleAndPrompt:
    """Test that search looks in both title and prompt fields."""

    def test_search_matches_title_only(self, content_service, test_user, content_items):
        """Test finding items where search term only in title."""
        result = content_service.get_unified_content_paginated(
            pagination=PaginationRequest(page=1, page_size=10),
            user_id=test_user.id,
            search_term="sunset"
        )

        items = result["items"]
        # "Beautiful sunset" (in title) and "Auto: Ocean waves" (in prompt)
        assert len(items) >= 1

    def test_search_matches_prompt_only(self, content_service, test_user, content_items):
        """Test finding items where search term only in prompt."""
        result = content_service.get_unified_content_paginated(
            pagination=PaginationRequest(page=1, page_size=10),
            user_id=test_user.id,
            search_term="moonlight"
        )

        items = result["items"]
        assert len(items) == 1
        # Term only in prompt, not title
        assert "moonlight" not in items[0]["title"].lower()
        assert "moonlight" in items[0]["prompt"].lower()

    def test_search_matches_both(self, content_service, test_user, content_items):
        """Test finding items where term appears in both title and prompt."""
        result = content_service.get_unified_content_paginated(
            pagination=PaginationRequest(page=1, page_size=10),
            user_id=test_user.id,
            search_term="cat"
        )

        items = result["items"]
        # Multiple items should match
        assert len(items) >= 3


class TestSearchAcrossContentTypes:
    """Test that search works across regular and auto-generated content."""

    def test_search_ocean_both_types(
        self,
        content_service,
        test_user,
        content_items,
        auto_content_items
    ):
        """Test search finds 'ocean' in both regular and auto content."""
        result = content_service.get_unified_content_paginated(
            pagination=PaginationRequest(page=1, page_size=20),
            user_id=test_user.id,
            search_term="ocean"
        )

        items = result["items"]
        # Should find "Beautiful sunset" (regular) and "Auto: Ocean waves" (auto)
        assert len(items) == 2


class TestEmptyAndEdgeCaseSearches:
    """Test edge cases in search."""

    def test_empty_search_returns_all(self, content_service, test_user, content_items):
        """Test that empty search returns all items."""
        result = content_service.get_unified_content_paginated(
            pagination=PaginationRequest(page=1, page_size=20),
            user_id=test_user.id,
            search_term=""
        )

        # Should return all items
        assert len(result["items"]) >= len(content_items)

    def test_none_search_returns_all(self, content_service, test_user, content_items):
        """Test that None search returns all items."""
        result = content_service.get_unified_content_paginated(
            pagination=PaginationRequest(page=1, page_size=20),
            user_id=test_user.id,
            search_term=None
        )

        # Should return all items
        assert len(result["items"]) >= len(content_items)

    def test_whitespace_only_search(self, content_service, test_user, content_items):
        """Test search with only whitespace."""
        result = content_service.get_unified_content_paginated(
            pagination=PaginationRequest(page=1, page_size=20),
            user_id=test_user.id,
            search_term="   "
        )

        # Should return all items (treated as empty)
        assert len(result["items"]) >= len(content_items)

    def test_empty_quotes_search(self, content_service, test_user, content_items):
        """Test search with empty quotes."""
        result = content_service.get_unified_content_paginated(
            pagination=PaginationRequest(page=1, page_size=20),
            user_id=test_user.id,
            search_term='""'
        )

        # Should return all items (empty phrase ignored)
        assert len(result["items"]) >= len(content_items)

    def test_special_characters_search(self, content_service, test_user, content_items, db_session):
        """Test search with special characters."""
        # Add item with special characters
        item = ContentItem(
            creator_id=test_user.id,
                content_type="image",
                content_data="path/to/test.jpg",
            title="Test: Special & chars!",
            prompt="Testing @#$% special characters",
            quality_score=0.8
        )
        db_session.add(item)
        db_session.commit()

        result = content_service.get_unified_content_paginated(
            pagination=PaginationRequest(page=1, page_size=20),
            user_id=test_user.id,
            search_term="Special"
        )

        # Should find the item
        items = result["items"]
        assert len(items) >= 1
        assert any("special" in item["title"].lower() for item in items)


class TestSearchPagination:
    """Test that pagination works correctly with search."""

    def test_search_second_page(self, content_service, test_user, db_session):
        """Test second page of search results."""
        for i in range(25):
            item = ContentItem(
                creator_id=test_user.id,
                content_type="image",
                content_data="path/to/test.jpg",
                title=f"Secondpagetest item {i}",
                prompt=f"Secondpagetest prompt {i}",
                quality_score=0.8
            )
            db_session.add(item)
        db_session.commit()

        result = content_service.get_unified_content_paginated(
            pagination=PaginationRequest(page=2, page_size=10),
            user_id=test_user.id,
            search_term="secondpagetest"
        )

        assert len(result["items"]) == 10
        assert result["pagination"]["page"] == 2
        assert result["pagination"]["has_next"] is True
        assert result["pagination"]["has_previous"] is True
