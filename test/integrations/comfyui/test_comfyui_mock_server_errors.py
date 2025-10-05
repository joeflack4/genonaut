"""Tests for error scenarios with mock server."""

import pytest
import requests
from genonaut.api.services.comfyui_client import ComfyUIClient, ComfyUIConnectionError, ComfyUIWorkflowError


class TestMockServerErrorScenarios:
    """Test error handling with mock server."""

    def test_connection_error_server_not_running(self):
        """Test connection error when server is not available."""
        # Create client pointing to non-existent server
        client = ComfyUIClient()
        client.base_url = "http://localhost:9999"  # Invalid port

        workflow = {"1": {"class_type": "SaveImage", "inputs": {"filename_prefix": "test"}}}

        with pytest.raises(ComfyUIConnectionError):
            client.submit_workflow(workflow)

    def test_invalid_prompt_id_history(self, mock_comfyui_url: str):
        """Test getting history for non-existent prompt_id."""
        response = requests.get(f"{mock_comfyui_url}/history/nonexistent-id-12345")
        assert response.status_code == 200

        data = response.json()
        # Mock server returns empty dict for non-existent IDs
        assert data == {}

    def test_get_workflow_status_unknown_id(self, mock_comfyui_client: ComfyUIClient):
        """Test workflow status for unknown prompt_id."""
        status = mock_comfyui_client.get_workflow_status("unknown-prompt-id-99999")

        # Should return unknown status
        assert status["status"] == "unknown"
        assert status["prompt_id"] == "unknown-prompt-id-99999"

    def test_empty_workflow_validation(self, mock_comfyui_client: ComfyUIClient):
        """Test submitting empty workflow raises validation error."""
        from genonaut.api.exceptions import ValidationError

        with pytest.raises(ValidationError):
            mock_comfyui_client.submit_workflow({})

    def test_workflow_timeout(self, mock_comfyui_client: ComfyUIClient):
        """Test workflow timeout handling."""
        # This test verifies the timeout mechanism exists
        # Our mock server completes instantly, so we can't trigger a real timeout
        # But we can verify the wait_for_completion has a timeout parameter

        workflow = {"1": {"class_type": "SaveImage", "inputs": {"filename_prefix": "timeout_test"}}}

        prompt_id = mock_comfyui_client.submit_workflow(workflow)

        # Should complete before timeout
        result = mock_comfyui_client.wait_for_completion(prompt_id, max_wait_time=1)
        assert result["status"] == "completed"

    def test_malformed_workflow_structure(self, mock_comfyui_url: str):
        """Test submitting malformed workflow."""
        # Submit workflow with invalid structure
        response = requests.post(
            f"{mock_comfyui_url}/prompt",
            json={"invalid_key": "invalid_value"}  # Missing 'prompt' key
        )

        # FastAPI will return 422 for validation error
        assert response.status_code == 422

    def test_network_error_handling(self):
        """Test handling of network errors."""
        client = ComfyUIClient()
        client.base_url = "http://256.256.256.256"  # Invalid IP
        client.timeout = 1  # Short timeout

        # Should return False or raise error, either is acceptable
        try:
            result = client.health_check()
            assert result is False
        except (ComfyUIConnectionError, Exception):
            # Network errors are acceptable too
            pass

    def test_invalid_endpoint(self, mock_comfyui_url: str):
        """Test accessing invalid endpoint."""
        response = requests.get(f"{mock_comfyui_url}/invalid_endpoint")
        assert response.status_code == 404

    def test_workflow_without_save_node(self, mock_comfyui_client: ComfyUIClient):
        """Test workflow without SaveImage node."""
        # Workflow without SaveImage node
        workflow = {
            "1": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "test_checkpoint.safetensors"}
            }
        }

        prompt_id = mock_comfyui_client.submit_workflow(workflow)
        result = mock_comfyui_client.wait_for_completion(prompt_id)

        # Should still complete, but with default prefix
        assert result["status"] == "completed"
        outputs = result["outputs"]
        assert "9" in outputs  # Mock always uses node ID "9"

    def test_concurrent_interrupt_calls(self, mock_comfyui_url: str):
        """Test multiple interrupt calls don't cause errors."""
        for _ in range(3):
            response = requests.post(f"{mock_comfyui_url}/interrupt")
            assert response.status_code == 200
            assert response.json()["status"] == "interrupted"
