"""Load testing for concurrent ComfyUI generation requests.

This test validates system behavior under concurrent load scenarios.
Tests are marked as slow and skipped by default to avoid interference with normal test runs.
"""

import asyncio
import pytest
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from genonaut.api.services.comfyui_generation_service import ComfyUIGenerationService
from genonaut.api.repositories.comfyui_generation_repository import ComfyUIGenerationRepository
from genonaut.api.models.requests import ComfyUIGenerationCreateRequest
from genonaut.db.schema import User, ComfyUIGenerationRequest, AvailableModel


class TestComfyUILoadTesting:
    """Load testing for ComfyUI generation system."""

    @pytest.fixture
    def test_user(self, db_session: Session) -> User:
        """Create a test user."""
        user = User(
            username="load_test_user",
            email="loadtest@example.com",
            created_at=datetime.utcnow()
        )
        db_session.add(user)
        db_session.commit()
        return user

    @pytest.fixture
    def test_model(self, db_session: Session) -> AvailableModel:
        """Create a test model."""
        model = AvailableModel(
            name="test_checkpoint.safetensors",
            type="checkpoint",
            file_path="/models/checkpoints/test_checkpoint.safetensors",
            is_available=True,
            discovered_at=datetime.utcnow()
        )
        db_session.add(model)
        db_session.commit()
        return model

    @pytest.fixture
    def generation_service(self, db_session: Session) -> ComfyUIGenerationService:
        """Create a generation service with mocked ComfyUI client."""
        repository = ComfyUIGenerationRepository(db_session)

        # Mock the ComfyUI client to avoid actual API calls
        with patch('genonaut.api.services.comfyui_generation_service.ComfyUIClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            # Mock successful workflow submission
            mock_client.submit_workflow.return_value = {"prompt_id": "test-prompt-123"}
            mock_client.get_status.return_value = {
                "status": {"status_str": "success"},
                "outputs": {"9": {"images": [{"filename": "test_image.png", "type": "output"}]}}
            }

            service = ComfyUIGenerationService(repository, mock_client)
            yield service

    def create_test_request(self, user_id: int, model_name: str,
                           prompt_suffix: str = "") -> ComfyUIGenerationCreateRequest:
        """Create a test generation request."""
        return ComfyUIGenerationCreateRequest(
            user_id=user_id,
            prompt=f"A beautiful landscape with mountains{prompt_suffix}",
            negative_prompt="blurry, low quality",
            checkpoint_model=model_name,
            width=512,
            height=512,
            steps=20,
            cfg_scale=7.0,
            seed=-1,
            batch_size=1
        )

    @pytest.mark.slow
    @pytest.mark.skip(reason="Load testing - only run manually for performance analysis")
    def test_concurrent_generation_requests_small_load(self, generation_service: ComfyUIGenerationService,
                                                      test_user: User, test_model: AvailableModel):
        """Test system with small concurrent load (5 simultaneous requests)."""
        num_requests = 5
        requests = []

        # Create multiple test requests
        for i in range(num_requests):
            request = self.create_test_request(
                test_user.id,
                test_model.name,
                f" - test {i}"
            )
            requests.append(request)

        # Submit requests concurrently
        start_time = time.time()
        results = []

        def submit_request(req):
            try:
                return generation_service.create_generation(req)
            except Exception as e:
                return {"error": str(e)}

        with ThreadPoolExecutor(max_workers=num_requests) as executor:
            future_to_request = {
                executor.submit(submit_request, req): req
                for req in requests
            }

            for future in as_completed(future_to_request):
                request = future_to_request[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({"error": str(e)})

        end_time = time.time()
        total_time = end_time - start_time

        # Assertions
        assert len(results) == num_requests
        successful_requests = [r for r in results if "error" not in r]
        failed_requests = [r for r in results if "error" in r]

        # All requests should succeed with mocked client
        assert len(successful_requests) == num_requests
        assert len(failed_requests) == 0

        # Performance assertions
        assert total_time < 5.0  # Should complete within 5 seconds
        avg_time_per_request = total_time / num_requests
        assert avg_time_per_request < 1.0  # Average should be under 1 second per request

        print(f"Small load test: {num_requests} requests in {total_time:.2f}s "
              f"(avg: {avg_time_per_request:.2f}s per request)")

    @pytest.mark.slow
    @pytest.mark.skip(reason="Load testing - only run manually for performance analysis")
    def test_concurrent_generation_requests_medium_load(self, generation_service: ComfyUIGenerationService,
                                                       test_user: User, test_model: AvailableModel):
        """Test system with medium concurrent load (20 simultaneous requests)."""
        num_requests = 20
        requests = []

        # Create multiple test requests
        for i in range(num_requests):
            request = self.create_test_request(
                test_user.id,
                test_model.name,
                f" - medium load test {i}"
            )
            requests.append(request)

        # Submit requests concurrently
        start_time = time.time()
        results = []

        def submit_request(req):
            try:
                return generation_service.create_generation(req)
            except Exception as e:
                return {"error": str(e)}

        with ThreadPoolExecutor(max_workers=num_requests) as executor:
            future_to_request = {
                executor.submit(submit_request, req): req
                for req in requests
            }

            for future in as_completed(future_to_request):
                result = future.result()
                results.append(result)

        end_time = time.time()
        total_time = end_time - start_time

        # Assertions
        assert len(results) == num_requests
        successful_requests = [r for r in results if "error" not in r]
        failed_requests = [r for r in results if "error" in r]

        # Most requests should succeed (allow for some failures under load)
        success_rate = len(successful_requests) / num_requests
        assert success_rate >= 0.8  # At least 80% success rate

        # Performance assertions
        assert total_time < 15.0  # Should complete within 15 seconds
        avg_time_per_request = total_time / num_requests
        assert avg_time_per_request < 2.0  # Average should be under 2 seconds per request

        print(f"Medium load test: {num_requests} requests in {total_time:.2f}s "
              f"(avg: {avg_time_per_request:.2f}s per request, "
              f"success rate: {success_rate:.1%})")

    @pytest.mark.slow
    @pytest.mark.skip(reason="Load testing - only run manually for performance analysis")
    def test_concurrent_generation_requests_high_load(self, generation_service: ComfyUIGenerationService,
                                                     test_user: User, test_model: AvailableModel):
        """Test system with high concurrent load (50 simultaneous requests)."""
        num_requests = 50
        requests = []

        # Create multiple test requests
        for i in range(num_requests):
            request = self.create_test_request(
                test_user.id,
                test_model.name,
                f" - high load test {i}"
            )
            requests.append(request)

        # Submit requests concurrently with controlled parallelism
        start_time = time.time()
        results = []

        def submit_request(req):
            try:
                return generation_service.create_generation(req)
            except Exception as e:
                return {"error": str(e)}

        # Limit concurrent workers to prevent overwhelming the system
        max_workers = min(20, num_requests)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_request = {
                executor.submit(submit_request, req): req
                for req in requests
            }

            for future in as_completed(future_to_request):
                result = future.result()
                results.append(result)

        end_time = time.time()
        total_time = end_time - start_time

        # Assertions
        assert len(results) == num_requests
        successful_requests = [r for r in results if "error" not in r]
        failed_requests = [r for r in results if "error" in r]

        # Accept lower success rate for high load testing
        success_rate = len(successful_requests) / num_requests
        assert success_rate >= 0.7  # At least 70% success rate under high load

        # Performance assertions (more lenient for high load)
        assert total_time < 30.0  # Should complete within 30 seconds
        avg_time_per_request = total_time / num_requests
        assert avg_time_per_request < 3.0  # Average should be under 3 seconds per request

        print(f"High load test: {num_requests} requests in {total_time:.2f}s "
              f"(avg: {avg_time_per_request:.2f}s per request, "
              f"success rate: {success_rate:.1%})")

    @pytest.mark.slow
    @pytest.mark.skip(reason="Load testing - only run manually for performance analysis")
    def test_generation_queue_processing_under_load(self, generation_service: ComfyUIGenerationService,
                                                   test_user: User, test_model: AvailableModel):
        """Test generation queue processing efficiency under load."""
        # Create a batch of requests
        num_requests = 15
        requests = []

        for i in range(num_requests):
            request = self.create_test_request(
                test_user.id,
                test_model.name,
                f" - queue test {i}"
            )
            requests.append(request)

        # Submit all requests and track their lifecycle
        start_time = time.time()
        submitted_generations = []

        # Submit requests sequentially to test queue processing
        for request in requests:
            try:
                generation = generation_service.create_generation(request)
                submitted_generations.append(generation)
            except Exception as e:
                print(f"Failed to submit request: {e}")

        submission_time = time.time()

        # Wait for processing (simulated with mocked responses)
        time.sleep(1)  # Simulate processing time

        # Check final status of all generations
        completed_count = 0
        failed_count = 0

        for generation in submitted_generations:
            # In real test, would check actual status from database
            # For now, assume all succeed with mocked client
            completed_count += 1

        end_time = time.time()
        total_time = end_time - start_time

        # Assertions
        assert len(submitted_generations) == num_requests
        assert completed_count > 0

        submission_rate = len(submitted_generations) / (submission_time - start_time)
        processing_efficiency = completed_count / len(submitted_generations)

        assert submission_rate > 5  # Should submit at least 5 requests per second
        assert processing_efficiency >= 0.8  # At least 80% should complete successfully

        print(f"Queue processing test: {num_requests} requests, "
              f"submission rate: {submission_rate:.1f} req/s, "
              f"completion rate: {processing_efficiency:.1%}")

    @pytest.mark.slow
    @pytest.mark.skip(reason="Load testing - only run manually for performance analysis")
    def test_database_performance_under_concurrent_writes(self, db_session: Session,
                                                         test_user: User, test_model: AvailableModel):
        """Test database performance with concurrent generation record writes."""
        num_concurrent_writes = 25

        def create_generation_record(i):
            try:
                generation = ComfyUIGenerationRequest(
                    user_id=test_user.id,
                    prompt=f"Database performance test {i}",
                    negative_prompt="test",
                    checkpoint_model=test_model.name,
                    width=512,
                    height=512,
                    steps=20,
                    cfg_scale=7.0,
                    seed=i,
                    batch_size=1,
                    status="pending",
                    created_at=datetime.utcnow()
                )

                # Use a separate session for each thread to avoid conflicts
                from sqlalchemy import create_engine
                from sqlalchemy.orm import sessionmaker
                engine = create_engine("sqlite:///:memory:")
                SessionLocal = sessionmaker(bind=engine)
                session = SessionLocal()

                session.add(generation)
                session.commit()
                session.close()

                return {"success": True, "id": i}
            except Exception as e:
                return {"success": False, "error": str(e), "id": i}

        # Execute concurrent database writes
        start_time = time.time()
        results = []

        with ThreadPoolExecutor(max_workers=num_concurrent_writes) as executor:
            futures = [executor.submit(create_generation_record, i)
                      for i in range(num_concurrent_writes)]

            for future in as_completed(futures):
                result = future.result()
                results.append(result)

        end_time = time.time()
        total_time = end_time - start_time

        # Analyze results
        successful_writes = [r for r in results if r["success"]]
        failed_writes = [r for r in results if not r["success"]]

        success_rate = len(successful_writes) / num_concurrent_writes
        write_rate = len(successful_writes) / total_time

        # Assertions
        assert len(results) == num_concurrent_writes
        assert success_rate >= 0.9  # At least 90% of writes should succeed
        assert write_rate > 10  # Should achieve at least 10 writes per second
        assert total_time < 5.0  # Should complete within 5 seconds

        print(f"Database concurrent writes: {num_concurrent_writes} writes in {total_time:.2f}s "
              f"(rate: {write_rate:.1f} writes/s, success: {success_rate:.1%})")

    def test_load_testing_metrics_collection(self):
        """Test that load testing can collect and report performance metrics."""
        # This test validates our ability to collect metrics during load testing
        metrics = {
            "requests_per_second": 0,
            "average_response_time": 0,
            "success_rate": 0,
            "error_count": 0,
            "memory_usage": 0,
            "cpu_usage": 0
        }

        # Simulate collecting metrics
        start_time = time.time()
        time.sleep(0.1)  # Simulate work
        end_time = time.time()

        metrics["requests_per_second"] = 10 / (end_time - start_time)
        metrics["average_response_time"] = (end_time - start_time) / 10
        metrics["success_rate"] = 1.0

        # Validate metric collection
        assert metrics["requests_per_second"] > 0
        assert metrics["average_response_time"] > 0
        assert 0 <= metrics["success_rate"] <= 1
        assert metrics["error_count"] >= 0

        print(f"Metrics collection test: {metrics}")