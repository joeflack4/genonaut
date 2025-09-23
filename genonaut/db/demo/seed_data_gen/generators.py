"""Data generators for synthetic seed data creation."""

import random
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from faker import Faker
from zoneinfo import ZoneInfo

from .prompt_engine import PromptEngine, GLOBAL_TAGS


class DataGenerator:
    """Base class for data generators."""

    def __init__(self, config: Dict[str, Any], fake: Optional[Faker] = None):
        self.config = config
        self.fake = fake or Faker()
        self.fake.seed_instance(random.randint(0, 1000000))

        # Date range for generation (ET timezone)
        self.et_tz = ZoneInfo("America/New_York")
        self.start_date = datetime(2025, 5, 1, 0, 0, 0, tzinfo=self.et_tz)
        self.end_date = datetime(2025, 9, 21, 23, 59, 59, tzinfo=self.et_tz)

    def random_datetime_et_to_utc(self) -> datetime:
        """Generate random datetime in ET range, convert to UTC for storage."""
        et_datetime = self.fake.date_time_between(
            start_date=self.start_date,
            end_date=self.end_date
        ).replace(tzinfo=self.et_tz)
        return et_datetime.astimezone(timezone.utc).replace(tzinfo=None)


class UserGenerator(DataGenerator):
    """Generates user data with uniqueness handling."""

    def __init__(self, config: Dict[str, Any], admin_uuid: str):
        super().__init__(config)
        self.admin_uuid = admin_uuid
        self.generated_usernames = set()

    def generate_batch(self, batch_size: int) -> List[Dict[str, Any]]:
        """Generate a batch of users."""
        users = []
        attempts = 0
        max_attempts = batch_size * 3  # Prevent infinite loops

        # Always include admin user in first batch
        if not hasattr(self, '_admin_generated'):
            admin_user = self._generate_admin_user()
            users.append(admin_user)
            self._admin_generated = True

        while len(users) < batch_size and attempts < max_attempts:
            attempts += 1
            user = self._generate_single_user()

            # Check for username uniqueness
            if user['username'] not in self.generated_usernames:
                self.generated_usernames.add(user['username'])
                users.append(user)

        return users

    def _generate_admin_user(self) -> Dict[str, Any]:
        """Generate the admin user with fixed UUID."""
        created_at = self.random_datetime_et_to_utc()
        return {
            'id': self.admin_uuid,
            'username': self.fake.user_name(),
            'email': self.fake.email(),
            'created_at': created_at,
            'updated_at': created_at,
            'is_active': True,
            'preferences': {
                'favorite_tags': PromptEngine.get_user_favorite_tags()
            }
        }

    def _generate_single_user(self) -> Dict[str, Any]:
        """Generate a single user."""
        created_at = self.random_datetime_et_to_utc()
        is_active = random.random() < 0.99  # 99% active

        return {
            'id': str(uuid.uuid4()),
            'username': self.fake.user_name(),
            'email': self.fake.email(),
            'created_at': created_at,
            'updated_at': created_at,
            'is_active': is_active,
            'preferences': {
                'favorite_tags': PromptEngine.get_user_favorite_tags()
            }
        }


