"""Unit tests for tag favorites duplicate handling."""
import pytest

class MockFavoritesService:
    def __init__(self):
        self.favorites = set()
    
    def add(self, user_id, tag_id) -> str:
        if tag_id in self.favorites:
            return "already_favorited"
        self.favorites.add(tag_id)
        return "added"
    
    def remove(self, user_id, tag_id) -> str:
        if tag_id not in self.favorites:
            return "not_found"
        self.favorites.remove(tag_id)
        return "removed"

def test_add_favorite_twice():
    service = MockFavoritesService()
    assert service.add('user1', 'tag1') == "added"
    assert service.add('user1', 'tag1') == "already_favorited"

def test_remove_nonexistent():
    service = MockFavoritesService()
    assert service.remove('user1', 'tag1') == "not_found"
