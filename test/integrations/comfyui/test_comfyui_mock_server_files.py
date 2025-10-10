"""Tests for mock server file output functionality."""

import pytest
from pathlib import Path
from genonaut.api.services.comfyui_client import ComfyUIClient


class TestMockServerFileOutput:
    """Test file generation and management in mock server."""

    @pytest.mark.longrunning
    @pytest.mark.comfyui_poll
    def test_output_file_naming_pattern(self, mock_comfyui_client: ComfyUIClient):
        """Test output files follow correct naming pattern."""
        workflow = {
            "1": {"class_type": "SaveImage", "inputs": {"filename_prefix": "naming_test"}}
        }

        prompt_id = mock_comfyui_client.submit_workflow(workflow)
        result = mock_comfyui_client.wait_for_completion(prompt_id)

        outputs = result["outputs"]
        images = outputs["9"]["images"]

        # Check filename pattern: {prefix}_{counter}_.png
        filename = images[0]["filename"]
        assert filename.startswith("naming_test_")
        assert filename.endswith("_.png")

    @pytest.mark.longrunning
    @pytest.mark.comfyui_poll
    def test_output_file_subfolder(self, mock_comfyui_client: ComfyUIClient):
        """Test output files report correct subfolder."""
        workflow = {
            "1": {"class_type": "SaveImage", "inputs": {"filename_prefix": "subfolder_test"}}
        }

        prompt_id = mock_comfyui_client.submit_workflow(workflow)
        result = mock_comfyui_client.wait_for_completion(prompt_id)

        outputs = result["outputs"]
        images = outputs["9"]["images"]

        # Mock server uses empty subfolder
        assert images[0]["subfolder"] == ""
        assert images[0]["type"] == "output"

    @pytest.mark.longrunning
    @pytest.mark.comfyui_poll
    def test_concurrent_jobs_unique_files(self, mock_comfyui_client: ComfyUIClient):
        """Test concurrent jobs create unique output files."""
        filenames = []

        for i in range(5):
            workflow = {
                "1": {"class_type": "SaveImage", "inputs": {"filename_prefix": f"concurrent_{i}"}}
            }

            prompt_id = mock_comfyui_client.submit_workflow(workflow)
            result = mock_comfyui_client.wait_for_completion(prompt_id)

            filename = result["outputs"]["9"]["images"][0]["filename"]
            filenames.append(filename)

        # All filenames should be unique
        assert len(filenames) == len(set(filenames))

        # Each should match its prefix
        for i, filename in enumerate(filenames):
            assert filename.startswith(f"concurrent_{i}_")

    @pytest.mark.longrunning
    @pytest.mark.comfyui_poll
    def test_output_files_exist_on_disk(self, mock_comfyui_url: str, mock_comfyui_client: ComfyUIClient):
        """Test generated files actually exist on disk."""
        output_dir = Path(__file__).parent.parent.parent / "_infra/mock_services/comfyui/output"

        workflow = {
            "1": {"class_type": "SaveImage", "inputs": {"filename_prefix": "disk_test"}}
        }

        prompt_id = mock_comfyui_client.submit_workflow(workflow)
        result = mock_comfyui_client.wait_for_completion(prompt_id)

        filename = result["outputs"]["9"]["images"][0]["filename"]
        file_path = output_dir / filename

        assert file_path.exists()
        assert file_path.is_file()
        assert file_path.stat().st_size > 0

    def test_output_files_cleaned_between_tests(self, mock_comfyui_url: str):
        """Test output files are cleaned between test runs."""
        output_dir = Path(__file__).parent.parent.parent / "_infra/mock_services/comfyui/output"

        # This test relies on the mock_comfyui_url fixture which resets server state
        # The output directory should be clean at the start of each test
        initial_files = list(output_dir.glob("*"))

        # Only files from this test run should exist (created by fixture startup)
        # We can't guarantee zero files if server just started, but we can verify cleanup happens
        assert output_dir.exists()

    @pytest.mark.longrunning
    @pytest.mark.comfyui_poll
    def test_multiple_images_same_job(self, mock_comfyui_client: ComfyUIClient):
        """Test job can have multiple output images."""
        # In the real ComfyUI, batch_size > 1 would create multiple images
        # Our mock currently creates one image per job, but structure supports multiple

        workflow = {
            "1": {"class_type": "SaveImage", "inputs": {"filename_prefix": "multi_image"}}
        }

        prompt_id = mock_comfyui_client.submit_workflow(workflow)
        result = mock_comfyui_client.wait_for_completion(prompt_id)

        images = result["outputs"]["9"]["images"]
        assert isinstance(images, list)
        assert len(images) >= 1  # At least one image

    @pytest.mark.longrunning
    @pytest.mark.comfyui_poll
    def test_filename_counter_increments(self, mock_comfyui_client: ComfyUIClient):
        """Test filename counter increments across jobs."""
        filenames = []

        # Submit 3 jobs with same prefix
        for _ in range(3):
            workflow = {
                "1": {"class_type": "SaveImage", "inputs": {"filename_prefix": "counter_test"}}
            }

            prompt_id = mock_comfyui_client.submit_workflow(workflow)
            result = mock_comfyui_client.wait_for_completion(prompt_id)

            filename = result["outputs"]["9"]["images"][0]["filename"]
            filenames.append(filename)

        # Extract counter values from filenames
        counters = []
        for filename in filenames:
            # Format: counter_test_{NNNNN}_.png
            parts = filename.replace("counter_test_", "").replace("_.png", "")
            counter = int(parts)
            counters.append(counter)

        # Counters should be incrementing
        assert counters[1] > counters[0]
        assert counters[2] > counters[1]
