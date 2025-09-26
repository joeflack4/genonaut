"""Performance tests for ComfyUI-related database queries.

This test validates query performance for ComfyUI generation operations
including complex joins, filtering, and aggregations.
"""

import pytest
import time
from datetime import datetime, timedelta
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from genonaut.db.schema import User, ComfyUIGenerationRequest, AvailableModel
from genonaut.api.repositories.comfyui_generation_repository import ComfyUIGenerationRepository
from genonaut.api.models.requests import PaginationRequest


class TestComfyUIQueryPerformance:
    """Performance tests for ComfyUI database queries."""

    @pytest.fixture
    def sample_users(self, db_session: Session) -> List[User]:
        """Create sample users for testing."""
        users = []
        for i in range(50):
            user = User(
                username=f"comfyui_user_{i:03d}",
                email=f"comfyui{i:03d}@example.com",
                created_at=datetime.utcnow() - timedelta(days=i),
                is_active=i % 5 != 0  # 80% active users
            )
            db_session.add(user)
            users.append(user)

        db_session.commit()
        return users

    @pytest.fixture
    def sample_models(self, db_session: Session) -> List[AvailableModel]:
        """Create sample models for testing."""
        models = []
        model_types = ["checkpoint", "lora", "vae", "controlnet"]

        for i in range(20):
            model = AvailableModel(
                name=f"test_model_{i:03d}.safetensors",
                type=model_types[i % len(model_types)],
                file_path=f"/models/{model_types[i % len(model_types)]}/test_model_{i:03d}.safetensors",
                is_active=i % 10 != 0,  # 90% active
                created_at=datetime.utcnow() - timedelta(hours=i)
            )
            db_session.add(model)
            models.append(model)

        db_session.commit()
        return models

    @pytest.fixture
    def sample_generations(self, db_session: Session, sample_users: List[User],
                          sample_models: List[AvailableModel]) -> List[ComfyUIGenerationRequest]:
        """Create sample generation requests for testing."""
        generations = []
        statuses = ["pending", "processing", "completed", "failed", "cancelled"]

        for i in range(500):
            user = sample_users[i % len(sample_users)]
            checkpoint_model = [m for m in sample_models if m.type == "checkpoint"][i % 5]

            generation = ComfyUIGenerationRequest(
                user_id=user.id,
                prompt=f"Test generation prompt {i:04d} with various details",
                negative_prompt="low quality, blurry" if i % 3 == 0 else "",
                checkpoint_model=checkpoint_model.name,
                width=512 if i % 2 == 0 else 768,
                height=512 if i % 2 == 0 else 768,
                steps=20 + (i % 30),  # 20-50 steps
                cfg_scale=7.0 + (i % 10) * 0.5,  # 7.0-12.0
                seed=i if i % 10 != 0 else -1,  # Some random seeds
                batch_size=1 if i % 5 != 0 else 4,  # Mostly single, some batch
                status=statuses[i % len(statuses)],
                created_at=datetime.utcnow() - timedelta(hours=i % 240),  # Last 10 days
                started_at=datetime.utcnow() - timedelta(hours=(i % 240) - 1) if i % 5 != 0 else None,
                completed_at=datetime.utcnow() - timedelta(hours=(i % 240) - 2) if i % 7 == 0 else None,
                error_message=f"Test error message {i}" if i % 20 == 0 else None
            )
            db_session.add(generation)
            generations.append(generation)

        db_session.commit()
        return generations

    @pytest.mark.skip(reason="Skipped until schema finalization - 'steps' field not in current schema")
    def test_generation_list_query_performance(self, db_session: Session,
                                             sample_generations: List[ComfyUIGenerationRequest]):
        """Test performance of basic generation list queries."""
        repository = ComfyUIGenerationRepository(db_session)

        pagination_request = PaginationRequest(page=1, page_size=50)

        # Test basic paginated query
        start_time = time.time()
        result = repository.get_paginated(pagination_request)
        end_time = time.time()

        query_time = end_time - start_time

        # Assertions
        assert len(result.items) > 0
        assert result.pagination.total_count > 0
        assert query_time < 0.1  # Should complete in less than 100ms

        print(f"Basic generation list query: {query_time:.3f}s for {len(result.items)} items")

    @pytest.mark.skip(reason="Skipped until schema finalization - 'steps' field not in current schema")
    def test_generation_by_user_query_performance(self, db_session: Session,
                                                 sample_users: List[User],
                                                 sample_generations: List[ComfyUIGenerationRequest]):
        """Test performance of user-specific generation queries."""
        repository = ComfyUIGenerationRepository(db_session)
        user_id = sample_users[0].id

        pagination_request = PaginationRequest(page=1, page_size=25)

        # Test user-specific query
        start_time = time.time()
        result = repository.get_by_user_paginated(user_id, pagination_request)
        end_time = time.time()

        query_time = end_time - start_time

        # Assertions
        assert len(result.items) > 0
        assert result.pagination.total_count > 0
        assert query_time < 0.05  # Should be very fast with user_id index

        # Verify all items belong to the user
        for item in result.items:
            assert item.user_id == user_id

        print(f"Generation by user query: {query_time:.3f}s for {len(result.items)} items")

    @pytest.mark.skip(reason="Skipped until schema finalization - 'steps' field not in current schema")
    def test_generation_by_status_query_performance(self, db_session: Session,
                                                   sample_generations: List[ComfyUIGenerationRequest]):
        """Test performance of status-filtered generation queries."""
        repository = ComfyUIGenerationRepository(db_session)

        pagination_request = PaginationRequest(page=1, page_size=50)

        # Test status filter query
        start_time = time.time()
        result = repository.get_by_status_paginated("completed", pagination_request)
        end_time = time.time()

        query_time = end_time - start_time

        # Assertions
        assert len(result.items) >= 0  # May be empty if no completed generations
        assert query_time < 0.08  # Should be fast with status index

        # Verify all items have correct status
        for item in result.items:
            assert item.status == "completed"

        print(f"Generation by status query: {query_time:.3f}s for {len(result.items)} items")

    @pytest.mark.skip(reason="Skipped until schema finalization - 'steps' field not in current schema")
    def test_generation_by_model_query_performance(self, db_session: Session,
                                                  sample_models: List[AvailableModel],
                                                  sample_generations: List[ComfyUIGenerationRequest]):
        """Test performance of model-specific generation queries."""
        repository = ComfyUIGenerationRepository(db_session)
        checkpoint_models = [m for m in sample_models if m.type == "checkpoint"]
        model_name = checkpoint_models[0].name

        pagination_request = PaginationRequest(page=1, page_size=30)

        # Test model-specific query
        start_time = time.time()
        result = repository.get_by_model_paginated(model_name, pagination_request)
        end_time = time.time()

        query_time = end_time - start_time

        # Assertions
        assert len(result.items) >= 0
        assert query_time < 0.08  # Should be fast with model index

        # Verify all items use the correct model
        for item in result.items:
            assert item.checkpoint_model == model_name

        print(f"Generation by model query: {query_time:.3f}s for {len(result.items)} items")

    @pytest.mark.skip(reason="Skipped until schema finalization - 'steps' field not in current schema")
    def test_generation_statistics_query_performance(self, db_session: Session,
                                                    sample_generations: List[ComfyUIGenerationRequest]):
        """Test performance of generation statistics aggregation queries."""
        start_time = time.time()

        # Complex aggregation query
        stats = db_session.query(
            func.count(ComfyUIGenerationRequest.id).label('total_generations'),
            func.count(func.distinct(ComfyUIGenerationRequest.user_id)).label('unique_users'),
            func.avg(ComfyUIGenerationRequest.steps).label('avg_steps'),
            func.avg(ComfyUIGenerationRequest.cfg_scale).label('avg_cfg_scale'),
            func.sum(ComfyUIGenerationRequest.batch_size).label('total_images')
        ).filter(
            ComfyUIGenerationRequest.created_at >= datetime.utcnow() - timedelta(days=7)
        ).first()

        end_time = time.time()
        query_time = end_time - start_time

        # Assertions
        assert stats.total_generations > 0
        assert stats.unique_users > 0
        assert query_time < 0.15  # Aggregation queries can be slower but should be reasonable

        print(f"Generation statistics query: {query_time:.3f}s "
              f"(total: {stats.total_generations}, users: {stats.unique_users})")

    @pytest.mark.skip(reason="Skipped until schema finalization - 'steps' field not in current schema")
    def test_generation_with_user_join_performance(self, db_session: Session,
                                                  sample_generations: List[ComfyUIGenerationRequest]):
        """Test performance of generation queries with user table joins."""
        start_time = time.time()

        # Query with join to user table
        results = db_session.query(
            ComfyUIGenerationRequest,
            User.username
        ).join(
            User, ComfyUIGenerationRequest.user_id == User.id
        ).filter(
            ComfyUIGenerationRequest.status == "completed",
            User.is_active == True
        ).limit(50).all()

        end_time = time.time()
        query_time = end_time - start_time

        # Assertions
        assert len(results) >= 0
        assert query_time < 0.12  # Join queries can be slower but should be optimized

        print(f"Generation with user join query: {query_time:.3f}s for {len(results)} items")

    @pytest.mark.skip(reason="Skipped until schema finalization - 'steps' field not in current schema")
    def test_generation_date_range_query_performance(self, db_session: Session,
                                                    sample_generations: List[ComfyUIGenerationRequest]):
        """Test performance of date range queries."""
        repository = ComfyUIGenerationRepository(db_session)

        # Test recent generations (last 24 hours)
        start_time = time.time()
        recent_count = repository.count({
            "created_after": datetime.utcnow() - timedelta(hours=24)
        })
        end_time = time.time()

        query_time = end_time - start_time

        # Assertions
        assert recent_count >= 0
        assert query_time < 0.05  # Date range queries should be fast with indexes

        print(f"Date range query: {query_time:.3f}s (found {recent_count} recent generations)")

    @pytest.mark.skip(reason="Skipped until schema finalization - 'steps' field not in current schema")
    def test_generation_complex_filter_performance(self, db_session: Session,
                                                  sample_generations: List[ComfyUIGenerationRequest]):
        """Test performance of complex multi-filter queries."""
        repository = ComfyUIGenerationRepository(db_session)

        pagination_request = PaginationRequest(page=1, page_size=20)
        filters = {
            "status": "completed",
            "width": 512,
            "height": 512,
            "steps_min": 20,
            "steps_max": 30
        }

        start_time = time.time()
        result = repository.get_paginated(pagination_request, filters=filters)
        end_time = time.time()

        query_time = end_time - start_time

        # Assertions
        assert len(result.items) >= 0
        assert query_time < 0.15  # Complex filters may be slower but should be reasonable

        # Verify filters are applied
        for item in result.items:
            assert item.status == "completed"
            assert item.width == 512
            assert item.height == 512
            assert 20 <= item.steps <= 30

        print(f"Complex filter query: {query_time:.3f}s for {len(result.items)} items with multiple filters")

    @pytest.mark.skip(reason="Skipped until schema finalization - 'steps' field not in current schema")
    def test_generation_search_query_performance(self, db_session: Session,
                                                sample_generations: List[ComfyUIGenerationRequest]):
        """Test performance of text search queries."""
        repository = ComfyUIGenerationRepository(db_session)

        pagination_request = PaginationRequest(page=1, page_size=25)

        # Test prompt text search
        start_time = time.time()
        result = repository.search_by_prompt("Test generation", pagination_request)
        end_time = time.time()

        query_time = end_time - start_time

        # Assertions
        assert len(result.items) >= 0
        assert query_time < 0.2  # Text search can be slower without full-text indexes

        # Verify search results contain the search term
        for item in result.items:
            assert "Test generation" in item.prompt

        print(f"Text search query: {query_time:.3f}s for {len(result.items)} items")

    @pytest.mark.skip(reason="Skipped until schema finalization - 'steps' field not in current schema")
    def test_available_models_query_performance(self, db_session: Session,
                                              sample_models: List[AvailableModel]):
        """Test performance of available models queries."""
        start_time = time.time()

        # Query available models by type
        checkpoint_models = db_session.query(AvailableModel).filter(
            AvailableModel.type == "checkpoint",
            AvailableModel.is_active == True
        ).order_by(AvailableModel.name).all()

        end_time = time.time()
        query_time = end_time - start_time

        # Assertions
        assert len(checkpoint_models) > 0
        assert query_time < 0.05  # Should be very fast for model queries

        # Verify results
        for model in checkpoint_models:
            assert model.type == "checkpoint"
            assert model.is_active is True

        print(f"Available models query: {query_time:.3f}s for {len(checkpoint_models)} models")

    @pytest.mark.skip(reason="Skipped until schema finalization - 'steps' field not in current schema")
    def test_model_usage_statistics_performance(self, db_session: Session,
                                               sample_generations: List[ComfyUIGenerationRequest]):
        """Test performance of model usage statistics queries."""
        start_time = time.time()

        # Query model usage statistics
        model_stats = db_session.query(
            ComfyUIGenerationRequest.checkpoint_model,
            func.count(ComfyUIGenerationRequest.id).label('usage_count'),
            func.count(func.distinct(ComfyUIGenerationRequest.user_id)).label('unique_users'),
            func.avg(ComfyUIGenerationRequest.steps).label('avg_steps')
        ).filter(
            ComfyUIGenerationRequest.status == "completed"
        ).group_by(
            ComfyUIGenerationRequest.checkpoint_model
        ).order_by(
            func.count(ComfyUIGenerationRequest.id).desc()
        ).limit(10).all()

        end_time = time.time()
        query_time = end_time - start_time

        # Assertions
        assert len(model_stats) >= 0
        assert query_time < 0.2  # Group by queries can be slower but should be reasonable

        print(f"Model usage statistics query: {query_time:.3f}s for {len(model_stats)} models")

    @pytest.mark.slow
    @pytest.mark.skip(reason="Performance stress testing - only run manually")
    def test_large_dataset_query_performance(self, db_session: Session):
        """Test query performance with a larger dataset."""
        # Create a larger test dataset
        users = []
        for i in range(100):
            user = User(
                username=f"perf_user_{i:05d}",
                email=f"perf{i:05d}@example.com",
                created_at=datetime.utcnow() - timedelta(days=i % 365)
            )
            db_session.add(user)
            users.append(user)

        models = []
        for i in range(10):
            model = AvailableModel(
                name=f"perf_model_{i:03d}.safetensors",
                type="checkpoint",
                file_path=f"/models/checkpoints/perf_model_{i:03d}.safetensors",
                is_active=True,
                created_at=datetime.utcnow()
            )
            db_session.add(model)
            models.append(model)

        # Create 5000 generation records
        generations = []
        for i in range(5000):
            generation = ComfyUIGenerationRequest(
                user_id=users[i % len(users)].id,
                prompt=f"Large dataset performance test {i:05d}",
                checkpoint_model=models[i % len(models)].name,
                width=512,
                height=512,
                steps=20,
                cfg_scale=7.0,
                seed=i,
                batch_size=1,
                status=["pending", "processing", "completed", "failed"][i % 4],
                created_at=datetime.utcnow() - timedelta(hours=i % (24 * 30))
            )
            db_session.add(generation)
            generations.append(generation)

        db_session.commit()

        repository = ComfyUIGenerationRepository(db_session)

        # Test various queries with large dataset
        test_cases = [
            ("Basic pagination", lambda: repository.get_paginated(PaginationRequest(page=50, page_size=50))),
            ("User filter", lambda: repository.get_by_user_paginated(users[0].id, PaginationRequest(page=1, page_size=50))),
            ("Status filter", lambda: repository.get_by_status_paginated("completed", PaginationRequest(page=1, page_size=50))),
            ("Date range", lambda: repository.count({"created_after": datetime.utcnow() - timedelta(days=7)})),
        ]

        for test_name, test_func in test_cases:
            start_time = time.time()
            result = test_func()
            end_time = time.time()
            query_time = end_time - start_time

            assert query_time < 0.5, f"{test_name} took {query_time:.3f}s - too slow!"
            print(f"Large dataset {test_name}: {query_time:.3f}s")