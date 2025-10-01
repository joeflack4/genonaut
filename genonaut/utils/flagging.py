"""Content flagging engine for detecting problematic words in content.

This module provides utilities for scanning content and calculating risk scores
based on configurable danger word lists.
"""

import re
from pathlib import Path
from typing import List, Set, Tuple, Dict, Any, Optional


def load_flag_words(file_path: str) -> Set[str]:
    """Load danger words from a configuration file.

    Args:
        file_path: Path to the flag-words.txt file

    Returns:
        Set of lowercase danger words

    Raises:
        FileNotFoundError: If the flag words file doesn't exist
        ValueError: If the file is empty or contains no valid words
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Flag words file not found: {file_path}")

    with open(path, 'r', encoding='utf-8') as f:
        # Read lines, strip whitespace, filter empty lines and comments
        words = {
            line.strip().lower()
            for line in f
            if line.strip() and not line.strip().startswith('#')
        }

    if not words:
        raise ValueError(f"No valid words found in flag words file: {file_path}")

    return words


def tokenize_text(text: str) -> List[str]:
    """Tokenize text into individual words.

    Splits on whitespace and punctuation, keeping only alphanumeric words.

    Args:
        text: The text to tokenize

    Returns:
        List of lowercase words
    """
    if not text:
        return []

    # Split on whitespace and punctuation, keep only alphanumeric characters
    words = re.findall(r'\b[a-zA-Z0-9]+\b', text.lower())
    return words


def detect_problem_words(
    text: str,
    flag_words: Set[str]
) -> Tuple[List[str], List[str]]:
    """Detect problem words in text.

    Args:
        text: The text to scan
        flag_words: Set of danger words to check against

    Returns:
        Tuple of (all_problem_words, unique_problem_words)
        - all_problem_words: List of all problem word occurrences (with duplicates)
        - unique_problem_words: List of unique problem words found
    """
    if not text or not flag_words:
        return ([], [])

    tokens = tokenize_text(text)
    all_problem_words = [word for word in tokens if word in flag_words]
    unique_problem_words = list(set(all_problem_words))

    return (all_problem_words, unique_problem_words)


def calculate_risk_score(
    total_problem_words: int,
    total_words: int,
    unique_problem_words: int
) -> float:
    """Calculate risk score for flagged content.

    The risk score is calculated as a weighted combination of:
    - 40% weight: problem word percentage
    - 30% weight: total problem word count (normalized to 10 words)
    - 30% weight: unique problem word diversity (normalized to 5 unique words)

    Args:
        total_problem_words: Count of problem word occurrences (with duplicates)
        total_words: Total word count in the text
        unique_problem_words: Count of unique problem words

    Returns:
        Risk score from 0-100, rounded to 2 decimal places
    """
    if total_words == 0:
        return 0.0

    # Calculate percentage score (0-100)
    percentage_score = (total_problem_words / total_words) * 100

    # Calculate count score (normalized to 10 words max, then scaled to 100)
    count_score = min(total_problem_words / 10, 1.0) * 100

    # Calculate diversity score (normalized to 5 unique words max, then scaled to 100)
    diversity_score = min(unique_problem_words / 5, 1.0) * 100

    # Weighted combination
    risk_score = (
        percentage_score * 0.4 +
        count_score * 0.3 +
        diversity_score * 0.3
    )

    return round(risk_score, 2)


def analyze_content(
    text: str,
    flag_words: Set[str]
) -> Dict[str, Any]:
    """Analyze content for problematic words and calculate risk metrics.

    Args:
        text: The text to analyze
        flag_words: Set of danger words to check against

    Returns:
        Dictionary with analysis results:
        {
            'flagged_words': list[str],  # unique problem words found
            'total_problem_words': int,   # count of problem word occurrences
            'total_words': int,           # total word count
            'problem_percentage': float,  # percentage of problematic words
            'risk_score': float,          # calculated risk score (0-100)
            'should_flag': bool           # whether content should be flagged
        }
    """
    if not text:
        return {
            'flagged_words': [],
            'total_problem_words': 0,
            'total_words': 0,
            'problem_percentage': 0.0,
            'risk_score': 0.0,
            'should_flag': False
        }

    # Tokenize and detect problems
    all_tokens = tokenize_text(text)
    total_words = len(all_tokens)
    all_problem_words, unique_problem_words = detect_problem_words(text, flag_words)
    total_problem_words = len(all_problem_words)
    unique_count = len(unique_problem_words)

    # Calculate metrics
    problem_percentage = (total_problem_words / total_words * 100) if total_words > 0 else 0.0
    risk_score = calculate_risk_score(total_problem_words, total_words, unique_count)

    return {
        'flagged_words': sorted(unique_problem_words),  # Sort for consistency
        'total_problem_words': total_problem_words,
        'total_words': total_words,
        'problem_percentage': round(problem_percentage, 2),
        'risk_score': risk_score,
        'should_flag': total_problem_words > 0
    }


def get_default_flag_words_path() -> Optional[str]:
    """Get the default path for flag-words.txt.

    Returns:
        Path to flag-words.txt in project root if it exists, None otherwise
    """
    # Get project root (assuming this file is in genonaut/utils/)
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent
    flag_words_path = project_root / "flag-words.txt"

    if flag_words_path.exists():
        return str(flag_words_path)

    return None
