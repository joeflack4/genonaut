"""Basic tests for ComfyUI mock server functionality."""

import pytest
import requests
from pathlib import Path


class TestMockServerBasics:
    """Test basic mock server functionality."""

    def test_server_health_check(self, mock_comfyui_url: str):
        """Test server responds to health check."""
        response = requests.get(f"{mock_comfyui_url}/system_stats")
        assert response.status_code == 200

        data = response.json()
        assert "system" in data

    def test_server_root(self, mock_comfyui_url: str):
        """Test server root endpoint."""
        response = requests.get(mock_comfyui_url)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ok"
        assert "Mock ComfyUI Server" in data["server"]

    def test_submit_workflow(self, mock_comfyui_url: str):
        """Test workflow submission returns prompt_id."""
        workflow = {
            "1": {
                "class_type": "SaveImage",
                "inputs": {
                    "filename_prefix": "test_job"
                }
            }
        }

        response = requests.post(
            f"{mock_comfyui_url}/prompt",
            json={"prompt": workflow}
        )

        assert response.status_code == 200
        data = response.json()
        assert "prompt_id" in data
        assert len(data["prompt_id"]) > 0

    def test_get_history_pending(self, mock_comfyui_url: str):
        """Test getting history for pending job."""
        # Submit a job
        workflow = {"1": {"class_type": "SaveImage", "inputs": {"filename_prefix": "test"}}}
        submit_response = requests.post(
            f"{mock_comfyui_url}/prompt",
            json={"prompt": workflow}
        )
        prompt_id = submit_response.json()["prompt_id"]

        # Get history (should auto-complete in mock)
        history_response = requests.get(f"{mock_comfyui_url}/history/{prompt_id}")
        assert history_response.status_code == 200

        history_data = history_response.json()
        assert prompt_id in history_data

    def test_get_history_completed(self, mock_comfyui_url: str):
        """Test getting history for completed job with outputs."""
        # Submit a job
        workflow = {"1": {"class_type": "SaveImage", "inputs": {"filename_prefix": "completed_job"}}}
        submit_response = requests.post(
            f"{mock_comfyui_url}/prompt",
            json={"prompt": workflow}
        )
        prompt_id = submit_response.json()["prompt_id"]

        # Get history
        history_response = requests.get(f"{mock_comfyui_url}/history/{prompt_id}")
        history_data = history_response.json()

        job_data = history_data[prompt_id]
        assert job_data["status"]["completed"] is True
        assert "outputs" in job_data
        assert "9" in job_data["outputs"]  # Mock node ID
        assert "images" in job_data["outputs"]["9"]

        images = job_data["outputs"]["9"]["images"]
        assert len(images) > 0
        assert "filename" in images[0]
        assert images[0]["filename"].startswith("completed_job_")

    def test_get_queue(self, mock_comfyui_url: str):
        """Test getting queue status."""
        response = requests.get(f"{mock_comfyui_url}/queue")
        assert response.status_code == 200

        data = response.json()
        assert "queue_running" in data
        assert "queue_pending" in data

    def test_get_object_info(self, mock_comfyui_url: str):
        """Test getting model information."""
        response = requests.get(f"{mock_comfyui_url}/object_info")
        assert response.status_code == 200

        data = response.json()
        assert "CheckpointLoaderSimple" in data
        assert "LoraLoader" in data

        # Check checkpoint models
        checkpoint_info = data["CheckpointLoaderSimple"]["input"]["required"]["ckpt_name"]
        assert len(checkpoint_info[0]) > 0  # Has at least one model

    def test_interrupt(self, mock_comfyui_url: str):
        """Test workflow interruption."""
        response = requests.post(f"{mock_comfyui_url}/interrupt")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "interrupted"

    def test_output_file_generation(self, mock_comfyui_url: str):
        """Test that mock server generates output files."""
        # Get output directory
        output_dir = Path(__file__).parent.parent.parent / "_infra/mock_services/comfyui/output"

        # Submit a job
        workflow = {"1": {"class_type": "SaveImage", "inputs": {"filename_prefix": "file_test"}}}
        submit_response = requests.post(
            f"{mock_comfyui_url}/prompt",
            json={"prompt": workflow}
        )
        prompt_id = submit_response.json()["prompt_id"]

        # Get history to trigger file generation
        history_response = requests.get(f"{mock_comfyui_url}/history/{prompt_id}")
        history_data = history_response.json()

        # Check file was created
        filename = history_data[prompt_id]["outputs"]["9"]["images"][0]["filename"]
        output_file = output_dir / filename

        assert output_file.exists()
        assert output_file.stat().st_size > 0  # File has content

    def test_multiple_jobs_unique_files(self, mock_comfyui_url: str):
        """Test that multiple jobs create unique output files."""
        filenames = []

        for i in range(3):
            workflow = {"1": {"class_type": "SaveImage", "inputs": {"filename_prefix": f"multi_job_{i}"}}}
            submit_response = requests.post(
                f"{mock_comfyui_url}/prompt",
                json={"prompt": workflow}
            )
            prompt_id = submit_response.json()["prompt_id"]

            history_response = requests.get(f"{mock_comfyui_url}/history/{prompt_id}")
            history_data = history_response.json()

            filename = history_data[prompt_id]["outputs"]["9"]["images"][0]["filename"]
            filenames.append(filename)

        # All filenames should be unique
        assert len(filenames) == len(set(filenames))
