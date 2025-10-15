"""Unit tests for user preferences update."""
import pytest

class MockPreferencesService:
    VALID_KEYS = {'theme', 'language', 'notifications'}
    
    def update(self, user_id, preferences: dict) -> bool:
        for key in preferences.keys():
            if key not in self.VALID_KEYS:
                raise ValueError(f"Invalid preference key: {key}")
        return True

def test_valid_preferences():
    service = MockPreferencesService()
    assert service.update('user1', {'theme': 'dark'}) is True

def test_invalid_preference_keys():
    service = MockPreferencesService()
    with pytest.raises(ValueError):
        service.update('user1', {'invalid_key': 'value'})
