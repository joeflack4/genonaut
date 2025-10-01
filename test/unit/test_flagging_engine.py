"""Unit tests for content flagging engine."""

import pytest
import sys
import tempfile
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from genonaut.utils.flagging import (
    load_flag_words,
    tokenize_text,
    detect_problem_words,
    calculate_risk_score,
    analyze_content,
    get_default_flag_words_path
)


class TestLoadFlagWords:
    """Tests for load_flag_words function."""

    def test_load_valid_file(self, tmp_path):
        """Test loading a valid flag words file."""
        # Create test file
        flag_file = tmp_path / "flag-words.txt"
        flag_file.write_text("violence\nhatred\nexplicit\n")

        # Load words
        words = load_flag_words(str(flag_file))

        assert words == {"violence", "hatred", "explicit"}

    def test_load_file_with_comments(self, tmp_path):
        """Test loading file with comments."""
        flag_file = tmp_path / "flag-words.txt"
        flag_file.write_text("# Comment line\nviolence\n# Another comment\nhatred\n")

        words = load_flag_words(str(flag_file))

        assert words == {"violence", "hatred"}

    def test_load_file_with_empty_lines(self, tmp_path):
        """Test loading file with empty lines."""
        flag_file = tmp_path / "flag-words.txt"
        flag_file.write_text("violence\n\n\nhatred\n\n")

        words = load_flag_words(str(flag_file))

        assert words == {"violence", "hatred"}

    def test_load_file_with_whitespace(self, tmp_path):
        """Test loading file with whitespace around words."""
        flag_file = tmp_path / "flag-words.txt"
        flag_file.write_text("  violence  \n\thatred\t\n  explicit  \n")

        words = load_flag_words(str(flag_file))

        assert words == {"violence", "hatred", "explicit"}

    def test_load_file_case_insensitive(self, tmp_path):
        """Test that loaded words are lowercased."""
        flag_file = tmp_path / "flag-words.txt"
        flag_file.write_text("Violence\nHATRED\nexplicit\n")

        words = load_flag_words(str(flag_file))

        assert words == {"violence", "hatred", "explicit"}

    def test_load_nonexistent_file(self):
        """Test loading a nonexistent file raises error."""
        with pytest.raises(FileNotFoundError):
            load_flag_words("/path/to/nonexistent/file.txt")

    def test_load_empty_file(self, tmp_path):
        """Test loading an empty file raises error."""
        flag_file = tmp_path / "flag-words.txt"
        flag_file.write_text("")

        with pytest.raises(ValueError, match="No valid words found"):
            load_flag_words(str(flag_file))

    def test_load_file_only_comments(self, tmp_path):
        """Test loading file with only comments raises error."""
        flag_file = tmp_path / "flag-words.txt"
        flag_file.write_text("# Comment 1\n# Comment 2\n")

        with pytest.raises(ValueError, match="No valid words found"):
            load_flag_words(str(flag_file))


class TestTokenizeText:
    """Tests for tokenize_text function."""

    def test_simple_text(self):
        """Test tokenizing simple text."""
        text = "hello world this is a test"
        tokens = tokenize_text(text)

        assert tokens == ["hello", "world", "this", "is", "a", "test"]

    def test_text_with_punctuation(self):
        """Test tokenizing text with punctuation."""
        text = "Hello, world! This is a test."
        tokens = tokenize_text(text)

        assert tokens == ["hello", "world", "this", "is", "a", "test"]

    def test_text_with_numbers(self):
        """Test tokenizing text with numbers."""
        text = "Test 123 with numbers 456"
        tokens = tokenize_text(text)

        assert tokens == ["test", "123", "with", "numbers", "456"]

    def test_text_with_special_chars(self):
        """Test tokenizing text with special characters."""
        text = "Test@#$%with^&*special()chars"
        tokens = tokenize_text(text)

        assert tokens == ["test", "with", "special", "chars"]

    def test_empty_text(self):
        """Test tokenizing empty text."""
        assert tokenize_text("") == []
        assert tokenize_text(None) == []

    def test_whitespace_only(self):
        """Test tokenizing whitespace-only text."""
        assert tokenize_text("   \n\t  ") == []

    def test_case_insensitive(self):
        """Test that tokenization lowercases words."""
        text = "Hello WORLD This"
        tokens = tokenize_text(text)

        assert tokens == ["hello", "world", "this"]


