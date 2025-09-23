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

    def generate_all_data(self):
        """Generate all synthetic data following FK dependencies."""
        start_time = time.time()

        try:
            logger.info("Starting synthetic data generation")
            print("Starting synthetic data generation...")

            # Optimize database for bulk operations
            self.bulk_inserter.optimize_for_bulk_insert()

            # Step 1: Generate Users (no dependencies)
            user_ids = self._generate_users()

            # Step 2: Generate Content Items (depend on users)
            content_items_data, content_items_auto_data = self._generate_content_items(user_ids)

            # Step 3: Generate Generation Jobs (depend on content items)
            self._generate_generation_jobs(user_ids, content_items_data, content_items_auto_data)

            # Restore normal database settings
            self.bulk_inserter.restore_normal_settings()

            # Record final statistics
            elapsed_time = time.time() - start_time
            self._collect_final_statistics(elapsed_time)
            self.stats.print_final_report()

            logger.info(f"Data generation completed in {elapsed_time:.2f} seconds")

        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"Data generation failed after {elapsed_time:.2f} seconds: {e}")
            self._collect_partial_statistics(elapsed_time)
            self.stats.print_final_report()
            raise

    def _generate_users(self) -> List[str]:
        """Generate users table."""
        print("\n1. Generating Users...")

        target_count = self.config.target_rows_users
        batch_size = self.config.batch_size_users
        progress = ProgressReporter("users", target_count)

        user_generator = UserGenerator(self.config.dict(), self.admin_uuid)
        generated_count = 0
        total_conflicts = 0
        all_conflicts = []

        while generated_count < target_count:
            current_batch_size = min(batch_size, target_count - generated_count)
            users_batch = user_generator.generate_batch(current_batch_size)

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
        print("\n2. Generating Content Items...")

        # Generate content_items
        content_items_data = self._generate_content_table(
            user_ids, "content_items", ContentItem,
            self.config.target_rows_content_items,
            self.config.batch_size_content_items
        )

        # Generate content_items_auto
        content_items_auto_data = self._generate_content_table(
            user_ids, "content_items_auto", ContentItemAuto,
            self.config.target_rows_content_items_auto,
            self.config.batch_size_content_items_auto
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
            self.config.dict(), user_ids, self.admin_uuid, table_name
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
        print("\n3. Generating Generation Jobs...")

        # Combine all content data
        all_content_data = content_items_data + content_items_auto_data

        # First, create completed jobs for each content item
        completed_jobs_count = self._generate_completed_jobs(all_content_data)

        # Then, create additional jobs with varied statuses to meet distribution requirements
        additional_jobs_count = self._generate_additional_jobs(user_ids, completed_jobs_count)

        total_jobs = completed_jobs_count + additional_jobs_count
        logger.info(f"Generated {total_jobs} total generation jobs ({completed_jobs_count} completed, {additional_jobs_count} additional)")

        # Update content references in completed jobs
        self._update_job_content_references()

    def _generate_completed_jobs(self, content_data: List[Dict[str, Any]]) -> int:
        """Generate completed jobs for all content items."""
        print("   Creating completed jobs for all content items...")

        batch_size = self.config.batch_size_generation_jobs
        total_content = len(content_data)
        progress = ProgressReporter("completed generation_jobs", total_content)

        job_generator = GenerationJobGenerator(self.config.dict(), content_data)
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

        batch_size = self.config.batch_size_generation_jobs
        progress = ProgressReporter("additional generation_jobs", additional_needed)

        job_generator = GenerationJobGenerator(self.config.dict(), [])
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
        print("   Linking jobs to content items...")

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