"""Unit tests for statement timeout handling.

Tests that statement timeout errors are properly caught and converted to appropriate
HTTP responses. The API enforces PostgreSQL statement_timeout to prevent runaway queries.
"""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.exc import OperationalError
from psycopg2.errors import QueryCanceled


class MockStatementTimeoutHandler:
    """Mock handler to test statement timeout error handling logic."""

    @staticmethod
    def handle_database_error(error: Exception) -> dict:
        """Handle database errors and convert to API response format.

        Args:
            error: The database exception

        Returns:
            dict with 'status_code', 'error_type', 'message'
        """
        # Check if it's a statement timeout error
        if isinstance(error, OperationalError):
            # Check if the original exception is QueryCanceled
            if hasattr(error, 'orig') and isinstance(error.orig, QueryCanceled):
                return {
                    'status_code': 504,
                    'error_type': 'statement_timeout',
                    'message': 'Query exceeded maximum execution time',
                }

        # Generic database error
        return {
            'status_code': 500,
            'error_type': 'database_error',
            'message': 'An unexpected database error occurred',
        }


def test_statement_timeout_detection():
    """Test that statement timeout errors are correctly identified."""
    handler = MockStatementTimeoutHandler()

    # Create a mock QueryCanceled error
    query_canceled = QueryCanceled()

    # Wrap it in SQLAlchemy OperationalError
    op_error = OperationalError(
        statement="SELECT * FROM content_items WHERE...",
        params={},
        orig=query_canceled
    )

    result = handler.handle_database_error(op_error)

    assert result['status_code'] == 504
    assert result['error_type'] == 'statement_timeout'
    assert 'exceeded maximum execution time' in result['message'].lower()


def test_generic_operational_error():
    """Test that non-timeout OperationalErrors are handled differently."""
    handler = MockStatementTimeoutHandler()

    # Create OperationalError without QueryCanceled
    op_error = OperationalError(
        statement="SELECT * FROM content_items",
        params={},
        orig=Exception("Connection lost")
    )

    result = handler.handle_database_error(op_error)

    # Should be generic database error, not timeout
    assert result['status_code'] == 500
    assert result['error_type'] == 'database_error'


def test_non_operational_error():
    """Test that non-OperationalErrors are handled as generic errors."""
    handler = MockStatementTimeoutHandler()

    # Some other exception type
    other_error = ValueError("Invalid parameter")

    result = handler.handle_database_error(other_error)

    assert result['status_code'] == 500
    assert result['error_type'] == 'database_error'


def test_statement_timeout_response_format():
    """Test that timeout responses include all required fields."""
    handler = MockStatementTimeoutHandler()

    query_canceled = QueryCanceled()
    op_error = OperationalError(
        statement="SELECT * FROM content_items",
        params={},
        orig=query_canceled
    )

    result = handler.handle_database_error(op_error)

    # Verify all required fields present
    assert 'status_code' in result
    assert 'error_type' in result
    assert 'message' in result

    # Verify correct types
    assert isinstance(result['status_code'], int)
    assert isinstance(result['error_type'], str)
    assert isinstance(result['message'], str)

    # Verify HTTP 504 Gateway Timeout
    assert result['status_code'] == 504


def test_timeout_error_message_helpful():
    """Test that timeout error message is user-friendly."""
    handler = MockStatementTimeoutHandler()

    query_canceled = QueryCanceled()
    op_error = OperationalError(
        statement="SELECT * FROM content_items",
        params={},
        orig=query_canceled
    )

    result = handler.handle_database_error(op_error)

    message = result['message'].lower()

    # Should mention query or execution or timeout
    assert any(word in message for word in ['query', 'execution', 'timeout', 'time'])

    # Should be clear about what happened
    assert any(word in message for word in ['exceeded', 'maximum', 'limit'])


@pytest.mark.parametrize('timeout_seconds', [15, 30, 60])
def test_different_timeout_values(timeout_seconds):
    """Test that timeout handling works regardless of configured timeout value.

    Note: This test documents that the handler doesn't need to know the specific
    timeout value - it just detects that a timeout occurred.
    """
    handler = MockStatementTimeoutHandler()

    # Timeout detection is independent of the actual timeout value
    query_canceled = QueryCanceled()
    op_error = OperationalError(
        statement=f"SET statement_timeout = {timeout_seconds}000; SELECT ...",
        params={},
        orig=query_canceled
    )

    result = handler.handle_database_error(op_error)

    # Should always return timeout error
    assert result['error_type'] == 'statement_timeout'
    assert result['status_code'] == 504


def test_multiple_timeout_errors_independent():
    """Test that multiple timeout errors are handled independently."""
    handler = MockStatementTimeoutHandler()

    # Create two separate timeout errors
    error1 = OperationalError(
        statement="SELECT * FROM content_items WHERE...",
        params={},
        orig=QueryCanceled()
    )

    error2 = OperationalError(
        statement="SELECT * FROM recommendations WHERE...",
        params={},
        orig=QueryCanceled()
    )

    result1 = handler.handle_database_error(error1)
    result2 = handler.handle_database_error(error2)

    # Both should be handled as timeouts
    assert result1['error_type'] == 'statement_timeout'
    assert result2['error_type'] == 'statement_timeout'

    # Results should be independent (not sharing state)
    assert result1 == result2


def test_timeout_with_complex_query():
    """Test timeout detection works with complex query statements."""
    handler = MockStatementTimeoutHandler()

    # Simulate timeout on a complex query
    complex_query = """
        SELECT ci.*,
               array_agg(t.name) as tag_names,
               COUNT(*) OVER() as total_count
        FROM content_items ci
        LEFT JOIN content_item_tags cit ON ci.id = cit.content_item_id
        LEFT JOIN tags t ON cit.tag_id = t.id
        WHERE ci.user_id = %(user_id)s
        AND ci.created_at > %(start_date)s
        GROUP BY ci.id
        ORDER BY ci.created_at DESC
        LIMIT 100
    """

    error = OperationalError(
        statement=complex_query,
        params={'user_id': '123', 'start_date': '2024-01-01'},
        orig=QueryCanceled()
    )

    result = handler.handle_database_error(error)

    assert result['error_type'] == 'statement_timeout'


def test_timeout_with_none_orig():
    """Test graceful handling when OperationalError has None as orig."""
    handler = MockStatementTimeoutHandler()

    # Create OperationalError with None as orig
    error = OperationalError(
        statement="SELECT * FROM content_items",
        params={},
        orig=None
    )

    # Should not raise exception, should return generic error
    result = handler.handle_database_error(error)

    assert result['status_code'] == 500
    assert result['error_type'] == 'database_error'