class ContentGenerator(DataGenerator):
    """Generates content items with FK relationships."""

    def __init__(self, config: Dict[str, Any], user_ids: List[str], admin_uuid: str, table_name: str):
        super().__init__(config)
        self.user_ids = user_ids
        self.admin_uuid = admin_uuid
        self.table_name = table_name
        self.prompt_engine = PromptEngine(config)
        self.admin_items_created = 0
        self.admin_items_needed = 50

    def generate_batch(self, batch_size: int) -> List[Dict[str, Any]]:
        """Generate a batch of content items."""
        items = []

        for _ in range(batch_size):
            item = self._generate_single_item()
            items.append(item)

        return items

    def _generate_single_item(self) -> Dict[str, Any]:
        """Generate a single content item."""
        # Determine creator - ensure exactly 50 go to admin
        if self.admin_items_created < self.admin_items_needed:
            creator_id = self.admin_uuid
            self.admin_items_created += 1
        else:
            creator_id = random.choice(self.user_ids)

        # Generate prompt and title
        prompt = self.prompt_engine.generate_prompt()
        title = prompt[:20]  # First 20 characters as title

        # Generate metadata
        style = random.choice(["anime", "illustration", "photorealistic"])
        resolution = random.choice([
            "1024x768", "1920x1080", "2560x1440", "1080x1920",
            "1280x720", "3840x2160", "1366x768", "1024x1024"
        ])
        tags = PromptEngine.get_random_tags(0, 200)

        # Content data path
        content_uuid = str(uuid.uuid4())
        images_dir = self.config.get('images_dir', 'io/storage/images/')
        content_data = f"{images_dir}/{content_uuid}.png"

        created_at = self.random_datetime_et_to_utc()
        is_private = random.random() < 0.1  # 10% private

        return {
            'title': title,
            'content_type': 'image',
            'content_data': content_data,
            'item_metadata': {
                'style': style,
                'resolution': resolution,
                'tags': tags,
                'prompt': prompt  # Store for generation jobs
            },
            'creator_id': creator_id,
            'created_at': created_at,
            'updated_at': created_at,
            'tags': tags,  # Also store at top level
            'quality_score': round(random.random(), 2),
            'is_private': is_private
        }


class GenerationJobGenerator(DataGenerator):
    """Generates generation jobs linked to content items."""

    def __init__(self, config: Dict[str, Any], content_items: List[Dict[str, Any]]):
        super().__init__(config)
        self.content_items = content_items
        self.completed_jobs_created = 0

    def generate_completed_jobs_batch(self, batch_size: int) -> List[Dict[str, Any]]:
        """Generate completed jobs for content items."""
        jobs = []

        # Get the next batch of content items that need completed jobs
        start_idx = self.completed_jobs_created
        end_idx = min(start_idx + batch_size, len(self.content_items))

        for i in range(start_idx, end_idx):
            content_item = self.content_items[i]
            job = self._generate_completed_job(content_item)
            jobs.append(job)
            self.completed_jobs_created += 1

        return jobs

    def generate_additional_jobs_batch(self, batch_size: int, user_ids: List[str]) -> List[Dict[str, Any]]:
        """Generate additional jobs with varied statuses."""
        jobs = []

        for _ in range(batch_size):
            # Determine status based on distribution
            rand = random.random()
            if rand < 0.98:
                status = "completed"
            elif rand < 0.989:
                status = "pending"
            elif rand < 0.999:
                status = "error"
            else:
                status = "canceled"

            job = self._generate_additional_job(user_ids, status)
            jobs.append(job)

        return jobs

    def _generate_completed_job(self, content_item: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a completed job for a specific content item."""
        # Extract prompt from content item metadata
        prompt = content_item['item_metadata'].get('prompt', '')
        if not prompt:
            # Fallback prompt generation
            from .prompt_engine import PromptEngine
            prompt_engine = PromptEngine(self.config)
            prompt = prompt_engine.generate_prompt()

        completed_at = self.random_datetime_et_to_utc()

        return {
            'user_id': content_item['creator_id'],
            'job_type': 'image',
            'prompt': prompt,
            'parameters': {},
            'status': 'completed',
            'result_content_id': None,  # Will be set after content insertion
            'created_at': completed_at,
            'updated_at': completed_at,
            'started_at': None,
            'completed_at': completed_at,
            'error_message': None
        }

    def _generate_additional_job(self, user_ids: List[str], status: str) -> Dict[str, Any]:
        """Generate additional job with specified status."""
        from .prompt_engine import PromptEngine
        prompt_engine = PromptEngine(self.config)
        prompt = prompt_engine.generate_prompt()

        created_at = self.random_datetime_et_to_utc()
        job_data = {
            'user_id': random.choice(user_ids),
            'job_type': 'image',
            'prompt': prompt,
            'parameters': {},
            'status': status,
            'result_content_id': None,
            'created_at': created_at,
            'updated_at': created_at,
            'started_at': None,
            'completed_at': None,
            'error_message': None
        }

        if status == 'completed':
            job_data['completed_at'] = self.random_datetime_et_to_utc()

        return job_data