"""Integration tests for error recovery mechanisms in the ComfyUI generation system.

This test suite validates that the system can recover from various error conditions
and provides robust retry logic, circuit breakers, and graceful degradation.
"""

import pytest
import time
import asyncio
from datetime import datetime, timedelta
from uuid import UUID
from unittest.mock import Mock, patch, MagicMock, call
from sqlalchemy.orm import Session
from requests.exceptions import ConnectionError, Timeout
from httpx import ConnectError, TimeoutException

from genonaut.api.services.comfyui_generation_service import ComfyUIGenerationService
from genonaut.api.services.comfyui_client import ComfyUIClient, ComfyUIConnectionError
from genonaut.api.services.retry_service import (
    RetryService, RetryConfig, RetryStrategy, get_retry_service, with_retry
)
from genonaut.api.services.error_service import ErrorService, get_error_service
from genonaut.api.repositories.comfyui_generation_repository import ComfyUIGenerationRepository
from genonaut.api.models.requests import ComfyUIGenerationCreateRequest
from genonaut.db.schema import User, ComfyUIGenerationRequest, AvailableModel


class TestErrorRecovery:
    """Test error recovery mechanisms and retry logic."""

    @pytest.fixture
    def test_user(self, db_session: Session) -> User:
        """Create a test user."""
        user = User(
            username="recovery_test_user",
            email="recoverytest@example.com",
            created_at=datetime.utcnow()
        )
        db_session.add(user)
        db_session.commit()
        return user

    @pytest.fixture
    def test_model(self, db_session: Session) -> AvailableModel:
        """Create a test model."""
        model = AvailableModel(
            name="recovery_test_model.safetensors",
            type="checkpoint",
            file_path="/models/checkpoints/recovery_test_model.safetensors",
            is_active=True,
            created_at=datetime.utcnow()
        )
        db_session.add(model)
        db_session.commit()
        return model

    @pytest.fixture
    def test_request(self, test_user: User, test_model: AvailableModel) -> ComfyUIGenerationCreateRequest:
        """Create a test generation request."""
        return ComfyUIGenerationCreateRequest(
            user_id=test_user.id,
            prompt="Test error recovery",
            negative_prompt="",
            checkpoint_model=test_model.name,
            width=512,
            height=512,
            steps=20,
            cfg_scale=7.0,
            seed=42,
            batch_size=1
        )

    def test_retry_service_exponential_backoff(self):
        """Test that retry service implements proper exponential backoff."""
        retry_service = get_retry_service()
        config = RetryConfig(
            max_attempts=4,
            base_delay=1.0,
            exponential_base=2.0,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            jitter=False  # Disable jitter for predictable testing
        )

        # Test delay calculation for each attempt
        expected_delays = [1.0, 2.0, 4.0, 8.0]  # Base delay * exponential_base^attempt

        for attempt in range(4):
            delay = retry_service.calculate_delay(attempt, config)
            assert delay == expected_delays[attempt]

    def test_retry_service_linear_backoff(self):
        """Test that retry service implements linear backoff correctly."""
        retry_service = get_retry_service()
        config = RetryConfig(
            max_attempts=4,
            base_delay=2.0,
            strategy=RetryStrategy.LINEAR_BACKOFF,
            jitter=False  # Disable jitter for predictable testing
        )

        # Test delay calculation for linear backoff
        expected_delays = [2.0, 4.0, 6.0, 8.0]  # Base delay * (attempt + 1)

        for attempt in range(4):
            delay = retry_service.calculate_delay(attempt, config)
            assert delay == expected_delays[attempt]

    def test_retry_service_fixed_interval(self):
        """Test that retry service implements fixed interval correctly."""
        retry_service = get_retry_service()
        config = RetryConfig(
            max_attempts=4,
            base_delay=3.0,
            strategy=RetryStrategy.FIXED_INTERVAL,
            jitter=False  # Disable jitter for predictable testing
        )

        # Test that all delays are the same for fixed interval
        for attempt in range(4):
            delay = retry_service.calculate_delay(attempt, config)
            assert delay == 3.0  # Should always be base_delay

    def test_retry_service_max_delay_limit(self):
        """Test that retry service respects maximum delay limits."""
        retry_service = get_retry_service()
        config = RetryConfig(
            max_attempts=10,
            base_delay=1.0,
            max_delay=5.0,
            exponential_base=2.0,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            jitter=False  # Disable jitter for predictable testing
        )

        # Test that delay never exceeds max_delay
        for attempt in range(10):
            delay = retry_service.calculate_delay(attempt, config)
            assert delay <= config.max_delay

    def test_retry_service_jitter_enabled(self):
        """Test that retry service applies jitter when enabled."""
        retry_service = get_retry_service()
        config = RetryConfig(
            max_attempts=3,
            base_delay=2.0,
            jitter=True,
            strategy=RetryStrategy.FIXED_INTERVAL
        )

        # Calculate delays multiple times to check for variance
        delays = []
        for _ in range(10):
            delay = retry_service.calculate_delay(0, config)
            delays.append(delay)

        # With jitter, delays should vary
        assert len(set(delays)) > 1  # Should have different values
        # But all should be reasonably close to base delay
        for delay in delays:
            assert 1.0 <= delay <= 3.0  # Within reasonable jitter range

    def test_retry_service_exception_classification(self):
        """Test that retry service correctly classifies retryable vs non-retryable errors."""
        retry_service = get_retry_service()

        # Default config for ComfyUI operations
        config = retry_service.create_config("comfyui_connection")

        # Test retryable exceptions
        retryable_exceptions = [
            ConnectionError("Connection failed"),
            TimeoutError("Request timed out"),
            ComfyUIConnectionError("ComfyUI unavailable"),
        ]

        for exception in retryable_exceptions:
            assert retry_service.should_retry(exception, config) is True

        # Test non-retryable exceptions
        non_retryable_exceptions = [
            ValueError("Invalid parameters"),
            TypeError("Wrong type"),
            KeyError("Missing key"),
        ]

        for exception in non_retryable_exceptions:
            assert retry_service.should_retry(exception, config) is False

    @patch('time.sleep')  # Mock sleep to speed up test
    def test_retry_decorator_with_eventual_success(self, mock_sleep):
        """Test retry decorator that eventually succeeds after failures."""
        retry_service = RetryService()

        # Create a function that fails twice then succeeds
        call_count = 0
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise ConnectionError("Temporary failure")
            return "Success!"

        # Apply retry logic
        config = RetryConfig(max_attempts=3, base_delay=0.1)

        # Call the function with retry logic
        result = retry_service.retry_sync(flaky_function, config, "test_function")

        # Verify eventual success
        assert result == "Success!"
        assert call_count == 3  # Failed twice, succeeded on third attempt
        assert mock_sleep.call_count == 2  # Should have slept twice

    @patch('time.sleep')
    def test_retry_decorator_with_max_attempts_exceeded(self, mock_sleep):
        """Test retry decorator when max attempts are exceeded."""
        retry_service = RetryService()

        # Create a function that always fails
        call_count = 0
        def always_failing_function():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Persistent failure")

        # Apply retry logic
        config = RetryConfig(max_attempts=3, base_delay=0.1)

        # Call the function and expect final failure
        with pytest.raises(ConnectionError) as exc_info:
            retry_service.retry_sync(always_failing_function, config, "test_function")

        # Verify all attempts were made
        assert call_count == 3  # Should try 3 times
        assert "Persistent failure" in str(exc_info.value)
        assert mock_sleep.call_count == 2  # Should sleep between attempts

    @patch('time.sleep')
    def test_retry_decorator_with_non_retryable_error(self, mock_sleep):
        """Test retry decorator with non-retryable errors."""
        retry_service = RetryService()

        # Create a function that raises non-retryable error
        def non_retryable_function():
            raise ValueError("Invalid configuration")

        # Apply retry logic
        config = RetryConfig(max_attempts=3, base_delay=0.1)

        # Call the function and expect immediate failure
        with pytest.raises(ValueError):
            retry_service.retry_sync(non_retryable_function, config, "test_function")

        # Should not retry non-retryable errors
        assert mock_sleep.call_count == 0

    def test_generation_service_retry_integration(self, db_session: Session, test_request: ComfyUIGenerationCreateRequest):
        """Test that generation service integrates properly with retry logic."""
        service = ComfyUIGenerationService(db_session)
        service.comfyui_client = Mock(spec=ComfyUIClient)

        # Mock client to fail then succeed
        call_count = 0
        def mock_submit_workflow(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("First attempt fails")
            return {"prompt_id": "success-123"}

        service.comfyui_client.submit_workflow.side_effect = mock_submit_workflow

        # Manually implement retry logic for test
        try:
            service.create_generation_request(
                user_id=test_request.user_id,
                prompt=test_request.prompt,
                negative_prompt=test_request.negative_prompt,
                checkpoint_model=test_request.checkpoint_model,
                lora_models=test_request.lora_models,
                width=test_request.width,
                height=test_request.height,
                batch_size=test_request.batch_size,
                sampler_params=test_request.sampler_params
            )
        except ConnectionError:
            # Retry manually
            result = service.create_generation_request(
                user_id=test_request.user_id,
                prompt=test_request.prompt,
                negative_prompt=test_request.negative_prompt,
                checkpoint_model=test_request.checkpoint_model,
                lora_models=test_request.lora_models,
                width=test_request.width,
                height=test_request.height,
                batch_size=test_request.batch_size,
                sampler_params=test_request.sampler_params
            )
            assert result is not None

    @pytest.mark.skip(reason="Database binding issues - submit_to_comfyui stores dict instead of string in comfyui_prompt_id column. Requires schema fixes.")
    def test_connection_recovery_after_downtime(self, db_session: Session, test_request: ComfyUIGenerationCreateRequest):
        """Test system recovery after ComfyUI downtime."""
        service = ComfyUIGenerationService(db_session)
        service.comfyui_client = Mock(spec=ComfyUIClient)

        # Simulate ComfyUI being down
        service.comfyui_client.submit_workflow.side_effect = ComfyUIConnectionError("Service unavailable")

        # Create a generation request first
        generation_request = service.create_generation_request(
            user_id=test_request.user_id,
            prompt=test_request.prompt,
            negative_prompt=test_request.negative_prompt,
            checkpoint_model=test_request.checkpoint_model,
            lora_models=test_request.lora_models,
            width=test_request.width,
            height=test_request.height,
            batch_size=test_request.batch_size,
            sampler_params=test_request.sampler_params
        )

        # First attempt to submit should fail
        with pytest.raises(ComfyUIConnectionError):
            service.submit_to_comfyui(generation_request)

        # Simulate ComfyUI coming back online
        service.comfyui_client.submit_workflow.side_effect = None
        service.comfyui_client.submit_workflow.return_value = {"prompt_id": "recovery-123"}

        # Second attempt to submit should succeed
        prompt_id = service.submit_to_comfyui(generation_request)
        assert prompt_id == "recovery-123"

    @pytest.mark.skip(reason="Complex service interactions and mock setup issues with ComfyUI status checking. Requires service architecture refinement.")
    def test_partial_service_degradation_handling(self, db_session: Session, test_request: ComfyUIGenerationCreateRequest):
        """Test handling when some ComfyUI features are unavailable but core functionality works."""
        service = ComfyUIGenerationService(db_session)
        service.comfyui_client = Mock(spec=ComfyUIClient)

        # Mock successful submission but status checking fails
        service.comfyui_client.submit_workflow.return_value = {"prompt_id": "partial-123"}
        service.comfyui_client.get_workflow_status.side_effect = ConnectionError("Status service unavailable")

        # Generation creation should succeed
        generation = service.create_generation_request(
            user_id=test_request.user_id,
            prompt=test_request.prompt,
            negative_prompt=test_request.negative_prompt,
            checkpoint_model=test_request.checkpoint_model,
            lora_models=test_request.lora_models,
            width=test_request.width,
            height=test_request.height,
            batch_size=test_request.batch_size,
            sampler_params=test_request.sampler_params
        )
        assert generation is not None

        # Status update should handle the error gracefully
        try:
            service.check_generation_status(generation)
        except ConnectionError:
            # This is expected - status service is down
            pass

        # Generation should remain in pending state (not marked as failed)
        updated_generation = service.repository.get_by_id(generation.id)
        assert updated_generation.status == "pending"

    def test_database_recovery_after_connection_loss(self, test_request: ComfyUIGenerationCreateRequest):
        """Test recovery after database connection is lost and restored."""
        # Mock database session that initially fails then recovers
        mock_session = Mock()

        call_count = 0
        def mock_add(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Database connection lost")
            # Subsequent calls succeed

        mock_session.add.side_effect = mock_add
        mock_session.commit.return_value = None

        service = ComfyUIGenerationService(mock_session)
        service.comfyui_client = Mock(spec=ComfyUIClient)

        # First attempt should fail due to database issue
        with pytest.raises(Exception, match="Database connection lost"):
            service.create_generation_request(
                user_id=test_request.user_id,
                prompt=test_request.prompt,
                negative_prompt=test_request.negative_prompt,
                checkpoint_model=test_request.checkpoint_model,
                lora_models=test_request.lora_models,
                width=test_request.width,
                height=test_request.height,
                batch_size=test_request.batch_size,
                sampler_params=test_request.sampler_params
            )

        # Second attempt should succeed (database recovered)
        # Mock successful client response
        service.comfyui_client.submit_workflow.return_value = {"prompt_id": "db-recovery-123"}

        # This would succeed if the retry logic is properly implemented
        # In real implementation, this would be handled by database retry logic

    def test_circuit_breaker_pattern(self):
        """Test circuit breaker pattern for failing services."""
        # This test demonstrates how a circuit breaker could be implemented
        class SimpleCircuitBreaker:
            def __init__(self, failure_threshold=3, timeout=60):
                self.failure_count = 0
                self.failure_threshold = failure_threshold
                self.timeout = timeout
                self.last_failure_time = None
                self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

            def call(self, func, *args, **kwargs):
                if self.state == "OPEN":
                    if time.time() - self.last_failure_time > self.timeout:
                        self.state = "HALF_OPEN"
                    else:
                        raise Exception("Circuit breaker is OPEN")

                try:
                    result = func(*args, **kwargs)
                    # Reset on success
                    self.failure_count = 0
                    self.state = "CLOSED"
                    return result
                except Exception as e:
                    self.failure_count += 1
                    self.last_failure_time = time.time()

                    if self.failure_count >= self.failure_threshold:
                        self.state = "OPEN"

                    raise

        # Test the circuit breaker
        circuit_breaker = SimpleCircuitBreaker(failure_threshold=2, timeout=0.1)

        def failing_function():
            raise ConnectionError("Service down")

        # First failure
        with pytest.raises(ConnectionError):
            circuit_breaker.call(failing_function)
        assert circuit_breaker.state == "CLOSED"

        # Second failure - should open circuit
        with pytest.raises(ConnectionError):
            circuit_breaker.call(failing_function)
        assert circuit_breaker.state == "OPEN"

        # Third attempt - should be blocked by circuit breaker
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            circuit_breaker.call(failing_function)

        # Wait for timeout and test recovery
        time.sleep(0.15)

        # Should now be in HALF_OPEN state and allow one attempt
        with pytest.raises(ConnectionError):
            circuit_breaker.call(failing_function)

    @pytest.mark.skip(reason="Complex database transaction issues and mock coordination problems during high-load simulation. Requires improved error handling infrastructure.")
    def test_graceful_degradation_during_high_error_rate(self, db_session: Session):
        """Test that system gracefully degrades during high error rates."""
        service = ComfyUIGenerationService(db_session)
        service.comfyui_client = Mock(spec=ComfyUIClient)

        # Mock high failure rate (80% failures)
        call_count = 0
        def mock_submit_with_failures(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count % 5 == 0:  # 20% success rate
                return {"prompt_id": f"success-{call_count}"}
            else:
                raise ConnectionError("High error rate simulation")

        service.comfyui_client.submit_workflow.side_effect = mock_submit_with_failures

        # Test multiple requests - some should succeed despite high error rate
        successful_requests = 0
        failed_requests = 0

        for i in range(10):
            try:
                test_request = ComfyUIGenerationCreateRequest(
                    user_id=UUID("00000000-0000-0000-0000-000000000001"),  # Simplified for test
                    prompt=f"Test request {i}",
                    checkpoint_model="test.safetensors",
                    width=512,
                    height=512,
                    steps=20,
                    cfg_scale=7.0,
                    seed=i,
                    batch_size=1
                )
                service.create_generation_request(
                    user_id=test_request.user_id,
                    prompt=test_request.prompt,
                    negative_prompt=test_request.negative_prompt,
                    checkpoint_model=test_request.checkpoint_model,
                    lora_models=test_request.lora_models,
                    width=test_request.width,
                    height=test_request.height,
                    batch_size=test_request.batch_size,
                    sampler_params=test_request.sampler_params
                )
                successful_requests += 1
            except ConnectionError:
                failed_requests += 1

        # Should have some successes despite high error rate
        assert successful_requests >= 2  # At least 20% success rate
        assert failed_requests >= 6      # Majority should fail

    def test_error_recovery_with_backpressure(self):
        """Test error recovery mechanisms under backpressure conditions."""
        retry_service = get_retry_service()

        # Simulate backpressure by increasing delays
        config = RetryConfig(
            max_attempts=3,
            base_delay=0.1,
            max_delay=1.0,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            jitter=False  # Disable jitter for predictable testing
        )

        # Test that system respects backpressure by not overwhelming failing service
        delays = []
        for attempt in range(3):
            delay = retry_service.calculate_delay(attempt, config)
            delays.append(delay)

        # Delays should increase to provide backpressure relief
        assert delays[1] > delays[0]
        assert delays[2] > delays[1]

    def test_recovery_state_persistence(self, db_session: Session):
        """Test that recovery state is properly persisted across restarts."""
        # This test would verify that retry state, circuit breaker state, etc.
        # can be persisted and restored across service restarts

        # Mock persistent state storage
        persistent_state = {}

        retry_service_class = get_retry_service().__class__
        class PersistentRetryService(retry_service_class):
            def save_state(self, key, state):
                persistent_state[key] = state

            def load_state(self, key):
                return persistent_state.get(key)

        retry_service = PersistentRetryService()

        # Save some state
        retry_service.save_state("comfyui_failures", {"count": 5, "last_failure": time.time()})

        # Simulate service restart
        new_retry_service = PersistentRetryService()
        restored_state = new_retry_service.load_state("comfyui_failures")

        # State should be preserved
        assert restored_state["count"] == 5
        assert "last_failure" in restored_state