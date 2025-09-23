"""Bulk insertion utilities with conflict handling."""

import logging
from typing import List, Dict, Any, Set, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text

from genonaut.db.schema import User, ContentItem, ContentItemAuto, GenerationJob


logger = logging.getLogger(__name__)


class BulkInserter:
    """Handles bulk insertion with conflict resolution."""

    def __init__(self, session: Session):
        self.session = session

    def insert_users_batch(self, users: List[Dict[str, Any]]) -> Tuple[int, List[str]]:
        """Insert users batch with username conflict handling."""
        if not users:
            return 0, []

        # Try bulk insert first
        try:
            self.session.bulk_insert_mappings(User, users)
            self.session.commit()
            return len(users), []
        except IntegrityError as e:
            self.session.rollback()

            # Handle username conflicts individually
            return self._insert_users_with_conflict_resolution(users)

    def _insert_users_with_conflict_resolution(self, users: List[Dict[str, Any]]) -> Tuple[int, List[str]]:
        """Insert users one by one, handling conflicts."""
        inserted_count = 0
        conflicted_usernames = []

        for user_data in users:
            try:
                user = User(**user_data)
                self.session.add(user)
                self.session.commit()
                inserted_count += 1
            except IntegrityError:
                self.session.rollback()
                conflicted_usernames.append(user_data['username'])
                logger.warning(f"Username conflict: {user_data['username']}")

        if conflicted_usernames:
            logger.warning(
                f"Removed {len(conflicted_usernames)} users due to username conflicts: "
                f"{', '.join(conflicted_usernames[:10])}"
                f"{'...' if len(conflicted_usernames) > 10 else ''}"
            )

        return inserted_count, conflicted_usernames

    def insert_content_items_batch(self, items: List[Dict[str, Any]], table_class) -> int:
        """Insert content items batch."""
        if not items:
            return 0

        try:
            self.session.bulk_insert_mappings(table_class, items)
            self.session.commit()
            return len(items)
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to insert content items batch: {e}")
            raise

    def insert_generation_jobs_batch(self, jobs: List[Dict[str, Any]]) -> int:
        """Insert generation jobs batch."""
        if not jobs:
            return 0

        try:
            self.session.bulk_insert_mappings(GenerationJob, jobs)
            self.session.commit()
            return len(jobs)
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to insert generation jobs batch: {e}")
            raise

    def get_user_ids(self) -> List[str]:
        """Get all user IDs for FK references."""
        result = self.session.execute(text("SELECT id FROM users"))
        return [str(row[0]) for row in result.fetchall()]

    def get_content_item_ids(self, table_name: str) -> List[int]:
        """Get all content item IDs for FK references."""
        result = self.session.execute(text(f"SELECT id FROM {table_name}"))
        return [row[0] for row in result.fetchall()]

    def update_generation_jobs_with_content_ids(self, content_table: str) -> int:
        """Update completed generation jobs with result_content_id."""
        # This updates jobs that were created for specific content items
        # We'll use a more sophisticated approach in the main generator
        query = text(f"""
            UPDATE generation_jobs
            SET result_content_id = (
                SELECT id FROM {content_table}
                WHERE {content_table}.creator_id = generation_jobs.user_id
                AND generation_jobs.status = 'completed'
                AND generation_jobs.result_content_id IS NULL
                LIMIT 1
            )
            WHERE generation_jobs.status = 'completed'
            AND generation_jobs.result_content_id IS NULL
        """)

        result = self.session.execute(query)
        self.session.commit()
        return result.rowcount

    def get_table_count(self, table_name: str) -> int:
        """Get current row count for a table."""
        result = self.session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        return result.scalar()

    def optimize_for_bulk_insert(self):
        """Optimize database settings for bulk insertion."""
        try:
            # These optimizations are PostgreSQL-specific
            self.session.execute(text("SET synchronous_commit = OFF"))
            self.session.execute(text("SET wal_buffers = '64MB'"))
            self.session.execute(text("SET checkpoint_segments = 64"))
            self.session.commit()
        except Exception as e:
            logger.warning(f"Could not apply bulk insert optimizations: {e}")
            self.session.rollback()

    def restore_normal_settings(self):
        """Restore normal database settings after bulk operations."""
        try:
            self.session.execute(text("SET synchronous_commit = ON"))
            self.session.commit()
        except Exception as e:
            logger.warning(f"Could not restore normal settings: {e}")
            self.session.rollback()


class ProgressReporter:
    """Reports progress during bulk operations."""

    def __init__(self, table_name: str, target_count: int):
        self.table_name = table_name
        self.target_count = target_count
        self.current_count = 0

    def update(self, batch_size: int):
        """Update progress and print status."""
        self.current_count += batch_size
        percent = min(100.0, (self.current_count / self.target_count) * 100)

        print(f"{self.table_name}: {self.current_count}/{self.target_count} ({percent:.1f}%)")

    def complete(self, final_count: int):
        """Mark completion with final count."""
        self.current_count = final_count
        percent = (final_count / self.target_count) * 100
        status = "✓" if final_count >= self.target_count else "⚠"

        print(f"{status} {self.table_name}: {final_count}/{self.target_count} ({percent:.1f}%)")


class StatisticsCollector:
    """Collects and reports final statistics."""

    def __init__(self):
        self.table_counts = {}
        self.total_time = 0
        self.conflicts = {}

    def record_table_count(self, table_name: str, count: int):
        """Record final count for a table."""
        self.table_counts[table_name] = count

    def record_conflicts(self, table_name: str, conflict_count: int, conflict_details: List[str] = None):
        """Record conflict information."""
        self.conflicts[table_name] = {
            'count': conflict_count,
            'details': conflict_details or []
        }

    def record_total_time(self, seconds: float):
        """Record total execution time."""
        self.total_time = seconds

    def print_final_report(self):
        """Print comprehensive final report."""
        print("\n" + "="*60)
        print("SYNTHETIC DATA GENERATION COMPLETE")
        print("="*60)

        print("\nTable Counts:")
        for table_name, count in self.table_counts.items():
            print(f"  {table_name}: {count:,} records")

        if self.conflicts:
            print("\nConflicts Resolved:")
            for table_name, conflict_info in self.conflicts.items():
                if conflict_info['count'] > 0:
                    print(f"  {table_name}: {conflict_info['count']} conflicts")

        print(f"\nTotal Execution Time: {self.total_time:.2f} seconds")

        total_records = sum(self.table_counts.values())
        if self.total_time > 0:
            rate = total_records / self.total_time
            print(f"Generation Rate: {rate:.0f} records/second")

        print("="*60)