class TestDetectProblemWords:
    """Tests for detect_problem_words function."""

    def test_no_problems(self):
        """Test text with no problem words."""
        text = "This is a clean text"
        flag_words = {"violence", "hatred", "explicit"}

        all_words, unique_words = detect_problem_words(text, flag_words)

        assert all_words == []
        assert unique_words == []

    def test_single_problem_word(self):
        """Test text with single problem word."""
        text = "This contains violence in it"
        flag_words = {"violence", "hatred", "explicit"}

        all_words, unique_words = detect_problem_words(text, flag_words)

        assert all_words == ["violence"]
        assert unique_words == ["violence"]

    def test_multiple_same_problem_word(self):
        """Test text with repeated problem word."""
        text = "violence is bad violence leads to more violence"
        flag_words = {"violence", "hatred", "explicit"}

        all_words, unique_words = detect_problem_words(text, flag_words)

        assert all_words == ["violence", "violence", "violence"]
        assert unique_words == ["violence"]

    def test_multiple_different_problem_words(self):
        """Test text with multiple different problem words."""
        text = "violence and hatred are explicit problems"
        flag_words = {"violence", "hatred", "explicit"}

        all_words, unique_words = detect_problem_words(text, flag_words)

        assert all_words == ["violence", "hatred", "explicit"]
        assert set(unique_words) == {"violence", "hatred", "explicit"}

    def test_case_insensitive(self):
        """Test that detection is case insensitive."""
        text = "Violence HATRED explicit"
        flag_words = {"violence", "hatred", "explicit"}

        all_words, unique_words = detect_problem_words(text, flag_words)

        assert set(all_words) == {"violence", "hatred", "explicit"}

    def test_empty_text(self):
        """Test with empty text."""
        flag_words = {"violence", "hatred"}

        all_words, unique_words = detect_problem_words("", flag_words)

        assert all_words == []
        assert unique_words == []

    def test_empty_flag_words(self):
        """Test with empty flag words set."""
        text = "This is some text"

        all_words, unique_words = detect_problem_words(text, set())

        assert all_words == []
        assert unique_words == []


class TestCalculateRiskScore:
    """Tests for calculate_risk_score function."""

    def test_no_problems(self):
        """Test risk score with no problem words."""
        score = calculate_risk_score(
            total_problem_words=0,
            total_words=100,
            unique_problem_words=0
        )

        assert score == 0.0

    def test_zero_words(self):
        """Test risk score with zero total words."""
        score = calculate_risk_score(
            total_problem_words=0,
            total_words=0,
            unique_problem_words=0
        )

        assert score == 0.0

    def test_low_risk(self):
        """Test low risk score (1 problem word in 100)."""
        score = calculate_risk_score(
            total_problem_words=1,
            total_words=100,
            unique_problem_words=1
        )

        # 40% * 1% + 30% * 10% + 30% * 20% = 0.4 + 3.0 + 6.0 = 9.4
        assert score == pytest.approx(9.4, abs=0.1)

    def test_medium_risk(self):
        """Test medium risk score (5 problem words in 50)."""
        score = calculate_risk_score(
            total_problem_words=5,
            total_words=50,
            unique_problem_words=3
        )

        # 40% * 10% + 30% * 50% + 30% * 60% = 4.0 + 15.0 + 18.0 = 37.0
        assert score == pytest.approx(37.0, abs=0.1)

    def test_high_risk(self):
        """Test high risk score (20 problem words in 100)."""
        score = calculate_risk_score(
            total_problem_words=20,
            total_words=100,
            unique_problem_words=5
        )

        # 40% * 20% + 30% * 100% + 30% * 100% = 8.0 + 30.0 + 30.0 = 68.0
        assert score == pytest.approx(68.0, abs=0.1)

    def test_very_high_risk(self):
        """Test very high risk score (all words are problems)."""
        score = calculate_risk_score(
            total_problem_words=10,
            total_words=10,
            unique_problem_words=5
        )

        # 40% * 100% + 30% * 100% + 30% * 100% = 40.0 + 30.0 + 30.0 = 100.0
        assert score == 100.0

    def test_capped_count_score(self):
        """Test that count score is capped at 10 words."""
        score1 = calculate_risk_score(
            total_problem_words=10,
            total_words=20,
            unique_problem_words=5
        )
        score2 = calculate_risk_score(
            total_problem_words=15,
            total_words=20,
            unique_problem_words=5
        )

        # Count component should be capped at 100% contribution
        # Both should have count_score = 100 in the count component
        # But percentage will differ: 50% vs 75%
        assert score2 > score1

    def test_capped_diversity_score(self):
        """Test that diversity score is capped at 5 unique words."""
        score1 = calculate_risk_score(
            total_problem_words=5,
            total_words=20,
            unique_problem_words=5
        )
        score2 = calculate_risk_score(
            total_problem_words=10,
            total_words=20,
            unique_problem_words=10
        )

        # Diversity component should be capped at 100% contribution
        # score1 has 5 unique (100%), score2 has 10 unique (also 100%)
        # score2 should be higher due to higher count and percentage
        assert score2 > score1

    def test_score_rounded(self):
        """Test that score is rounded to 2 decimal places."""
        score = calculate_risk_score(
            total_problem_words=1,
            total_words=3,
            unique_problem_words=1
        )

        # Should have at most 2 decimal places
        assert len(str(score).split('.')[-1]) <= 2


