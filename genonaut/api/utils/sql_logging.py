"""SQL query logging utilities for performance debugging."""

import logging
from sqlalchemy import event
from sqlalchemy.engine import Engine
from typing import Optional

logger = logging.getLogger("genonaut.sql")

# Global flag to track if SQL logging is enabled
_sql_logging_enabled = False


def enable_sql_logging(engine: Optional[Engine] = None):
    """
    Enable SQL query logging.

    This will log all SQL queries executed through SQLAlchemy, including
    execution time. Useful for detecting N+1 queries and slow queries.

    Args:
        engine: Optional specific engine to enable logging for.
                If None, will apply to all engines.
    """
    global _sql_logging_enabled

    @event.listens_for(Engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        conn.info.setdefault('query_start_time', []).append(logger._log)
        import time
        conn.info.setdefault('query_start_time', []).append(time.perf_counter())

    @event.listens_for(Engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        import time
        total = time.perf_counter() - conn.info['query_start_time'].pop()

        # Only log if query took > 1ms
        if total > 0.001:
            logger.info(
                f"[SQL] {total*1000:.2f}ms - {statement[:200]}"
                + ("..." if len(statement) > 200 else "")
            )

    _sql_logging_enabled = True
    logger.info("SQL query logging enabled")


def disable_sql_logging():
    """Disable SQL query logging."""
    global _sql_logging_enabled

    # Remove event listeners
    event.remove(Engine, "before_cursor_execute", before_cursor_execute)
    event.remove(Engine, "after_cursor_execute", after_cursor_execute)

    _sql_logging_enabled = False
    logger.info("SQL query logging disabled")


def is_sql_logging_enabled() -> bool:
    """Check if SQL logging is currently enabled."""
    return _sql_logging_enabled
