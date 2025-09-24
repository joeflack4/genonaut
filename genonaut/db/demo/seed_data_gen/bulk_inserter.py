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
        self.original_wal_buffers = None
        self.wal_buffers_changed = False
        # Store engine for potential session recreation
        self.engine = session.bind

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
                # logger.warning(f"Username conflict: {user_data['username']}")

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

    def optimize_for_bulk_insert(self, should_pause_for_restart=False):
        """Optimize database settings for bulk insertion."""
        try:
            # First, capture current wal_buffers value
            result = self.session.execute(text("SHOW wal_buffers"))
            self.original_wal_buffers = result.scalar()
            logger.info(f"Current wal_buffers: {self.original_wal_buffers}")

            # Apply session-level optimizations (these work without restart)
            self.session.execute(text("SET synchronous_commit = OFF"))

            # Note: checkpoint_segments was replaced by max_wal_size in PostgreSQL 9.5+
            # Try both for compatibility
            try:
                self.session.execute(text("SET max_wal_size = '2GB'"))
            except:
                try:
                    self.session.execute(text("SET checkpoint_segments = 64"))
                except:
                    pass  # Skip if neither works

            self.session.commit()

            # Apply system-level wal_buffers optimization using autocommit connection
            # This must be done outside of a transaction block
            self._alter_system_wal_buffers('64MB')

            # Conditional pause for PostgreSQL restart on large datasets
            # Session recreation happens automatically within the pause method
            if should_pause_for_restart:
                self._pause_for_postgresql_restart()

            logger.info("Bulk insert optimizations applied successfully")

        except Exception as e:
            logger.warning(f"Could not apply bulk insert optimizations: {e}")
            self.session.rollback()

    def _pause_for_postgresql_restart(self):
        """Pause execution and prompt user to restart PostgreSQL for optimal performance."""
        print("\n" + "="*80)
        print("POSTGRESQL RESTART REQUIRED FOR OPTIMAL PERFORMANCE")
        print("="*80)
        print("For large datasets, PostgreSQL should be restarted to apply the new wal_buffers setting.")
        print("This will significantly improve bulk insertion performance.")
        print("")
        print("Please:")
        print("1. Restart your PostgreSQL server now")
        print("2. Press any key to continue once PostgreSQL has restarted")
        print("="*80)

        try:
            input("Press any key to continue...")
            print("Continuing with data generation...")
            print("="*80)

            # Recreate session immediately after PostgreSQL restart
            self._recreate_session_after_restart()

        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            raise

    def _recreate_session_after_restart(self):
        """Recreate database session after PostgreSQL restart."""
        import time
        max_retries = 5
        retry_delay = 2  # seconds

        for attempt in range(max_retries):
            try:
                logger.info(f"Recreating database session after PostgreSQL restart (attempt {attempt + 1}/{max_retries})...")

                # Close the old session and dispose the old engine
                self.session.close()
                old_url = str(self.engine.url)
                self.engine.dispose()

                # Small delay to let PostgreSQL fully initialize
                if attempt > 0:
                    logger.info(f"Waiting {retry_delay} seconds before retry...")
                    time.sleep(retry_delay)

                # Create completely new engine and session (don't reuse old engine)
                from sqlalchemy import create_engine
                from sqlalchemy.orm import sessionmaker

                logger.info("Creating fresh engine and session...")
                self.engine = create_engine(old_url, echo=False)
                session_factory = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
                self.session = session_factory()

                # Test connection health before proceeding
                logger.info("Testing connection health after session recreation...")
                self._test_connection_health()

                logger.info("Database session successfully recreated with fresh engine and tested")
                return  # Success, exit retry loop

            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed to recreate database session: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"All {max_retries} attempts failed to recreate database session")
                    raise
                else:
                    retry_delay *= 2  # Exponential backoff

    def _test_connection_health(self):
        """Test that the database connection is working properly."""
        try:
            # Simple connectivity test
            result = self.session.execute(text("SELECT 1 as test"))
            test_value = result.scalar()

            if test_value != 1:
                raise Exception("Connection health test failed - unexpected result")

            # Additional warmup queries to ensure connection is stable
            logger.info("Running connection warmup queries...")

            # Test current database
            result = self.session.execute(text("SELECT current_database()"))
            db_name = result.scalar()
            logger.info(f"Connected to database: {db_name}")

            # Test current user
            result = self.session.execute(text("SELECT current_user"))
            username = result.scalar()
            logger.info(f"Connected as user: {username}")

            # Test basic table query (if users table exists)
            try:
                result = self.session.execute(text("SELECT COUNT(*) FROM users"))
                user_count = result.scalar()
                logger.info(f"Users table accessible with {user_count} records")
            except:
                logger.info("Users table not accessible yet (expected for fresh database)")

            logger.info("Connection health test and warmup completed successfully")

        except Exception as e:
            logger.error(f"Connection health test failed: {e}")
            raise

    def _alter_system_wal_buffers(self, value: str):
        """Execute ALTER SYSTEM for wal_buffers using autocommit connection."""
        try:
            # Create a new connection with autocommit for ALTER SYSTEM
            engine = self.session.bind
            with engine.connect() as conn:
                # Set autocommit mode
                conn.execute(text("COMMIT"))  # End any existing transaction
                conn.connection.autocommit = True

                logger.info(f"Setting wal_buffers to {value} using ALTER SYSTEM...")
                conn.execute(text(f"ALTER SYSTEM SET wal_buffers = '{value}'"))
                self.wal_buffers_changed = True

                # Restore normal transaction mode
                conn.connection.autocommit = False

            # Log important information about the restart requirement
            logger.warning("wal_buffers has been changed via ALTER SYSTEM. The new setting will take effect after the next PostgreSQL restart.")
            logger.warning("For optimal performance, consider restarting PostgreSQL now and re-running the seed data generation.")

        except Exception as e:
            logger.error(f"Failed to execute ALTER SYSTEM for wal_buffers: {e}")
            raise

    def restore_normal_settings(self):
        """Restore normal database settings after bulk operations."""
        try:
            # Restore session-level settings using autocommit connection
            # This avoids issues with failed transaction states
            self._restore_session_settings()

            # Restore system-level wal_buffers if we changed it
            if self.wal_buffers_changed and self.original_wal_buffers:
                self._alter_system_wal_buffers(self.original_wal_buffers)
                self.wal_buffers_changed = False
                logger.info(f"wal_buffers restored to original value: {self.original_wal_buffers}")
                logger.warning("wal_buffers has been restored via ALTER SYSTEM. The restored setting will take effect after the next PostgreSQL restart.")

            logger.info("Normal database settings restored successfully")

        except Exception as e:
            logger.warning(f"Could not restore normal settings: {e}")

    def _restore_session_settings(self):
        """Restore session-level settings using autocommit connection."""
        try:
            # Use autocommit connection to avoid transaction block issues
            engine = self.session.bind
            with engine.connect() as conn:
                # Set autocommit mode
                conn.execute(text("COMMIT"))  # End any existing transaction
                conn.connection.autocommit = True

                logger.info("Restoring synchronous_commit to ON...")
                conn.execute(text("SET synchronous_commit = ON"))

                # Restore normal transaction mode
                conn.connection.autocommit = False

        except Exception as e:
            logger.error(f"Failed to restore session settings: {e}")
            raise


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