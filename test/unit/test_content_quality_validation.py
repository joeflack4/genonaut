"""Unit tests for content quality score validation."""
import pytest

class MockQualityValidator:
    @staticmethod
    def validate(score: float) -> bool:
        return 0.0 <= score <= 1.0

def test_valid_boundary_values():
    validator = MockQualityValidator()
    assert validator.validate(0.0) is True
    assert validator.validate(1.0) is True
    assert validator.validate(0.5) is True

def test_invalid_values():
    validator = MockQualityValidator()
    assert validator.validate(-0.1) is False
    assert validator.validate(1.1) is False
    assert validator.validate(2.0) is False
