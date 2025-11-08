"""ComfyUI client for workflow submission and management."""

import json
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List

import requests
from requests.exceptions import RequestException, ConnectionError, Timeout

from genonaut.api.config import get_settings, Settings, get_cached_settings
from genonaut.api.exceptions import ValidationError
from genonaut.api.services.cache_service import ComfyUICacheService


class ComfyUIConnectionError(Exception):
    """Exception raised when ComfyUI connection fails."""
    pass


class ComfyUIWorkflowError(Exception):
    """Exception raised when ComfyUI workflow execution fails."""
    pass


class ComfyUIClient:
    """Client for interacting with ComfyUI API.

    Handles workflow submission, status monitoring, and result retrieval.
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        backend_url: Optional[str] = None,
        output_dir: Optional[str] = None,
        models_dir: Optional[str] = None
    ):
        """Initialize ComfyUI client with configuration settings.

        Args:
            settings: Optional settings instance to bind to this client. When
                ``None``, configuration is loaded via :func:`get_settings`.
            backend_url: Optional backend URL override. If provided, this URL
                will be used instead of the configured comfyui_url.
            output_dir: Optional output directory override. If provided, this
                directory will be used for resolving output file paths instead
                of the configured comfyui_output_dir.
            models_dir: Optional models directory override. If provided, this
                directory will be used for model-related operations instead
                of the configured comfyui_models_dir.
        """
        self.settings = settings or get_cached_settings() or get_settings()
        # Use backend_url if provided, otherwise fall back to configured URL
        self.base_url = (backend_url or self.settings.comfyui_url).rstrip('/')
        # Use output_dir if provided, otherwise fall back to configured output dir
        self.output_dir = output_dir or self.settings.comfyui_output_dir
        # Use models_dir if provided, otherwise fall back to configured models dir
        self.models_dir = models_dir or self.settings.comfyui_models_dir
        self.timeout = self.settings.comfyui_timeout
        self.poll_interval = self.settings.comfyui_poll_interval
        self.session = requests.Session()
        self.cache_service = ComfyUICacheService()

    def health_check(self) -> bool:
        """Check if ComfyUI server is accessible.

        Returns:
            True if server is accessible, False otherwise
        """
        # Try to get from cache first
        cached_health = self.cache_service.get_comfyui_health()
        if cached_health is not None:
            return cached_health.get('is_healthy', False)

        # Perform actual health check
        try:
            response = self.session.get(
                f"{self.base_url}/system_stats",
                timeout=5
            )
            is_healthy = response.status_code == 200

            # Cache the health status
            health_status = {
                'is_healthy': is_healthy,
                'checked_at': time.time(),
                'status_code': response.status_code if is_healthy else None
            }
            self.cache_service.set_comfyui_health(health_status)

            return is_healthy

        except RequestException as e:
            # Cache the failure status
            health_status = {
                'is_healthy': False,
                'checked_at': time.time(),
                'error': str(e)
            }
            self.cache_service.set_comfyui_health(health_status)
            return False

    def submit_workflow(self, workflow: Dict[str, Any], client_id: Optional[str] = None) -> str:
        """Submit a workflow to ComfyUI for execution.

        Args:
            workflow: ComfyUI workflow dictionary
            client_id: Optional client ID for tracking

        Returns:
            Prompt ID for tracking the workflow execution

        Raises:
            ComfyUIConnectionError: If unable to connect to ComfyUI
            ComfyUIWorkflowError: If workflow submission fails
            ValidationError: If workflow is invalid
        """
        if not workflow:
            raise ValidationError("Workflow cannot be empty")

        if not client_id:
            client_id = str(uuid.uuid4())

        payload = {
            "prompt": workflow,
            "client_id": client_id
        }

        try:
            response = self.session.post(
                f"{self.base_url}/prompt",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            result = response.json()

            if "prompt_id" not in result:
                raise ComfyUIWorkflowError(f"Invalid response from ComfyUI: {result}")

            return result["prompt_id"]

        except ConnectionError as e:
            raise ComfyUIConnectionError(f"Failed to connect to ComfyUI at {self.base_url}: {str(e)}")
        except Timeout as e:
            raise ComfyUIConnectionError(f"Timeout connecting to ComfyUI: {str(e)}")
        except RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    raise ComfyUIWorkflowError(f"ComfyUI rejected workflow: {error_detail}")
                except (ValueError, json.JSONDecodeError):
                    raise ComfyUIWorkflowError(f"ComfyUI request failed: HTTP {e.response.status_code}")
            else:
                raise ComfyUIConnectionError(f"Request failed: {str(e)}")

    def get_workflow_status(self, prompt_id: str) -> Dict[str, Any]:
        """Get the status of a workflow execution.

        Args:
            prompt_id: The prompt ID returned from submit_workflow

        Returns:
            Dictionary containing workflow status information

        Raises:
            ComfyUIConnectionError: If unable to connect to ComfyUI
        """
        try:
            response = self.session.get(
                f"{self.base_url}/history/{prompt_id}",
                timeout=self.timeout
            )
            response.raise_for_status()

            history = response.json()

            if prompt_id not in history:
                # Workflow might still be running or queued
                queue_response = self.session.get(
                    f"{self.base_url}/queue",
                    timeout=self.timeout
                )
                queue_response.raise_for_status()
                queue_data = queue_response.json()

                # Check if prompt is in queue
                for item in queue_data.get("queue_running", []) + queue_data.get("queue_pending", []):
                    if item[1] == prompt_id:
                        return {
                            "status": "running" if item in queue_data.get("queue_running", []) else "queued",
                            "prompt_id": prompt_id
                        }

                return {
                    "status": "unknown",
                    "prompt_id": prompt_id
                }

            # Workflow is in history - check if completed successfully
            workflow_history = history[prompt_id]
            status = workflow_history.get("status", {})

            if status.get("completed", False):
                return {
                    "status": "completed",
                    "prompt_id": prompt_id,
                    "outputs": workflow_history.get("outputs", {}),
                    "messages": status.get("messages", [])
                }
            else:
                return {
                    "status": "failed",
                    "prompt_id": prompt_id,
                    "messages": status.get("messages", [])
                }

        except RequestException as e:
            raise ComfyUIConnectionError(f"Failed to get workflow status: {str(e)}")

    def wait_for_completion(self, prompt_id: str, max_wait_time: int = 300) -> Dict[str, Any]:
        """Wait for a workflow to complete execution.

        Args:
            prompt_id: The prompt ID to monitor
            max_wait_time: Maximum time to wait in seconds

        Returns:
            Final workflow status

        Raises:
            ComfyUIConnectionError: If connection fails during polling
            ComfyUIWorkflowError: If workflow fails or times out
        """
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            status = self.get_workflow_status(prompt_id)

            if status["status"] in ["completed", "failed"]:
                return status

            time.sleep(self.poll_interval)

        raise ComfyUIWorkflowError(f"Workflow {prompt_id} timed out after {max_wait_time} seconds")

    def cancel_workflow(self, prompt_id: str) -> bool:
        """Cancel a running workflow.

        Args:
            prompt_id: The prompt ID to cancel

        Returns:
            True if cancellation was successful

        Raises:
            ComfyUIConnectionError: If unable to connect to ComfyUI
        """
        try:
            response = self.session.post(
                f"{self.base_url}/interrupt",
                timeout=self.timeout
            )
            response.raise_for_status()
            return True

        except RequestException as e:
            raise ComfyUIConnectionError(f"Failed to cancel workflow: {str(e)}")

    def get_available_models(self) -> Dict[str, List[str]]:
        """Get list of available models from ComfyUI.

        Returns:
            Dictionary with model types as keys and lists of model names as values

        Raises:
            ComfyUIConnectionError: If unable to connect to ComfyUI
        """
        try:
            response = self.session.get(
                f"{self.base_url}/object_info",
                timeout=self.timeout
            )
            response.raise_for_status()

            object_info = response.json()
            models = {}

            # Extract checkpoint models
            if "CheckpointLoaderSimple" in object_info:
                checkpoint_info = object_info["CheckpointLoaderSimple"]["input"]["required"]
                if "ckpt_name" in checkpoint_info:
                    models["checkpoints"] = checkpoint_info["ckpt_name"][0]

            # Extract LoRA models
            if "LoraLoader" in object_info:
                lora_info = object_info["LoraLoader"]["input"]["required"]
                if "lora_name" in lora_info:
                    models["loras"] = lora_info["lora_name"][0]

            return models

        except RequestException as e:
            raise ComfyUIConnectionError(f"Failed to get available models: {str(e)}")

    def get_output_files(self, outputs: Dict[str, Any]) -> List[str]:
        """Extract output file paths from ComfyUI outputs.

        Args:
            outputs: The outputs dictionary from workflow completion

        Returns:
            List of output file paths
        """
        file_paths = []

        for node_id, node_outputs in outputs.items():
            if "images" in node_outputs:
                for image in node_outputs["images"]:
                    if "filename" in image and "subfolder" in image:
                        # Construct full path
                        filename = image["filename"]
                        subfolder = image["subfolder"]
                        if subfolder:
                            file_path = f"{self.output_dir}/{subfolder}/{filename}"
                        else:
                            file_path = f"{self.output_dir}/{filename}"
                        file_paths.append(file_path)

        return file_paths

    def read_output_file(self, filename: str, *, subfolder: str = "") -> bytes:
        """Read a generated image file from the ComfyUI output directory.

        Args:
            filename: Name of the file produced by ComfyUI.
            subfolder: Optional subfolder reported by ComfyUI.

        Returns:
            Raw file bytes.

        Raises:
            FileNotFoundError: If the composed path does not exist.
            OSError: If reading the file fails.
        """

        base_path = Path(self.output_dir)
        target_path = base_path / subfolder / filename if subfolder else base_path / filename

        if not target_path.exists():
            raise FileNotFoundError(f"ComfyUI output file not found: {target_path}")

        return target_path.read_bytes()
