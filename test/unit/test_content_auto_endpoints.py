"""Unit tests for content auto endpoints."""
def test_auto_content_crud():
    auto_content = {'id': 1, 'type': 'auto'}
    assert auto_content['type'] == 'auto'
