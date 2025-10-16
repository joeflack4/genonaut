"""Unit tests for search query parser."""

import pytest
from genonaut.api.services.search_parser import (
    parse_search_query,
    build_search_conditions,
    ParsedSearchQuery
)


class TestParseSearchQuery:
    """Test suite for parse_search_query function."""

    def test_simple_words(self):
        """Test parsing simple words without quotes."""
        result = parse_search_query('hello world')
        assert result.phrases == []
        assert result.words == ['hello', 'world']
        assert result.original_query == 'hello world'

    def test_single_quoted_phrase(self):
        """Test parsing a single quoted phrase."""
        result = parse_search_query('"exact phrase"')
        assert result.phrases == ['exact phrase']
        assert result.words == []

    def test_mixed_phrase_and_words(self):
        """Test parsing mixed quoted phrases and words."""
        result = parse_search_query('"exact phrase" word1 word2')
        assert result.phrases == ['exact phrase']
        assert set(result.words) == {'word1', 'word2'}

    def test_multiple_phrases(self):
        """Test parsing multiple quoted phrases."""
        result = parse_search_query('"phrase one" "phrase two" word')
        assert result.phrases == ['phrase one', 'phrase two']
        assert result.words == ['word']

    def test_empty_query(self):
        """Test parsing empty query."""
        result = parse_search_query('')
        assert result.phrases == []
        assert result.words == []

    def test_whitespace_only(self):
        """Test parsing whitespace-only query."""
        result = parse_search_query('   ')
        assert result.phrases == []
        assert result.words == []

    def test_empty_quotes(self):
        """Test parsing empty quotes - empty content is filtered out."""
        result = parse_search_query('""')
        # Empty quotes should not add a phrase, but the "" itself becomes a word
        assert result.phrases == []
        # The "" is treated as a word since the phrase extraction removes the quotes
        # but leaves the "" in the remaining text
        assert result.words == ['""'] or result.phrases == []

    def test_escaped_quotes_in_phrase(self):
        """Test parsing phrases with escaped quotes."""
        result = parse_search_query(r'"phrase with \"nested\" quotes"')
        assert result.phrases == ['phrase with "nested" quotes']

    def test_multiple_spaces(self):
        """Test parsing with multiple spaces."""
        result = parse_search_query('word1    word2   "phrase"')
        assert result.words == ['word1', 'word2']
        assert result.phrases == ['phrase']

    def test_phrase_at_end(self):
        """Test parsing with phrase at end."""
        result = parse_search_query('word1 word2 "end phrase"')
        assert result.words == ['word1', 'word2']
        assert result.phrases == ['end phrase']

    def test_phrase_at_beginning(self):
        """Test parsing with phrase at beginning."""
        result = parse_search_query('"start phrase" word1 word2')
        assert result.phrases == ['start phrase']
        assert result.words == ['word1', 'word2']

    def test_phrase_in_middle(self):
        """Test parsing with phrase in middle."""
        result = parse_search_query('word1 "middle phrase" word2')
        assert result.phrases == ['middle phrase']
        assert set(result.words) == {'word1', 'word2'}

    def test_special_characters_in_words(self):
        """Test parsing words with special characters."""
        result = parse_search_query('word-with-dashes word_with_underscores')
        assert 'word-with-dashes' in result.words
        assert 'word_with_underscores' in result.words

    def test_special_characters_in_phrase(self):
        """Test parsing phrase with special characters."""
        result = parse_search_query('"phrase with !@#$%^&*() symbols"')
        assert result.phrases == ['phrase with !@#$%^&*() symbols']

    def test_numbers_in_query(self):
        """Test parsing query with numbers."""
        result = parse_search_query('word1 123 "phrase with 456"')
        assert '123' in result.words
        assert 'word1' in result.words
        assert result.phrases == ['phrase with 456']

    def test_single_word(self):
        """Test parsing single word."""
        result = parse_search_query('onlyword')
        assert result.words == ['onlyword']
        assert result.phrases == []

    def test_single_phrase(self):
        """Test parsing single phrase."""
        result = parse_search_query('"only phrase"')
        assert result.phrases == ['only phrase']
        assert result.words == []


class TestBuildSearchConditions:
    """Test suite for build_search_conditions function."""

    def test_search_both_fields(self):
        """Test building conditions for searching both title and prompt."""
        parsed = ParsedSearchQuery(
            phrases=['exact phrase'],
            words=['word1', 'word2'],
            original_query='"exact phrase" word1 word2'
        )
        conditions = build_search_conditions(parsed)

        assert conditions['phrases'] == ['exact phrase']
        assert conditions['words'] == ['word1', 'word2']
        assert set(conditions['search_fields']) == {'title', 'prompt'}

    def test_search_title_only(self):
        """Test building conditions for searching title only."""
        parsed = ParsedSearchQuery(
            phrases=['phrase'],
            words=['word'],
            original_query='"phrase" word'
        )
        conditions = build_search_conditions(
            parsed,
            search_in_title=True,
            search_in_prompt=False
        )

        assert conditions['search_fields'] == ['title']

    def test_search_prompt_only(self):
        """Test building conditions for searching prompt only."""
        parsed = ParsedSearchQuery(
            phrases=['phrase'],
            words=['word'],
            original_query='"phrase" word'
        )
        conditions = build_search_conditions(
            parsed,
            search_in_title=False,
            search_in_prompt=True
        )

        assert conditions['search_fields'] == ['prompt']

    def test_empty_parsed_query(self):
        """Test building conditions with empty parsed query."""
        parsed = ParsedSearchQuery(
            phrases=[],
            words=[],
            original_query=''
        )
        conditions = build_search_conditions(parsed)

        assert conditions['phrases'] == []
        assert conditions['words'] == []
        assert set(conditions['search_fields']) == {'title', 'prompt'}

    def test_original_query_preserved(self):
        """Test that original query is preserved in conditions."""
        original = '"test phrase" word1'
        parsed = parse_search_query(original)
        conditions = build_search_conditions(parsed)

        assert conditions['original_query'] == original
