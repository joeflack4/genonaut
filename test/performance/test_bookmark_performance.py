"""Performance tests for bookmark queries with JOINs to partitioned tables.

This script tests the performance of bookmark queries that JOIN with content_items_all
(a partitioned table) and user_interactions to provide content data and user ratings.
"""

import time
import statistics
from typing import List, Dict, Any
from sqlalchemy import text
from sqlalchemy.orm import Session

from genonaut.api.dependencies import get_database_session
from genonaut.api.config import get_settings


def time_query(db: Session, query_sql: str, params: Dict[str, Any] = None) -> float:
    """Execute a query and return execution time in milliseconds."""
    start = time.time()
    db.execute(text(query_sql), params or {})
    end = time.time()
    return (end - start) * 1000  # Convert to milliseconds


def get_explain_analyze(db: Session, query_sql: str, params: Dict[str, Any] = None) -> str:
    """Get EXPLAIN ANALYZE output for a query."""
    explain_sql = f"EXPLAIN ANALYZE {query_sql}"
    result = db.execute(text(explain_sql), params or {})
    return "\n".join([row[0] for row in result])


def test_bookmark_list_query_performance(db: Session, user_id: str) -> Dict[str, Any]:
    """Test performance of listing bookmarks with content JOINs."""

    # Query that matches repository implementation
    query = """
        SELECT b.*, c.*, ui.rating
        FROM bookmarks b
        LEFT OUTER JOIN content_items_all c
            ON b.content_id = c.id AND b.content_source_type = c.source_type
        LEFT OUTER JOIN user_interactions ui
            ON ui.user_id = :user_id AND ui.content_item_id = b.content_id
        WHERE b.user_id = :user_id AND b.deleted_at IS NULL
        ORDER BY ui.rating DESC NULLS LAST, b.created_at DESC
        LIMIT 100
    """

    params = {"user_id": user_id}

    # Run query multiple times to get average
    times = []
    for _ in range(5):
        exec_time = time_query(db, query, params)
        times.append(exec_time)

    # Get EXPLAIN ANALYZE
    explain = get_explain_analyze(db, query, params)

    return {
        "query_type": "list_bookmarks_with_content",
        "avg_time_ms": statistics.mean(times),
        "min_time_ms": min(times),
        "max_time_ms": max(times),
        "std_dev_ms": statistics.stdev(times) if len(times) > 1 else 0,
        "explain_analyze": explain
    }


def test_category_bookmarks_query_performance(db: Session, category_id: str, user_id: str) -> Dict[str, Any]:
    """Test performance of listing bookmarks in a category with content JOINs."""

    query = """
        SELECT b.*, c.*, ui.rating
        FROM bookmarks b
        JOIN bookmark_category_members bcm ON bcm.bookmark_id = b.id
        LEFT OUTER JOIN content_items_all c
            ON b.content_id = c.id AND b.content_source_type = c.source_type
        LEFT OUTER JOIN user_interactions ui
            ON ui.user_id = :user_id AND ui.content_item_id = b.content_id
        WHERE bcm.category_id = :category_id AND b.deleted_at IS NULL
        ORDER BY c.quality_score DESC
        LIMIT 100
    """

    params = {"category_id": category_id, "user_id": user_id}

    # Run query multiple times
    times = []
    for _ in range(5):
        exec_time = time_query(db, query, params)
        times.append(exec_time)

    # Get EXPLAIN ANALYZE
    explain = get_explain_analyze(db, query, params)

    return {
        "query_type": "category_bookmarks_with_content",
        "avg_time_ms": statistics.mean(times),
        "min_time_ms": min(times),
        "max_time_ms": max(times),
        "std_dev_ms": statistics.stdev(times) if len(times) > 1 else 0,
        "explain_analyze": explain
    }


def test_partitioned_table_join_performance(db: Session) -> Dict[str, Any]:
    """Test JOIN performance specifically for partitioned content_items_all table."""

    # Test JOIN with items partition
    items_query = """
        SELECT COUNT(*)
        FROM bookmarks b
        JOIN content_items_all c
            ON b.content_id = c.id AND b.content_source_type = c.source_type
        WHERE c.source_type = 'items'
    """

    # Test JOIN with auto partition
    auto_query = """
        SELECT COUNT(*)
        FROM bookmarks b
        JOIN content_items_all c
            ON b.content_id = c.id AND b.content_source_type = c.source_type
        WHERE c.source_type = 'auto'
    """

    items_times = [time_query(db, items_query) for _ in range(5)]
    auto_times = [time_query(db, auto_query) for _ in range(5)]

    items_explain = get_explain_analyze(db, items_query)
    auto_explain = get_explain_analyze(db, auto_query)

    return {
        "query_type": "partitioned_table_joins",
        "items_partition": {
            "avg_time_ms": statistics.mean(items_times),
            "min_time_ms": min(items_times),
            "max_time_ms": max(items_times),
            "explain_analyze": items_explain
        },
        "auto_partition": {
            "avg_time_ms": statistics.mean(auto_times),
            "min_time_ms": min(auto_times),
            "max_time_ms": max(auto_times),
            "explain_analyze": auto_explain
        }
    }


