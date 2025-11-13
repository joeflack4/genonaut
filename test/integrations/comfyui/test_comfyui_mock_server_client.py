"""Tests for ComfyUIClient integration with mock server."""

import pytest
from genonaut.api.services.comfyui_client import ComfyUIClient, ComfyUIConnectionError, ComfyUIWorkflowError


class TestComfyUIClientIntegration:
    """Test ComfyUIClient against mock server."""

    def test_submit_workflow(self, mock_comfyui_client: ComfyUIClient):
        """Test submitting workflow to mock server."""
        workflow = {
            "1": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "test_checkpoint.safetensors"}
            },
            "2": {
                "class_type": "SaveImage",
                "inputs": {"filename_prefix": "test_submit"}
            }
        }

        prompt_id = mock_comfyui_client.submit_workflow(workflow)

        assert prompt_id is not None
        assert len(prompt_id) > 0
        assert isinstance(prompt_id, str)

    @pytest.mark.longrunning
    @pytest.mark.comfyui_poll
    def test_get_workflow_status_completed(self, mock_comfyui_client: ComfyUIClient):
        """Test getting workflow status for completed job."""
        workflow = {
            "1": {"class_type": "SaveImage", "inputs": {"filename_prefix": "status_test"}}
        }

        prompt_id = mock_comfyui_client.submit_workflow(workflow)

        # Wait for completion since mock server now has processing delay
        result = mock_comfyui_client.wait_for_completion(prompt_id, max_wait_time=10)

        # Now get status to verify it shows completed
        status = mock_comfyui_client.get_workflow_status(prompt_id)

        assert status["status"] == "completed"
        assert status["prompt_id"] == prompt_id
        assert "outputs" in status
        assert len(status["outputs"]) > 0

    @pytest.mark.longrunning
    @pytest.mark.comfyui_poll
    def test_wait_for_completion(self, mock_comfyui_client: ComfyUIClient):
        """Test waiting for workflow completion."""
        workflow = {
            "1": {"class_type": "SaveImage", "inputs": {"filename_prefix": "wait_test"}}
        }

        prompt_id = mock_comfyui_client.submit_workflow(workflow)
        result = mock_comfyui_client.wait_for_completion(prompt_id, max_wait_time=10)

        assert result["status"] == "completed"
        assert "outputs" in result

    def test_cancel_workflow(self, mock_comfyui_client: ComfyUIClient):
        """Test canceling a workflow."""
        result = mock_comfyui_client.cancel_workflow("any-prompt-id")
        assert result is True

    def test_get_available_models(self, mock_comfyui_client: ComfyUIClient):
        """Test getting available models from mock server."""
        models = mock_comfyui_client.get_available_models()

        assert "checkpoints" in models
        assert "loras" in models
        assert len(models["checkpoints"]) > 0
        assert len(models["loras"]) > 0

    @pytest.mark.longrunning
    @pytest.mark.comfyui_poll
    def test_get_output_files(self, mock_comfyui_client_dynamic: ComfyUIClient):
        """Test extracting output files from workflow result."""
        mock_comfyui_client = mock_comfyui_client_dynamic  # Alias for minimal changes
        workflow = {
            "1": {"class_type": "SaveImage", "inputs": {"filename_prefix": "output_test"}}
        }

        prompt_id = mock_comfyui_client.submit_workflow(workflow)
        result = mock_comfyui_client.wait_for_completion(prompt_id, max_wait_time=10)

        output_files = mock_comfyui_client.get_output_files(result["outputs"])

        assert len(output_files) > 0
        assert all("output_test" in path for path in output_files)

    @pytest.mark.longrunning
    @pytest.mark.comfyui_poll
    def test_workflow_with_client_id(self, mock_comfyui_client: ComfyUIClient):
        """Test submitting workflow with custom client_id."""
        workflow = {
            "1": {"class_type": "SaveImage", "inputs": {"filename_prefix": "client_id_test"}}
        }

        prompt_id = mock_comfyui_client.submit_workflow(workflow, client_id="custom-client-123")

        assert prompt_id is not None

        # Wait for completion since mock server now has processing delay
        result = mock_comfyui_client.wait_for_completion(prompt_id, max_wait_time=10)

        # Verify status is completed
        status = mock_comfyui_client.get_workflow_status(prompt_id)
        assert status["status"] == "completed"

    @pytest.mark.longrunning
    def test_health_check(self, mock_comfyui_client: ComfyUIClient):
        """Test health check against mock server."""
        is_healthy = mock_comfyui_client.health_check()
        assert is_healthy is True
