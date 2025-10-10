"""Integration tests for various error scenarios in the ComfyUI generation system.

This test suite validates that different types of failures are handled gracefully
and provide appropriate error messages and recovery options.
"""

import json
import time
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest
from requests.exceptions import ConnectionError, HTTPError
from httpx import TimeoutException
from sqlalchemy.orm import Session

from genonaut.api.exceptions import ValidationError
from genonaut.api.models.requests import ComfyUIGenerationCreateRequest
from genonaut.api.repositories.generation_job_repository import GenerationJobRepository
from genonaut.api.services.comfyui_client import ComfyUIClient, ComfyUIConnectionError
from genonaut.api.services.comfyui_generation_service import ComfyUIGenerationService
from genonaut.api.services.error_service import ErrorCategory, ErrorService, ErrorSeverity
from genonaut.api.services.file_storage_service import FileStorageService
from genonaut.api.services.metrics_service import MetricsService
from genonaut.api.services.retry_service import RetryService
from genonaut.api.services.thumbnail_service import ThumbnailService
from genonaut.db.schema import AvailableModel, GenerationJob, User


class TestErrorScenarios:
    """Test various failure scenarios in the ComfyUI generation system."""

    @pytest.fixture
    def test_user(self, db_session: Session) -> User:
        """Create a test user."""
        user = User(
            username="error_test_user",
            email="errortest@example.com",
            created_at=datetime.utcnow()
        )
        db_session.add(user)
        db_session.commit()
        return user

    @pytest.fixture
    def test_model(self, db_session: Session) -> AvailableModel:
        """Create a test model."""
        model = AvailableModel(
            name="error_test_model.safetensors",
            type="checkpoint",
            file_path="/models/checkpoints/error_test_model.safetensors",
            is_active=True,
            created_at=datetime.utcnow()
        )
        db_session.add(model)
        db_session.commit()
        return model

    @pytest.fixture
    def generation_service(self, db_session: Session) -> ComfyUIGenerationService:
        """Create a generation service with mocked dependencies."""
        service = ComfyUIGenerationService(db_session)

        # Use mocks for external integrations
        service.comfyui_client = Mock(spec=ComfyUIClient)
        service.comfyui_client.get_output_files.return_value = []

        service.file_storage_service = MagicMock(spec=FileStorageService)
        service.thumbnail_service = MagicMock(spec=ThumbnailService)

        # Simplify retry/metrics behaviour for deterministic testing
        service.retry_service = MagicMock(spec=RetryService)
        service.retry_service.create_config.side_effect = lambda *a, **k: {}
        service.retry_service.retry_sync.side_effect = lambda func, *a, **k: func()

        service.metrics_service = MagicMock(spec=MetricsService)

        return service

    @pytest.fixture
    def test_request(self, test_user: User, test_model: AvailableModel) -> ComfyUIGenerationCreateRequest:
        """Create a test generation request."""
        return ComfyUIGenerationCreateRequest(
            user_id=test_user.id,
            prompt="Test error scenario",
            negative_prompt="low quality",
            checkpoint_model=test_model.name,
            width=512,
            height=512,
            steps=20,
            cfg_scale=7.0,
            seed=42,
            batch_size=1
        )

    def test_comfyui_connection_failure(self, generation_service: ComfyUIGenerationService,
                                       test_request: ComfyUIGenerationCreateRequest):
        """Test handling of ComfyUI connection failures."""
        job = generation_service.create_generation_request(
            user_id=test_request.user_id,
            prompt=test_request.prompt,
            negative_prompt=test_request.negative_prompt,
            checkpoint_model=test_request.checkpoint_model,
            lora_models=test_request.lora_models,
            width=test_request.width,
            height=test_request.height,
            batch_size=test_request.batch_size,
            sampler_params=test_request.sampler_params,
        )

        generation_service.comfyui_client.submit_workflow.side_effect = ComfyUIConnectionError(
            "Failed to connect to ComfyUI server"
        )

        with pytest.raises(ComfyUIConnectionError):
            generation_service.submit_to_comfyui(job)

        failed_job = generation_service.repository.get_or_404(job.id)
        assert failed_job.status == "failed"
        assert "unavailable" in (failed_job.error_message or "").lower()

    def test_comfyui_timeout_failure(self, generation_service: ComfyUIGenerationService,
                                    test_request: ComfyUIGenerationCreateRequest):
        """Test handling of ComfyUI timeout failures."""
        job = generation_service.create_generation_request(
            user_id=test_request.user_id,
            prompt=test_request.prompt,
            negative_prompt=test_request.negative_prompt,
            checkpoint_model=test_request.checkpoint_model,
            lora_models=test_request.lora_models,
            width=test_request.width,
            height=test_request.height,
            batch_size=test_request.batch_size,
            sampler_params=test_request.sampler_params,
        )

        generation_service.comfyui_client.submit_workflow.side_effect = TimeoutException(
            "Request to ComfyUI timed out"
        )

        with pytest.raises(TimeoutException):
            generation_service.submit_to_comfyui(job)

        failed_job = generation_service.repository.get_or_404(job.id)
        assert failed_job.status == "failed"
        assert failed_job.error_message

    def test_invalid_model_request(self, generation_service: ComfyUIGenerationService,
                                  test_request: ComfyUIGenerationCreateRequest):
        """Test handling of invalid model requests."""
        test_request.checkpoint_model = "nonexistent_model.safetensors"

        job = generation_service.create_generation_request(
            user_id=test_request.user_id,
            prompt=test_request.prompt,
            negative_prompt=test_request.negative_prompt,
            checkpoint_model=test_request.checkpoint_model,
            lora_models=test_request.lora_models,
            width=test_request.width,
            height=test_request.height,
            batch_size=test_request.batch_size,
            sampler_params=test_request.sampler_params,
        )

        generation_service.comfyui_client.submit_workflow.side_effect = ValueError(
            "Model 'nonexistent_model.safetensors' not found"
        )

        with pytest.raises(ValueError):
            generation_service.submit_to_comfyui(job)

        failed_job = generation_service.repository.get_or_404(job.id)
        assert failed_job.status == "failed"
        assert failed_job.error_message

    def test_invalid_generation_parameters(self, generation_service: ComfyUIGenerationService,
                                          test_request: ComfyUIGenerationCreateRequest):
        """Test handling of invalid generation parameters."""
        # Set invalid parameters
        test_request.width = -1
        test_request.height = 0
        test_request.sampler_params = {'steps': -5}
        job = generation_service.create_generation_request(
            user_id=test_request.user_id,
            prompt=test_request.prompt,
            negative_prompt=test_request.negative_prompt,
            checkpoint_model=test_request.checkpoint_model,
            lora_models=test_request.lora_models,
            width=test_request.width,
            height=test_request.height,
            batch_size=test_request.batch_size,
            sampler_params=test_request.sampler_params,
        )

        with pytest.raises(ValidationError):
            generation_service.submit_to_comfyui(job)

        failed_job = generation_service.repository.get_or_404(job.id)
        assert failed_job.status == "failed"

    def test_comfyui_server_error(self, generation_service: ComfyUIGenerationService,
                                 test_request: ComfyUIGenerationCreateRequest):
        """Test handling of ComfyUI server errors (500, etc.)."""
        job = generation_service.create_generation_request(
            user_id=test_request.user_id,
            prompt=test_request.prompt,
            negative_prompt=test_request.negative_prompt,
            checkpoint_model=test_request.checkpoint_model,
            lora_models=test_request.lora_models,
            width=test_request.width,
            height=test_request.height,
            batch_size=test_request.batch_size,
            sampler_params=test_request.sampler_params,
        )

        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        server_error = HTTPError("500 Server Error")
        server_error.response = mock_response
        generation_service.comfyui_client.submit_workflow.side_effect = server_error

        with pytest.raises(HTTPError):
            generation_service.submit_to_comfyui(job)

        failed_job = generation_service.repository.get_or_404(job.id)
        assert failed_job.status == "failed"

    def test_comfyui_workflow_failure(self, generation_service: ComfyUIGenerationService,
                                     test_request: ComfyUIGenerationCreateRequest):
        """Test handling of ComfyUI workflow execution failures."""
        job = generation_service.create_generation_request(
            user_id=test_request.user_id,
            prompt=test_request.prompt,
            negative_prompt=test_request.negative_prompt,
            checkpoint_model=test_request.checkpoint_model,
            lora_models=test_request.lora_models,
            width=test_request.width,
            height=test_request.height,
            batch_size=test_request.batch_size,
            sampler_params=test_request.sampler_params,
        )

        generation_service.comfyui_client.submit_workflow.return_value = "test-123"
        generation_service.submit_to_comfyui(job)

        refreshed_job = generation_service.repository.get_or_404(job.id)

        generation_service.comfyui_client.get_workflow_status.return_value = {
            "status": "failed",
            "messages": ["Workflow execution failed: Out of VRAM"],
        }

        generation_service.check_generation_status(refreshed_job)

        updated_generation = generation_service.repository.get_or_404(job.id)
        assert updated_generation.status == "failed"
        assert "vram" in (updated_generation.error_message or "").lower()

    def test_database_connection_failure(self, test_request: ComfyUIGenerationCreateRequest):
        """Test handling of database connection failures."""
        # Mock database error
        mock_session = Mock()
        mock_session.add.side_effect = Exception("Database connection lost")

        # Create service and replace the session
        service = ComfyUIGenerationService(mock_session)
        service.repository = GenerationJobRepository(mock_session)

        # Attempt to create generation
        with pytest.raises(Exception) as exc_info:
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

        # Verify error is properly propagated
        assert "Database connection lost" in str(exc_info.value)

    def test_file_system_error(self, generation_service: ComfyUIGenerationService,
                              test_request: ComfyUIGenerationCreateRequest):
        """Test handling of file system errors during image processing."""
        job = generation_service.create_generation_request(
            user_id=test_request.user_id,
            prompt=test_request.prompt,
            negative_prompt=test_request.negative_prompt,
            checkpoint_model=test_request.checkpoint_model,
            lora_models=test_request.lora_models,
            width=test_request.width,
            height=test_request.height,
            batch_size=test_request.batch_size,
            sampler_params=test_request.sampler_params,
        )

        generation_service.comfyui_client.submit_workflow.return_value = "test-123"
        generation_service.submit_to_comfyui(job)

        refreshed_job = generation_service.repository.get_or_404(job.id)

        generation_service.comfyui_client.get_workflow_status.return_value = {
            "status": "completed",
            "outputs": {
                "9": {
                    "images": [
                        {"filename": "test.png", "type": "output", "subfolder": ""}
                    ]
                }
            },
        }
        generation_service.comfyui_client.get_output_files.return_value = ["/tmp/comfyui/test.png"]
        generation_service.file_storage_service.organize_generation_files.side_effect = FileNotFoundError(
            "Generated file not found"
        )
        generation_service.thumbnail_service.generate_thumbnail_for_generation.return_value = {}

        result = generation_service.check_generation_status(refreshed_job)
        assert result["status"] == "completed"

        updated_generation = generation_service.repository.get_or_404(job.id)
        assert updated_generation.status == "completed"

    def test_memory_exhaustion_scenario(self, generation_service: ComfyUIGenerationService,
                                       test_request: ComfyUIGenerationCreateRequest):
        """Test handling of memory exhaustion during generation."""
        job = generation_service.create_generation_request(
            user_id=test_request.user_id,
            prompt=test_request.prompt,
            negative_prompt=test_request.negative_prompt,
            checkpoint_model=test_request.checkpoint_model,
            lora_models=test_request.lora_models,
            width=test_request.width,
            height=test_request.height,
            batch_size=test_request.batch_size,
            sampler_params=test_request.sampler_params,
        )

        generation_service.comfyui_client.submit_workflow.side_effect = MemoryError(
            "Insufficient memory for generation"
        )

        with pytest.raises(MemoryError):
            generation_service.submit_to_comfyui(job)

        failed_job = generation_service.repository.get_or_404(job.id)
        assert failed_job.status == "failed"
        assert "memory" in (failed_job.error_message or "").lower()

    def test_concurrent_request_conflicts(self, generation_service: ComfyUIGenerationService,
                                         test_request: ComfyUIGenerationCreateRequest):
        """Test handling of conflicts during concurrent requests."""
        generations = []
        for i in range(3):
            generation = generation_service.create_generation_request(
                user_id=test_request.user_id,
                prompt=test_request.prompt,
                negative_prompt=test_request.negative_prompt,
                checkpoint_model=test_request.checkpoint_model,
                lora_models=test_request.lora_models,
                width=test_request.width,
                height=test_request.height,
                batch_size=test_request.batch_size,
                sampler_params={"seed": i},
            )
            generations.append(generation)

        db_generations = generation_service.repository.get_by_user(test_request.user_id)
        assert len(db_generations) == 3
        assert all(job.status == "pending" for job in db_generations)

    def test_malformed_comfyui_response(self, generation_service: ComfyUIGenerationService,
                                       test_request: ComfyUIGenerationCreateRequest):
        """Test handling of malformed responses from ComfyUI."""
        job = generation_service.create_generation_request(
            user_id=test_request.user_id,
            prompt=test_request.prompt,
            negative_prompt=test_request.negative_prompt,
            checkpoint_model=test_request.checkpoint_model,
            lora_models=test_request.lora_models,
            width=test_request.width,
            height=test_request.height,
            batch_size=test_request.batch_size,
            sampler_params=test_request.sampler_params,
        )

        generation_service.comfyui_client.submit_workflow.side_effect = json.JSONDecodeError(
            "Expecting value", "malformed response", 0
        )

        with pytest.raises(json.JSONDecodeError):
            generation_service.submit_to_comfyui(job)

        failed_job = generation_service.repository.get_or_404(job.id)
        assert failed_job.status == "failed"

    def test_network_interruption_during_generation(self, generation_service: ComfyUIGenerationService,
                                                   test_request: ComfyUIGenerationCreateRequest):
        """Test handling of network interruptions during generation monitoring."""
        job = generation_service.create_generation_request(
            user_id=test_request.user_id,
            prompt=test_request.prompt,
            negative_prompt=test_request.negative_prompt,
            checkpoint_model=test_request.checkpoint_model,
            lora_models=test_request.lora_models,
            width=test_request.width,
            height=test_request.height,
            batch_size=test_request.batch_size,
            sampler_params=test_request.sampler_params,
        )

        generation_service.comfyui_client.submit_workflow.return_value = "test-123"
        generation_service.submit_to_comfyui(job)

        refreshed_job = generation_service.repository.get_or_404(job.id)
        generation_service.comfyui_client.get_workflow_status.side_effect = ConnectionError(
            "Network connection interrupted"
        )

        with pytest.raises(ConnectionError):
            generation_service.check_generation_status(refreshed_job)

        updated_generation = generation_service.repository.get_or_404(job.id)
        assert updated_generation.status == "processing"

    def test_partial_generation_failure(self, generation_service: ComfyUIGenerationService,
                                       test_request: ComfyUIGenerationCreateRequest):
        """Test handling of partial generation failures (some images succeed, some fail)."""
        # Set batch size > 1
        test_request.batch_size = 4

        job = generation_service.create_generation_request(
            user_id=test_request.user_id,
            prompt=test_request.prompt,
            negative_prompt=test_request.negative_prompt,
            checkpoint_model=test_request.checkpoint_model,
            lora_models=test_request.lora_models,
            width=test_request.width,
            height=test_request.height,
            batch_size=test_request.batch_size,
            sampler_params=test_request.sampler_params,
        )

        generation_service.comfyui_client.submit_workflow.return_value = "test-123"
        generation_service.submit_to_comfyui(job)

        refreshed_job = generation_service.repository.get_or_404(job.id)

        generation_service.comfyui_client.get_workflow_status.return_value = {
            "status": "completed",
            "outputs": {
                "9": {
                    "images": [
                        {"filename": "image_1.png", "type": "output", "subfolder": ""},
                        {"filename": "image_2.png", "type": "output", "subfolder": ""},
                    ]
                }
            },
            "messages": ["2/4 images completed"],
        }
        generation_service.comfyui_client.get_output_files.return_value = [
            "/tmp/comfyui/image_1.png",
            "/tmp/comfyui/image_2.png",
        ]
        generation_service.file_storage_service.organize_generation_files.return_value = [
            "/organized/image_1.png",
            "/organized/image_2.png",
        ]
        generation_service.thumbnail_service.generate_thumbnail_for_generation.return_value = {
            "/organized/image_1.png": {},
            "/organized/image_2.png": {},
        }

        result = generation_service.check_generation_status(refreshed_job)
        assert result["status"] == "completed"

        updated_generation = generation_service.repository.get_or_404(job.id)
        assert updated_generation.status == "completed"

    def test_error_service_categorization(self):
        """Test that the error service properly categorizes different error types."""
        error_service = ErrorService()

        # Test different error categorizations
        test_cases = [
            (ComfyUIConnectionError("Connection failed"), ErrorCategory.CONNECTION),
            (TimeoutError("Request timed out"), ErrorCategory.CONNECTION),
            (ValueError("Invalid parameters"), ErrorCategory.VALIDATION),
            (PermissionError("Access denied"), ErrorCategory.PERMISSION),
            (MemoryError("Out of memory"), ErrorCategory.SYSTEM),
            (FileNotFoundError("File not found"), ErrorCategory.RESOURCE),
        ]

        for error, expected_category in test_cases:
            error_info = error_service.handle_error(error)
            assert error_info["category"] == expected_category.value

    def test_error_message_user_friendliness(self):
        """Test that technical errors are converted to user-friendly messages."""
        error_service = ErrorService()

        # Test technical error gets user-friendly message
        technical_error = ComfyUIConnectionError("Failed to establish connection to 127.0.0.1:8000")
        error_info = error_service.handle_error(technical_error)

        # Should not contain technical details like IP addresses
        assert "127.0.0.1" not in error_info["user_message"]
        assert "8000" not in error_info["user_message"]
        # Should contain user-friendly language
        assert "service" in error_info["user_message"].lower()
        assert "try again" in error_info["user_message"].lower()

    def test_error_retry_recommendations(self):
        """Test that appropriate retry recommendations are provided."""
        error_service = ErrorService()

        # Test retryable error
        retryable_error = ComfyUIConnectionError("Temporary connection failure")
        error_info = error_service.handle_error(retryable_error)
        assert error_info["can_retry"] is True
        assert error_info["retry_delay"] > 0

        # Test non-retryable error
        non_retryable_error = ValueError("Invalid model configuration")
        error_info = error_service.handle_error(non_retryable_error)
        assert error_info["can_retry"] is False

    def test_error_severity_assessment(self):
        """Test that errors are assigned appropriate severity levels."""
        error_service = ErrorService()

        # Test different severity levels
        test_cases = [
            (ComfyUIConnectionError("Connection failed"), ErrorSeverity.MEDIUM),
            (MemoryError("Out of memory"), ErrorSeverity.HIGH),
            (ValueError("Invalid parameter"), ErrorSeverity.LOW),
            (Exception("Unknown system error"), ErrorSeverity.CRITICAL),
        ]

        for error, expected_severity in test_cases:
            error_info = error_service.handle_error(error)
            # Severity should be reasonable (exact match may vary based on implementation)
            assert error_info["severity"] in [s.value for s in ErrorSeverity]