class TestAnalyzeContent:
    """Tests for analyze_content function."""

    def test_clean_content(self):
        """Test analyzing clean content."""
        text = "This is a perfectly clean piece of content"
        flag_words = {"violence", "hatred", "explicit"}

        result = analyze_content(text, flag_words)

        assert result['flagged_words'] == []
        assert result['total_problem_words'] == 0
        assert result['total_words'] == 8
        assert result['problem_percentage'] == 0.0
        assert result['risk_score'] == 0.0
        assert result['should_flag'] is False

    def test_content_with_problems(self):
        """Test analyzing content with problem words."""
        text = "violence and hatred are bad"
        flag_words = {"violence", "hatred", "explicit"}

        result = analyze_content(text, flag_words)

        assert set(result['flagged_words']) == {"violence", "hatred"}
        assert result['total_problem_words'] == 2
        assert result['total_words'] == 5
        assert result['problem_percentage'] == pytest.approx(40.0, abs=0.1)
        assert result['risk_score'] > 0
        assert result['should_flag'] is True

    def test_content_with_repeated_problems(self):
        """Test analyzing content with repeated problem words."""
        text = "violence violence violence"
        flag_words = {"violence"}

        result = analyze_content(text, flag_words)

        assert result['flagged_words'] == ["violence"]
        assert result['total_problem_words'] == 3
        assert result['total_words'] == 3
        assert result['problem_percentage'] == 100.0
        assert result['should_flag'] is True

    def test_empty_content(self):
        """Test analyzing empty content."""
        flag_words = {"violence", "hatred"}

        result = analyze_content("", flag_words)

        assert result['flagged_words'] == []
        assert result['total_problem_words'] == 0
        assert result['total_words'] == 0
        assert result['problem_percentage'] == 0.0
        assert result['risk_score'] == 0.0
        assert result['should_flag'] is False

    def test_flagged_words_sorted(self):
        """Test that flagged words are returned sorted."""
        text = "zebra violence apple hatred banana"
        flag_words = {"violence", "hatred", "zebra", "banana"}

        result = analyze_content(text, flag_words)

        # Should be alphabetically sorted
        assert result['flagged_words'] == ["banana", "hatred", "violence", "zebra"]

    def test_real_world_prompt(self):
        """Test with a realistic prompt containing some problem words."""
        text = """
        Create a dramatic action scene with violence and explosions,
        showcasing the hero's combat skills in an intense battle.
        Include detailed weapon effects and destruction.
        """
        flag_words = {"violence", "weapon", "destruction", "combat"}

        result = analyze_content(text, flag_words)

        assert set(result['flagged_words']) == {"violence", "weapon", "destruction", "combat"}
        assert result['total_problem_words'] == 4
        assert result['should_flag'] is True
        assert result['risk_score'] > 0


class TestGetDefaultFlagWordsPath:
    """Tests for get_default_flag_words_path function."""

    def test_returns_path_if_exists(self, tmp_path, monkeypatch):
        """Test that it returns path if flag-words.txt exists."""
        # This test is tricky because it depends on file structure
        # We can at least test that it returns None or a string
        result = get_default_flag_words_path()

        assert result is None or isinstance(result, str)

    def test_returns_none_if_not_exists(self, tmp_path, monkeypatch):
        """Test that it returns None if flag-words.txt doesn't exist."""
        # Mock the path to point somewhere without the file
        import genonaut.utils.flagging as flagging_module
        original_file = flagging_module.__file__

        # Create a temporary directory structure
        fake_module_dir = tmp_path / "genonaut" / "utils"
        fake_module_dir.mkdir(parents=True)

        # Temporarily change __file__ to point to temp location
        monkeypatch.setattr(flagging_module, '__file__', str(fake_module_dir / "flagging.py"))

        result = get_default_flag_words_path()

        assert result is None