def count_test_data(db: Session) -> Dict[str, int]:
    """Count existing test data."""
    counts = {}

    # Count bookmarks
    result = db.execute(text("SELECT COUNT(*) FROM bookmarks WHERE deleted_at IS NULL"))
    counts["bookmarks"] = result.scalar()

    # Count categories
    result = db.execute(text("SELECT COUNT(*) FROM bookmark_categories"))
    counts["categories"] = result.scalar()

    # Count content items
    result = db.execute(text("SELECT COUNT(*) FROM content_items_all"))
    counts["content_items"] = result.scalar()

    # Count user interactions
    result = db.execute(text("SELECT COUNT(*) FROM user_interactions"))
    counts["user_interactions"] = result.scalar()

    return counts


def run_performance_tests():
    """Run all performance tests and print results."""
    settings = get_settings()

    print("=" * 80)
    print("BOOKMARK PERFORMANCE TESTS - Phase 5")
    print("=" * 80)
    print(f"\nEnvironment: {settings.env_target}")
    print()

    # Get database session
    db_gen = get_database_session()
    db = next(db_gen)

    try:
        # Count existing data
        print("\n" + "=" * 80)
        print("EXISTING DATA COUNTS")
        print("=" * 80)
        counts = count_test_data(db)
        for key, value in counts.items():
            print(f"{key}: {value:,}")

        if counts["bookmarks"] == 0:
            print("\nWARNING: No bookmarks found. Performance tests require existing data.")
            print("Consider running integration tests first to create test data.")
            return

        # Get a sample user_id with bookmarks
        result = db.execute(text("SELECT DISTINCT user_id FROM bookmarks WHERE deleted_at IS NULL LIMIT 1"))
        sample_user = result.scalar()

        if not sample_user:
            print("\nERROR: Could not find user with bookmarks.")
            return

        print(f"\nUsing sample user_id: {sample_user}")

        # Test 1: List bookmarks with content JOIN
        print("\n" + "=" * 80)
        print("TEST 1: List Bookmarks with Content JOIN")
        print("=" * 80)
        result1 = test_bookmark_list_query_performance(db, str(sample_user))
        print(f"Query Type: {result1['query_type']}")
        print(f"Average Time: {result1['avg_time_ms']:.2f}ms")
        print(f"Min Time: {result1['min_time_ms']:.2f}ms")
        print(f"Max Time: {result1['max_time_ms']:.2f}ms")
        print(f"Std Dev: {result1['std_dev_ms']:.2f}ms")
        print(f"\nEXPLAIN ANALYZE:\n{result1['explain_analyze']}")

        # Test 2: Category bookmarks (if categories exist)
        if counts["categories"] > 0:
            result = db.execute(text("""
                SELECT DISTINCT bcm.category_id
                FROM bookmark_category_members bcm
                LIMIT 1
            """))
            sample_category = result.scalar()

            if sample_category:
                print("\n" + "=" * 80)
                print("TEST 2: Category Bookmarks with Content JOIN")
                print("=" * 80)
                result2 = test_category_bookmarks_query_performance(db, str(sample_category), str(sample_user))
                print(f"Query Type: {result2['query_type']}")
                print(f"Average Time: {result2['avg_time_ms']:.2f}ms")
                print(f"Min Time: {result2['min_time_ms']:.2f}ms")
                print(f"Max Time: {result2['max_time_ms']:.2f}ms")
                print(f"Std Dev: {result2['std_dev_ms']:.2f}ms")
                print(f"\nEXPLAIN ANALYZE:\n{result2['explain_analyze']}")

        # Test 3: Partitioned table JOIN performance
        print("\n" + "=" * 80)
        print("TEST 3: Partitioned Table JOIN Performance")
        print("=" * 80)
        result3 = test_partitioned_table_join_performance(db)
        print(f"\nITEMS Partition:")
        print(f"Average Time: {result3['items_partition']['avg_time_ms']:.2f}ms")
        print(f"Min Time: {result3['items_partition']['min_time_ms']:.2f}ms")
        print(f"Max Time: {result3['items_partition']['max_time_ms']:.2f}ms")
        print(f"\nEXPLAIN ANALYZE (items):\n{result3['items_partition']['explain_analyze']}")

        print(f"\nAUTO Partition:")
        print(f"Average Time: {result3['auto_partition']['avg_time_ms']:.2f}ms")
        print(f"Min Time: {result3['auto_partition']['min_time_ms']:.2f}ms")
        print(f"Max Time: {result3['auto_partition']['max_time_ms']:.2f}ms")
        print(f"\nEXPLAIN ANALYZE (auto):\n{result3['auto_partition']['explain_analyze']}")

        # Summary
        print("\n" + "=" * 80)
        print("PERFORMANCE SUMMARY")
        print("=" * 80)
        print(f"✓ All queries completed successfully")
        print(f"✓ Bookmark list query: {result1['avg_time_ms']:.2f}ms avg")
        if counts["categories"] > 0 and 'result2' in locals():
            print(f"✓ Category bookmarks query: {result2['avg_time_ms']:.2f}ms avg")
        print(f"✓ Items partition JOIN: {result3['items_partition']['avg_time_ms']:.2f}ms avg")
        print(f"✓ Auto partition JOIN: {result3['auto_partition']['avg_time_ms']:.2f}ms avg")

        # Performance assessment
        max_time = max([result1['avg_time_ms'], result3['items_partition']['avg_time_ms'], result3['auto_partition']['avg_time_ms']])
        if max_time < 100:
            print(f"\n✓ EXCELLENT: All queries under 100ms")
        elif max_time < 200:
            print(f"\n✓ GOOD: All queries under 200ms")
        else:
            print(f"\n⚠ WARNING: Some queries over 200ms - consider optimization")

    finally:
        db.close()


if __name__ == "__main__":
    run_performance_tests()
