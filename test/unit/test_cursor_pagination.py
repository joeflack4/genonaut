"""Unit tests for cursor pagination utilities."""

import pytest
from datetime import datetime, timezone
from genonaut.api.utils.cursor_pagination import (
    encode_cursor,
    decode_cursor,
    validate_cursor,
    create_next_cursor,
    create_prev_cursor,
    CursorError
)


class TestCursorEncoding:
    """Test cursor encoding functionality."""

    def test_encode_cursor_basic(self):
        """Test basic cursor encoding."""
        ts = datetime(2025, 1, 15, 12, 30, 45, tzinfo=timezone.utc)
        cursor = encode_cursor(ts, 123, "items")

        assert cursor is not None
        assert isinstance(cursor, str)
        assert len(cursor) > 0

    def test_encode_cursor_with_auto_source(self):
        """Test cursor encoding with auto source type."""
        ts = datetime(2025, 1, 15, 12, 30, 45, tzinfo=timezone.utc)
        cursor = encode_cursor(ts, 456, "auto")

        assert cursor is not None
        assert isinstance(cursor, str)

    def test_encode_cursor_deterministic(self):
        """Test that same inputs produce same cursor."""
        ts = datetime(2025, 1, 15, 12, 30, 45, tzinfo=timezone.utc)
        cursor1 = encode_cursor(ts, 789, "items")
        cursor2 = encode_cursor(ts, 789, "items")

        assert cursor1 == cursor2

    def test_encode_cursor_different_for_different_inputs(self):
        """Test that different inputs produce different cursors."""
        ts1 = datetime(2025, 1, 15, 12, 30, 45, tzinfo=timezone.utc)
        ts2 = datetime(2025, 1, 15, 12, 30, 46, tzinfo=timezone.utc)

        cursor1 = encode_cursor(ts1, 100, "items")
        cursor2 = encode_cursor(ts2, 100, "items")
        cursor3 = encode_cursor(ts1, 101, "items")
        cursor4 = encode_cursor(ts1, 100, "auto")

        assert cursor1 != cursor2
        assert cursor1 != cursor3
        assert cursor1 != cursor4


class TestCursorDecoding:
    """Test cursor decoding functionality."""

    def test_decode_cursor_basic(self):
        """Test basic cursor decoding."""
        ts = datetime(2025, 1, 15, 12, 30, 45, tzinfo=timezone.utc)
        cursor = encode_cursor(ts, 123, "items")

        decoded_ts, decoded_id, decoded_src = decode_cursor(cursor)

        assert decoded_ts == ts
        assert decoded_id == 123
        assert decoded_src == "items"

    def test_decode_cursor_roundtrip(self):
        """Test encoding and decoding roundtrip."""
        original_ts = datetime(2025, 1, 15, 12, 30, 45, 123456, tzinfo=timezone.utc)
        original_id = 999
        original_src = "auto"

        cursor = encode_cursor(original_ts, original_id, original_src)
        decoded_ts, decoded_id, decoded_src = decode_cursor(cursor)

        assert decoded_ts == original_ts
        assert decoded_id == original_id
        assert decoded_src == original_src

    def test_decode_cursor_empty_string_raises_error(self):
        """Test that empty cursor raises error."""
        with pytest.raises(CursorError, match="Cursor cannot be empty"):
            decode_cursor("")

    def test_decode_cursor_whitespace_raises_error(self):
        """Test that whitespace-only cursor raises error."""
        with pytest.raises(CursorError, match="Cursor cannot be empty"):
            decode_cursor("   ")

    def test_decode_cursor_invalid_base64_raises_error(self):
        """Test that invalid base64 raises error."""
        with pytest.raises(CursorError):
            decode_cursor("not_valid_base64!@#$%")

    def test_decode_cursor_invalid_json_raises_error(self):
        """Test that invalid JSON raises error."""
        import base64
        invalid_json = base64.urlsafe_b64encode(b"not valid json").decode('utf-8')
        with pytest.raises(CursorError, match="Invalid JSON"):
            decode_cursor(invalid_json)

    def test_decode_cursor_missing_fields_raises_error(self):
        """Test that cursor missing required fields raises error."""
        import base64
        import json

        # Missing 'id' field
        incomplete_data = json.dumps({"ts": "2025-01-15T12:30:45+00:00", "src": "items"})
        incomplete_cursor = base64.urlsafe_b64encode(incomplete_data.encode('utf-8')).decode('utf-8')

        with pytest.raises(CursorError, match="missing required fields"):
            decode_cursor(incomplete_cursor)

    def test_decode_cursor_invalid_source_type_raises_error(self):
        """Test that invalid source type raises error."""
        import base64
        import json

        invalid_data = json.dumps({
            "ts": "2025-01-15T12:30:45+00:00",
            "id": 123,
            "src": "invalid_source"
        })
        invalid_cursor = base64.urlsafe_b64encode(invalid_data.encode('utf-8')).decode('utf-8')

        with pytest.raises(CursorError, match="Invalid source_type"):
            decode_cursor(invalid_cursor)


