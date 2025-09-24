"""Main data generation orchestrator."""

import logging
import time
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from genonaut.db.schema import User, ContentItem, ContentItemAuto, GenerationJob
from .config import SeedDataConfig, ConfigManager
from .generators import UserGenerator, ContentGenerator, GenerationJobGenerator
from .bulk_inserter import BulkInserter, ProgressReporter, StatisticsCollector


logger = logging.getLogger(__name__)


class SyntheticDataGenerator:
    """Main orchestrator for synthetic data generation."""

    def __init__(self, session: Session, config: SeedDataConfig, admin_uuid: str):
        self.session = session
        self.config = config
        self.admin_uuid = admin_uuid
        self.bulk_inserter = BulkInserter(session)
        self.stats = StatisticsCollector()
        # Store engine for session recreation after PostgreSQL restart
        self.engine = session.bind

    def generate_all_data(self):
        """Generate all synthetic data following FK dependencies."""
        start_time = time.time()

        try:
            logger.info("Starting synthetic data generation")
            print("Starting synthetic data generation...")

            # Check if we should pause for PostgreSQL restart on large datasets
            total_content_items = self.config.target_rows_content_items + self.config.target_rows_content_items_auto
            should_pause = total_content_items > 400000 and not self.config.use_unmodified_wal_buffers

            # Optimize database for bulk operations (skip if using unmodified wal_buffers)
            if not self.config.use_unmodified_wal_buffers:
                self.bulk_inserter.optimize_for_bulk_insert(should_pause_for_restart=should_pause)

            # Step 1: Generate Users (no dependencies)
            user_ids = self._generate_users()

            # Step 2: Generate Content Items (depend on users)
            content_items_data, content_items_auto_data = self._generate_content_items(user_ids)

            # Step 3: Generate Generation Jobs (depend on content items)
            self._generate_generation_jobs(user_ids, content_items_data, content_items_auto_data)

            # Restore normal database settings (skip if using unmodified wal_buffers)
            if not self.config.use_unmodified_wal_buffers:
                self.bulk_inserter.restore_normal_settings()

            # Record final statistics
            elapsed_time = time.time() - start_time
            self._collect_final_statistics(elapsed_time)
            self.stats.print_final_report()

            # Print final warning about PostgreSQL restart (skip if using unmodified wal_buffers)
            if not self.config.use_unmodified_wal_buffers:
                self._print_final_postgresql_warning()

            logger.info(f"Data generation completed in {elapsed_time:.2f} seconds")

        except Exception as e:
            # Always try to restore normal database settings on failure (skip if using unmodified wal_buffers)
            if not self.config.use_unmodified_wal_buffers:
                try:
                    self.bulk_inserter.restore_normal_settings()
                except Exception as restore_error:
                    logger.error(f"Failed to restore database settings after error: {restore_error}")

            elapsed_time = time.time() - start_time
            logger.error(f"Data generation failed after {elapsed_time:.2f} seconds: {e}")
            self._collect_partial_statistics(elapsed_time)
            self.stats.print_final_report()
            raise

    def _generate_users(self) -> List[str]:
        """Generate users table."""
        print("\nGenerating record sets 1 of 3: Users...")

        target_count = self.config.target_rows_users
        # OLD: batch_size = self.config.batch_size_users
        # NEW: Use unified batch size, but don't exceed target count
        batch_size = min(self.config.batch_size, target_count)
        progress = ProgressReporter("users", target_count)

        user_generator = UserGenerator(self.config.model_dump(), self.admin_uuid)
        generated_count = 0
        total_conflicts = 0
        all_conflicts = []

        # Track all usernames generated across all batches to prevent cross-batch conflicts
        all_generated_usernames = set()

        while generated_count < target_count:
            current_batch_size = min(batch_size, target_count - generated_count)
            users_batch = user_generator.generate_batch(current_batch_size)

            # Deduplicate batch to remove usernames already generated in previous batches
            # original_batch_size = len(users_batch)
            users_batch = [
                user for user in users_batch
                if user['username'] not in all_generated_usernames
            ]

            # Log deduplication if any occurred
            # deduped_count = original_batch_size - len(users_batch)
            # if deduped_count > 0:
            #     logger.info(f"Removed {deduped_count} users from batch due to cross-batch username conflicts")

            # Add usernames from current batch to global tracking set
            for user in users_batch:
                all_generated_usernames.add(user['username'])

            # Skip insertion if batch is empty after deduplication
            if not users_batch:
                continue

            inserted_count, conflicts = self.bulk_inserter.insert_users_batch(users_batch)
            generated_count += inserted_count
            total_conflicts += len(conflicts)
            all_conflicts.extend(conflicts)

            progress.update(inserted_count)

        progress.complete(generated_count)
        self.stats.record_conflicts("users", total_conflicts, all_conflicts)

        # Get all user IDs for FK references
        user_ids = self.bulk_inserter.get_user_ids()
        logger.info(f"Generated {generated_count} users with {total_conflicts} conflicts resolved")

        return user_ids

    def _generate_content_items(self, user_ids: List[str]) -> tuple:
        """Generate content items and content items auto."""
        print("\nGenerating record sets 2 of 3: Content Items...")

        # Generate content_items
        content_items_data = self._generate_content_table(
            user_ids, "content_items", ContentItem,
            self.config.target_rows_content_items,
            # OLD: self.config.batch_size_content_items
            # NEW: Use unified batch size, but don't exceed target count
            min(self.config.batch_size, self.config.target_rows_content_items)
        )

        # Generate content_items_auto
        content_items_auto_data = self._generate_content_table(
            user_ids, "content_items_auto", ContentItemAuto,
            self.config.target_rows_content_items_auto,
            # OLD: self.config.batch_size_content_items_auto
            # NEW: Use unified batch size, but don't exceed target count
            min(self.config.batch_size, self.config.target_rows_content_items_auto)
        )

        return content_items_data, content_items_auto_data

    def _generate_content_table(
        self,
        user_ids: List[str],
        table_name: str,
        table_class,
        target_count: int,
        batch_size: int
    ) -> List[Dict[str, Any]]:
        """Generate a single content table."""
        print(f"\n   Generating {table_name}...")

        progress = ProgressReporter(table_name, target_count)
        content_generator = ContentGenerator(
            self.config.model_dump(), user_ids, self.admin_uuid, table_name
        )

        generated_count = 0
        all_content_data = []

        while generated_count < target_count:
            current_batch_size = min(batch_size, target_count - generated_count)
            content_batch = content_generator.generate_batch(current_batch_size)

            # Store data for generation jobs
            all_content_data.extend(content_batch)

            inserted_count = self.bulk_inserter.insert_content_items_batch(content_batch, table_class)
            generated_count += inserted_count

            progress.update(inserted_count)

        progress.complete(generated_count)
        logger.info(f"Generated {generated_count} {table_name}")

        return all_content_data

    def _generate_generation_jobs(
        self,
        user_ids: List[str],
        content_items_data: List[Dict[str, Any]],
        content_items_auto_data: List[Dict[str, Any]]
    ):
        """Generate generation jobs."""
        print("\nGenerating record sets 3 of 3: Generation Jobs...")

        # Combine all content data
        all_content_data = content_items_data + content_items_auto_data

        # First, create completed jobs for each content item
        completed_jobs_count = self._generate_completed_jobs(all_content_data)

        # Then, create additional jobs with varied statuses to meet distribution requirements
        additional_jobs_count = self._generate_additional_jobs(user_ids, completed_jobs_count)

        total_jobs = completed_jobs_count + additional_jobs_count
        logger.info(f"Generated {total_jobs} total generation jobs ({completed_jobs_count} completed, "
                    f"{additional_jobs_count} additional)")

        # Update content references in completed jobs
        self._update_job_content_references()

    def _generate_completed_jobs(self, content_data: List[Dict[str, Any]]) -> int:
        """Generate completed jobs for all content items."""
        print("   Creating completed jobs for all content items...")

        # OLD: batch_size = self.config.batch_size_generation_jobs
        # NEW: Use unified batch size, but don't exceed total_content
        total_content = len(content_data)
        batch_size = min(self.config.batch_size, total_content)
        progress = ProgressReporter("completed generation_jobs", total_content)

        job_generator = GenerationJobGenerator(self.config.model_dump(), content_data)
        generated_count = 0

        while generated_count < total_content:
            current_batch_size = min(batch_size, total_content - generated_count)
            jobs_batch = job_generator.generate_completed_jobs_batch(current_batch_size)

            inserted_count = self.bulk_inserter.insert_generation_jobs_batch(jobs_batch)
            generated_count += inserted_count

            progress.update(inserted_count)

        progress.complete(generated_count)
        return generated_count

    def _generate_additional_jobs(self, user_ids: List[str], completed_count: int) -> int:
        """Generate additional jobs to achieve proper status distribution."""
        # Calculate how many additional jobs we need
        # If completed_count represents 98% of total, then total = completed_count / 0.98
        total_needed = int(completed_count / 0.98)
        additional_needed = max(0, total_needed - completed_count)

        if additional_needed == 0:
            return 0

        print(f"   Creating {additional_needed} additional jobs for status distribution...")

        # OLD: batch_size = self.config.batch_size_generation_jobs
        # NEW: Use unified batch size, but don't exceed additional_needed
        batch_size = min(self.config.batch_size, additional_needed)
        progress = ProgressReporter("additional generation_jobs", additional_needed)

        job_generator = GenerationJobGenerator(self.config.model_dump(), [])
        generated_count = 0

        while generated_count < additional_needed:
            current_batch_size = min(batch_size, additional_needed - generated_count)
            jobs_batch = job_generator.generate_additional_jobs_batch(current_batch_size, user_ids)

            inserted_count = self.bulk_inserter.insert_generation_jobs_batch(jobs_batch)
            generated_count += inserted_count

            progress.update(inserted_count)

        progress.complete(generated_count)
        return generated_count

    def _update_job_content_references(self):
        """Update generation jobs with content item references."""
        # todo: does this print before it takes a while, or after?
        #  Observed this line showing up in the logs and then 'Linking jobs to content items' showed up ~2 minutes
        #  later. But that was before I change it from `print` to `logger.info()`.:
        #  logger.info(f"Generated {total_jobs} total generation jobs ... )
        logger.info("   Linking jobs to content items (this can take a while)...")

        # Update for content_items
        content_updates = self.bulk_inserter.update_generation_jobs_with_content_ids("content_items")
        logger.info(f"Updated {content_updates} jobs with content_items references")

        # Update for content_items_auto
        auto_updates = self.bulk_inserter.update_generation_jobs_with_content_ids("content_items_auto")
        logger.info(f"Updated {auto_updates} jobs with content_items_auto references")

    def _collect_final_statistics(self, elapsed_time: float):
        """Collect final statistics for all tables."""
        tables = ["users", "content_items", "content_items_auto", "generation_jobs"]

        for table_name in tables:
            count = self.bulk_inserter.get_table_count(table_name)
            self.stats.record_table_count(table_name, count)

        self.stats.record_total_time(elapsed_time)

    def _collect_partial_statistics(self, elapsed_time: float):
        """Collect partial statistics when generation fails."""
        try:
            self._collect_final_statistics(elapsed_time)
        except Exception as e:
            logger.error(f"Failed to collect partial statistics: {e}")
            self.stats.record_total_time(elapsed_time)


    def _print_final_postgresql_warning(self):
        """Print final warning about PostgreSQL restart requirement."""
        print("\n" + "!"*80)
        print("WARNING!!!: Final operation needed: Please restart PostgreSQL to return")
        print("Write-Ahead Logging (WAL) buffers back to their original state")
        print("!"*80)
        print("")
        print("After restarting PostgreSQL, you may want to verify that wal_buffers")
        print("has been reset to the correct value. If not, run:")
        print("  make db-wal-buffers-reset")
        print("")
        print("You can check the current value with:")
        print("  SHOW wal_buffers;  -- (in PostgreSQL)")
        print("!"*80)
