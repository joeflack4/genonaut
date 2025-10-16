"""Integration tests for user experience during error conditions.

This test suite validates that users receive appropriate feedback, guidance,
and recovery options when errors occur in the ComfyUI generation system.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from fastapi import status

from genonaut.api.main import app
from genonaut.api.services.comfyui_generation_service import ComfyUIGenerationService
from genonaut.api.services.comfyui_client import ComfyUIConnectionError
from genonaut.api.services.error_service import ErrorService
from genonaut.api.models.requests import ComfyUIGenerationCreateRequest
from genonaut.db.schema import User, GenerationJob, AvailableModel


class TestUserErrorExperience:
    """Test user experience during various error conditions."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    @pytest.fixture
    def test_user(self, db_session: Session) -> User:
        """Create a test user."""
        user = User(
            username="ux_test_user",
            email="uxtest@example.com",
            created_at=datetime.utcnow()
        )
        db_session.add(user)
        db_session.commit()
        return user

    @pytest.fixture
    def test_model(self, db_session: Session) -> AvailableModel:
        """Create a test model."""
        model = AvailableModel(
            name="ux_test_model.safetensors",
            type="checkpoint",
            file_path="/models/checkpoints/ux_test_model.safetensors",
            is_active=True,
            created_at=datetime.utcnow()
        )
        db_session.add(model)
        db_session.commit()
        return model

    @pytest.mark.skip(reason="Skipped until API endpoints implemented")
    def test_api_error_response_structure(self, client: TestClient, test_user: User, test_model: AvailableModel):
        """Test that API error responses have consistent, user-friendly structure."""
        # Mock ComfyUI connection error
        with patch('genonaut.api.services.comfyui_generation_service.ComfyUIGenerationService.create_generation') as mock_create:
            mock_create.side_effect = ComfyUIConnectionError("Connection failed")

            # Make request that will trigger error
            response = client.post("/api/comfyui/generations", json={
                "user_id": str(test_user.id),
                "prompt": "Test prompt",
                "checkpoint_model": test_model.name,
                "width": 512,
                "height": 512,
                "steps": 20,
                "cfg_scale": 7.0,
                "seed": 42,
                "batch_size": 1
            })

            # Verify error response structure
            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            error_data = response.json()

            # Should have user-friendly error structure
            assert "error" in error_data
            assert "message" in error_data["error"]
            assert "category" in error_data["error"]
            assert "retry_after" in error_data["error"]
            assert "support_info" in error_data["error"]

            # Message should be user-friendly, not technical
            message = error_data["error"]["message"]
            assert "service" in message.lower()
            assert "try again" in message.lower()
            assert "127.0.0.1" not in message  # No technical details
            assert "connection failed" not in message.lower()  # No raw error

    @pytest.mark.skip(reason="Skipped until API endpoints implemented")
    def test_validation_error_user_feedback(self, client: TestClient, test_user: User, test_model: AvailableModel):
        """Test that validation errors provide clear guidance to users."""
        # Send request with invalid parameters
        response = client.post("/api/comfyui/generations", json={
            "user_id": str(test_user.id),
            "prompt": "",  # Empty prompt
            "checkpoint_model": test_model.name,
            "width": -1,   # Invalid width
            "height": 0,   # Invalid height
            "steps": 0,    # Invalid steps
            "cfg_scale": -1,  # Invalid CFG scale
            "seed": "invalid",  # Invalid seed type
            "batch_size": 0    # Invalid batch size
        })

        # Should return validation error
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        error_data = response.json()

        # Should provide specific guidance for each validation error
        assert "detail" in error_data
        validation_errors = error_data["detail"]

        # Check that errors are descriptive and helpful
        error_messages = [error["msg"] for error in validation_errors]

        # Should not just say "validation error" but explain what's wrong
        width_errors = [msg for msg in error_messages if "width" in msg.lower()]
        assert len(width_errors) > 0
        assert any("positive" in msg.lower() for msg in width_errors)

    @pytest.mark.skip(reason="Skipped until API endpoints implemented")
    def test_model_not_found_error_guidance(self, client: TestClient, test_user: User):
        """Test user guidance when requested model is not available."""
        response = client.post("/api/comfyui/generations", json={
            "user_id": str(test_user.id),
            "prompt": "Test prompt",
            "checkpoint_model": "nonexistent_model.safetensors",
            "width": 512,
            "height": 512,
            "steps": 20,
            "cfg_scale": 7.0,
            "seed": 42,
            "batch_size": 1
        })

        # Should return not found error
        assert response.status_code == status.HTTP_404_NOT_FOUND
        error_data = response.json()

        # Should provide helpful guidance
        assert "error" in error_data
        message = error_data["error"]["message"]
        assert "model" in message.lower()
        assert "available" in message.lower()

        # Should suggest next steps
        assert "suggestions" in error_data["error"]
        suggestions = error_data["error"]["suggestions"]
        assert len(suggestions) > 0
        assert any("list" in suggestion.lower() for suggestion in suggestions)

    @pytest.mark.skip(reason="Skipped until API endpoints implemented")
    def test_service_unavailable_error_experience(self, client: TestClient, test_user: User, test_model: AvailableModel):
        """Test user experience when ComfyUI service is unavailable."""
        with patch('genonaut.api.services.comfyui_client.ComfyUIClient.submit_workflow') as mock_submit:
            mock_submit.side_effect = ComfyUIConnectionError("Service unavailable")

            response = client.post("/api/comfyui/generations", json={
                "user_id": str(test_user.id),
                "prompt": "Test prompt",
                "checkpoint_model": test_model.name,
                "width": 512,
                "height": 512,
                "steps": 20,
                "cfg_scale": 7.0,
                "seed": 42,
                "batch_size": 1
            })

            # Should return service unavailable
            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            error_data = response.json()

            # Should provide clear explanation and next steps
            assert "error" in error_data
            message = error_data["error"]["message"]
            assert "temporarily unavailable" in message.lower()
            assert "try again" in message.lower()

            # Should provide retry guidance
            assert "retry_after" in error_data["error"]
            assert error_data["error"]["retry_after"] > 0

            # Should provide support information
            assert "support_info" in error_data["error"]
            support_info = error_data["error"]["support_info"]
            assert "status_page" in support_info or "contact" in support_info

    @pytest.mark.skip(reason="Skipped until rate limiting middleware implemented")
    def test_rate_limit_error_user_guidance(self, client: TestClient, test_user: User, test_model: AvailableModel):
        """Test user experience when rate limits are exceeded."""
        with patch('genonaut.api.middleware.rate_limiter.is_rate_limited') as mock_rate_limit:
            mock_rate_limit.return_value = True

            response = client.post("/api/comfyui/generations", json={
                "user_id": str(test_user.id),
                "prompt": "Test prompt",
                "checkpoint_model": test_model.name,
                "width": 512,
                "height": 512,
                "steps": 20,
                "cfg_scale": 7.0,
                "seed": 42,
                "batch_size": 1
            })

            # Should return rate limit error
            assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
            error_data = response.json()

            # Should explain rate limiting clearly
            assert "error" in error_data
            message = error_data["error"]["message"]
            assert "too many" in message.lower() or "rate limit" in message.lower()

            # Should provide specific timing guidance
            assert "retry_after" in error_data["error"]
            assert "rate_limit_info" in error_data["error"]
            rate_info = error_data["error"]["rate_limit_info"]
            assert "current_usage" in rate_info
            assert "limit" in rate_info
            assert "reset_time" in rate_info

    @pytest.mark.skip(reason="Skipped until API endpoints implemented")
    def test_generation_status_error_communication(self, client: TestClient, db_session: Session, test_user: User, test_model: AvailableModel):
        """Test how generation errors are communicated through status endpoints."""
        # Create a failed generation
        failed_generation = GenerationJob(
            creator_id=test_user.id,
            content_type="image",
            content_data="path/to/test.jpg",
            prompt="Test failed generation",
            checkpoint_model=test_model.name,
            width=512,
            height=512,
            steps=20,
            cfg_scale=7.0,
            seed=42,
            batch_size=1,
            status="failed",
            error_message="Generation failed due to insufficient VRAM",
            created_at=datetime.utcnow()
        )
        db_session.add(failed_generation)
        db_session.commit()

        # Request generation status
        response = client.get(f"/api/comfyui/generations/{failed_generation.id}")

        assert response.status_code == status.HTTP_200_OK
        generation_data = response.json()

        # Should clearly indicate failure
        assert generation_data["status"] == "failed"
        assert "error_message" in generation_data
        assert generation_data["error_message"] is not None

        # Error message should be user-friendly
        error_message = generation_data["error_message"]
        assert "VRAM" in error_message  # Technical term that users understand
        assert len(error_message) > 10  # Should be descriptive

        # Should provide recovery suggestions if available
        if "recovery_suggestions" in generation_data:
            suggestions = generation_data["recovery_suggestions"]
            assert isinstance(suggestions, list)
            assert len(suggestions) > 0

    def test_error_service_user_friendly_messages(self):
        """Test that error service generates appropriate user-friendly messages."""
        error_service = ErrorService()

        test_cases = [
            # (Technical Error, Expected User-Friendly Elements based on actual error service messages)
            (ComfyUIConnectionError("Failed to connect to 127.0.0.1:8000"),
             ["service", "temporarily", "unavailable", "try again", "minutes"]),

            (ConnectionError("Connection refused"),
             ["unable", "connect", "service", "check", "connection"]),

            (TimeoutError("Request timed out after 30 seconds"),
             ["timed out", "busy", "try again", "later"]),

            (ValueError("Invalid checkpoint model: model_xyz.safetensors"),
             ["invalid", "input", "check", "entries"]),

            (MemoryError("Insufficient VRAM for generation"),
             ["system", "memory", "try again", "later"]),

            (FileNotFoundError("Output file not found"),
             ["file", "resource", "not found"]),
        ]

        for technical_error, expected_elements in test_cases:
            error_info = error_service.handle_error(technical_error)
            message = error_info["user_message"].lower()

            # Should contain user-friendly elements
            for element in expected_elements:
                assert element in message, f"Expected '{element}' in message for {technical_error.__class__.__name__}"

            # Should not contain technical jargon
            technical_terms = ["127.0.0.1", "8000", "connection refused", "vram error", "file path"]
            for term in technical_terms:
                assert term not in message, f"Message should not contain technical term '{term}'"

    def test_error_recovery_guidance_by_category(self):
        """Test that different error categories provide appropriate recovery guidance."""
        error_service = ErrorService()

        # Connection errors should suggest retry with timing
        connection_error = ComfyUIConnectionError("Connection failed")
        error_info = error_service.handle_error(connection_error)

        assert error_info["can_retry"] is True
        assert error_info["retry_delay"] > 0
        assert error_info["category"] == "connection"
        assert "try again" in error_info["user_message"].lower()

        # Validation errors should not suggest retry with same params
        validation_error = ValueError("Invalid width parameter")
        error_info = error_service.handle_error(validation_error)

        assert error_info["can_retry"] is False  # Don't retry with same params
        assert error_info["category"] == "validation"
        assert "check" in error_info["user_message"].lower() or "invalid" in error_info["user_message"].lower()

        # System errors should suggest retry after delay
        system_error = MemoryError("Insufficient memory")
        error_info = error_service.handle_error(system_error)

        assert error_info["can_retry"] is True
        assert error_info["category"] == "system"
        assert "memory" in error_info["user_message"].lower()

    @pytest.mark.skip(reason="Skipped until enhanced error service features implemented")
    def test_progressive_error_disclosure(self):
        """Test that error information is disclosed progressively based on user needs."""
        error_service = ErrorService()

        # Basic error info for regular users
        error = ComfyUIConnectionError("Connection failed")
        basic_info = error_service.handle_error(error)

        assert "message" in basic_info
        assert "category" in basic_info
        assert "technical_details" not in basic_info  # Hidden from basic users

        # Advanced error info for power users
        advanced_info = error_service.handle_error(error)

        assert "message" in advanced_info
        assert "category" in advanced_info
        assert "technical_details" in advanced_info
        assert len(advanced_info["technical_details"]) > 0

        # Debug info for developers
        debug_info = error_service.handle_error(error)

        assert "message" in debug_info
        assert "technical_details" in debug_info
        assert "stack_trace" in debug_info
        assert "timestamp" in debug_info

    @pytest.mark.skip(reason="Skipped until enhanced error service features implemented")
    def test_error_help_links_and_documentation(self):
        """Test that errors provide links to relevant help and documentation."""
        error_service = ErrorService()

        # Different errors should link to different help sections
        test_cases = [
            (ComfyUIConnectionError("Connection failed"), "troubleshooting"),
            (ValueError("Invalid model"), "models"),
            (MemoryError("Out of memory"), "optimization"),
            (PermissionError("Access denied"), "setup"),
        ]

        for error, expected_help_section in test_cases:
            error_info = error_service.handle_error(error)

            assert "help_links" in error_info
            help_links = error_info["help_links"]
            assert len(help_links) > 0

            # Should have relevant help link
            relevant_link = any(expected_help_section in link["url"] for link in help_links)
            assert relevant_link, f"No relevant help link for {expected_help_section}"

            # Each link should have title and description
            for link in help_links:
                assert "title" in link
                assert "url" in link
                assert "description" in link

    @pytest.mark.skip(reason="Skipped until enhanced error service features implemented")
    def test_error_feedback_collection(self):
        """Test that the system can collect user feedback on error experiences."""
        error_service = ErrorService()

        # Error info should include feedback collection mechanism
        error = ComfyUIConnectionError("Connection failed")
        error_info = error_service.handle_error(error)

        assert "feedback" in error_info
        feedback_info = error_info["feedback"]

        assert "enabled" in feedback_info
        assert "methods" in feedback_info

        if feedback_info["enabled"]:
            methods = feedback_info["methods"]
            assert len(methods) > 0

            # Should support different feedback methods
            method_types = [method["type"] for method in methods]
            assert "rating" in method_types or "survey" in method_types

            # Each method should have clear instructions
            for method in methods:
                assert "type" in method
                assert "description" in method
                assert "endpoint" in method or "url" in method

    @pytest.mark.skip(reason="Skipped until enhanced error service features implemented")
    def test_error_analytics_and_trends(self):
        """Test that error information includes analytics for trend analysis."""
        error_service = ErrorService()

        # Should track error patterns for improvement
        error = ComfyUIConnectionError("Connection failed")

        # Simulate multiple occurrences
        for _ in range(5):
            error_service.handle_error(error, user_id="1")

        # Get error statistics
        error_stats = error_service.get_error_statistics(error.__class__.__name__)

        assert "frequency" in error_stats
        assert "recent_occurrences" in error_stats
        assert "affected_users" in error_stats
        assert "resolution_rate" in error_stats

        # Should provide trend information
        assert error_stats["frequency"] > 0
        assert error_stats["recent_occurrences"] >= 5

    @pytest.mark.skip(reason="Skipped until multilingual support implemented")
    def test_multilingual_error_messages(self):
        """Test support for multilingual error messages."""
        error_service = ErrorService()

        error = ComfyUIConnectionError("Connection failed")

        # Test different language support
        languages = ["en", "es", "fr", "de", "ja"]

        for lang in languages:
            error_info = error_service.handle_error(error)

            # Should have message in requested language
            assert "message" in error_info
            assert len(error_info["user_message"]) > 0

            # Should indicate the language used
            assert "language" in error_info
            assert error_info["language"] == lang

            # Fallback to English if translation not available
            if error_info["language"] != lang:
                assert error_info["language"] == "en"  # Fallback language

    @pytest.mark.skip(reason="Skipped until accessibility features implemented")
    def test_accessibility_in_error_communication(self):
        """Test that error communication supports accessibility requirements."""
        error_service = ErrorService()

        error = ComfyUIConnectionError("Connection failed")
        error_info = error_service.handle_error(error)

        # Should include accessibility-friendly content
        assert "accessibility" in error_info
        accessibility_info = error_info["accessibility"]

        # Should have screen reader friendly text
        assert "screen_reader_text" in accessibility_info
        assert len(accessibility_info["screen_reader_text"]) > 0

        # Should have semantic markup suggestions
        assert "semantic_level" in accessibility_info
        assert accessibility_info["semantic_level"] in ["error", "warning", "alert"]

        # Should have ARIA attributes suggestions
        assert "aria_attributes" in accessibility_info
        aria_attrs = accessibility_info["aria_attributes"]
        assert "role" in aria_attrs
        assert "aria-live" in aria_attrs

    @pytest.mark.skip(reason="Skipped until enhanced error service features implemented")
    def test_error_context_preservation(self):
        """Test that error context is preserved for better user understanding."""
        error_service = ErrorService()

        # Create error with context
        context = {
            "user_action": "create_generation",
            "parameters": {"width": 512, "height": 512, "model": "test.safetensors"},
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": "test-session-123"
        }

        error = ComfyUIConnectionError("Connection failed")
        error_info = error_service.handle_error(error, context=context)

        # Should preserve relevant context
        assert "context" in error_info
        error_context = error_info["context"]

        assert "user_action" in error_context
        assert error_context["user_action"] == "create_generation"

        # Should sanitize sensitive information
        assert "session_id" not in error_context  # Sensitive info removed

        # Should include relevant parameters for troubleshooting
        if "parameters" in error_context:
            params = error_context["parameters"]
            assert "model" in params  # Relevant for troubleshooting
            # But sensitive params should be removed or masked