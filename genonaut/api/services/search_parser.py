"""Search query parser for content search functionality.

This module provides functionality to parse user search queries and extract
quoted phrases and individual words for use in database queries.
"""

import re
from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class ParsedSearchQuery:
    """Parsed search query containing phrases and words.

    Attributes:
        phrases: List of quoted phrases to match exactly
        words: List of individual words to match (from non-quoted parts)
        original_query: The original unparsed query string
    """
    phrases: List[str]
    words: List[str]
    original_query: str


def parse_search_query(query: str) -> ParsedSearchQuery:
    """Parse a search query into quoted phrases and individual words.

    Extracts text within quotes as literal phrases, and treats remaining
    text as individual words. Handles escaped quotes and empty strings.

    Args:
        query: The search query string to parse

    Returns:
        ParsedSearchQuery containing phrases, words, and original query

    Examples:
        >>> parse_search_query('hello world')
        ParsedSearchQuery(phrases=[], words=['hello', 'world'], original_query='hello world')

        >>> parse_search_query('"exact phrase" word1 word2')
        ParsedSearchQuery(phrases=['exact phrase'], words=['word1', 'word2'], ...)

        >>> parse_search_query('"phrase one" "phrase two" word')
        ParsedSearchQuery(phrases=['phrase one', 'phrase two'], words=['word'], ...)
    """
    if not query or not query.strip():
        return ParsedSearchQuery(phrases=[], words=[], original_query=query)

    phrases: List[str] = []
    remaining_text = query

    # Extract quoted phrases using regex
    # Match text within double quotes, handling escaped quotes
    quote_pattern = r'"([^"\\]*(?:\\.[^"\\]*)*)"'
    matches = re.finditer(quote_pattern, query)

    # Collect phrases and their positions
    phrase_positions: List[Tuple[int, int]] = []
    for match in matches:
        phrase = match.group(1)
        # Unescape any escaped quotes
        phrase = phrase.replace('\\"', '"')
        # Always track position to remove quotes from remaining text
        phrase_positions.append((match.start(), match.end()))
        if phrase.strip():  # Only add non-empty phrases to results
            phrases.append(phrase.strip())

    # Remove quoted sections from the query to get remaining text
    if phrase_positions:
        # Build remaining text by excluding quoted sections
        parts = []
        last_end = 0
        for start, end in phrase_positions:
            parts.append(query[last_end:start])
            last_end = end
        parts.append(query[last_end:])
        remaining_text = ' '.join(parts)

    # Extract individual words from remaining text
    words = [word.strip() for word in remaining_text.split() if word.strip()]

    return ParsedSearchQuery(
        phrases=phrases,
        words=words,
        original_query=query
    )


def build_search_conditions(
    parsed_query: ParsedSearchQuery,
    search_in_title: bool = True,
    search_in_prompt: bool = True
) -> dict:
    """Build search conditions from a parsed query for database filtering.

    Creates a dictionary with conditions for phrase matching (exact) and
    word matching (any word) that can be used by repository/service layers.

    Args:
        parsed_query: The parsed search query
        search_in_title: Whether to search in title field
        search_in_prompt: Whether to search in prompt field

    Returns:
        Dictionary with search conditions:
        {
            'phrases': List of phrases for exact matching,
            'words': List of words for word matching,
            'search_fields': List of field names to search ('title', 'prompt')
        }
    """
    search_fields = []
    if search_in_title:
        search_fields.append('title')
    if search_in_prompt:
        search_fields.append('prompt')

    return {
        'phrases': parsed_query.phrases,
        'words': parsed_query.words,
        'search_fields': search_fields,
        'original_query': parsed_query.original_query
    }