class TestCursorValidation:
    """Test cursor validation functionality."""

    def test_validate_cursor_valid(self):
        """Test validation of valid cursor."""
        ts = datetime(2025, 1, 15, 12, 30, 45, tzinfo=timezone.utc)
        cursor = encode_cursor(ts, 123, "items")

        assert validate_cursor(cursor) is True

    def test_validate_cursor_none(self):
        """Test validation of None cursor (valid - means first page)."""
        assert validate_cursor(None) is True

    def test_validate_cursor_empty_string(self):
        """Test validation of empty string cursor (valid - means first page)."""
        assert validate_cursor("") is True

    def test_validate_cursor_invalid(self):
        """Test validation of invalid cursor."""
        assert validate_cursor("invalid_cursor") is False

    def test_validate_cursor_malformed(self):
        """Test validation of malformed cursor."""
        import base64
        malformed = base64.urlsafe_b64encode(b"not json").decode('utf-8')
        assert validate_cursor(malformed) is False


class TestCreateNextCursor:
    """Test next cursor creation from items."""

    def test_create_next_cursor_from_dicts(self):
        """Test creating next cursor from dictionary items."""
        items = [
            {"id": 1, "created_at": "2025-01-15T12:00:00+00:00", "source_type": "items"},
            {"id": 2, "created_at": "2025-01-15T12:01:00+00:00", "source_type": "items"},
            {"id": 3, "created_at": "2025-01-15T12:02:00+00:00", "source_type": "items"},
        ]

        cursor = create_next_cursor(items)

        assert cursor is not None
        decoded_ts, decoded_id, decoded_src = decode_cursor(cursor)
        assert decoded_id == 3
        assert decoded_src == "items"

    def test_create_next_cursor_empty_list(self):
        """Test creating next cursor from empty list returns None."""
        cursor = create_next_cursor([])
        assert cursor is None

    def test_create_next_cursor_with_datetime_objects(self):
        """Test creating cursor with datetime objects (not strings)."""
        items = [
            {
                "id": 100,
                "created_at": datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
                "source_type": "auto"
            }
        ]

        cursor = create_next_cursor(items)

        assert cursor is not None
        decoded_ts, decoded_id, decoded_src = decode_cursor(cursor)
        assert decoded_id == 100
        assert decoded_src == "auto"


class TestCreatePrevCursor:
    """Test previous cursor creation from items."""

    def test_create_prev_cursor_from_dicts(self):
        """Test creating previous cursor from dictionary items."""
        items = [
            {"id": 1, "created_at": "2025-01-15T12:00:00+00:00", "source_type": "items"},
            {"id": 2, "created_at": "2025-01-15T12:01:00+00:00", "source_type": "items"},
            {"id": 3, "created_at": "2025-01-15T12:02:00+00:00", "source_type": "items"},
        ]

        cursor = create_prev_cursor(items)

        assert cursor is not None
        decoded_ts, decoded_id, decoded_src = decode_cursor(cursor)
        assert decoded_id == 1
        assert decoded_src == "items"

    def test_create_prev_cursor_empty_list(self):
        """Test creating previous cursor from empty list returns None."""
        cursor = create_prev_cursor([])
        assert cursor is None

    def test_create_prev_cursor_with_datetime_objects(self):
        """Test creating previous cursor with datetime objects (not strings)."""
        items = [
            {
                "id": 50,
                "created_at": datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
                "source_type": "auto"
            }
        ]

        cursor = create_prev_cursor(items)

        assert cursor is not None
        decoded_ts, decoded_id, decoded_src = decode_cursor(cursor)
        assert decoded_id == 50
        assert decoded_src == "auto"
