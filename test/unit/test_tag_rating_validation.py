"""Unit tests for tag rating validation."""
import pytest

class MockRatingValidator:
    @staticmethod
    def validate(rating: float) -> bool:
        return 1.0 <= rating <= 5.0

def test_valid_ratings():
    validator = MockRatingValidator()
    assert validator.validate(1.0) is True
    assert validator.validate(5.0) is True
    assert validator.validate(2.5) is True

def test_invalid_ratings():
    validator = MockRatingValidator()
    assert validator.validate(0) is False
    assert validator.validate(6) is False
    assert validator.validate(-1) is False
