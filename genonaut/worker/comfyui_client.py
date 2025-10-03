"""Worker-facing ComfyUI client helpers."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from genonaut.api.services.comfyui_client import (
    ComfyUIClient,
    ComfyUIConnectionError,
    ComfyUIWorkflowError,
)


class ComfyUIWorkerClient(ComfyUIClient):
    """Thin wrapper around the API ComfyUI client for Celery workers.

    The base client already encapsulates request handling, retryable error
    types, and output parsing logic.  This subclass simply provides
    worker-friendly names and default configuration for long-running
    workflows handled by Celery tasks.
    """

    def submit_generation(self, workflow: Dict[str, Any], *, client_id: Optional[str] = None) -> str:
        """Submit a workflow and return the ComfyUI prompt ID."""

        return self.submit_workflow(workflow, client_id=client_id)

    def wait_for_outputs(self, prompt_id: str, *, max_wait_time: Optional[int] = None) -> Dict[str, Any]:
        """Block until the workflow finishes and return the status payload."""

        effective_wait = max_wait_time or self.settings.comfyui_max_wait_time
        return self.wait_for_completion(prompt_id, max_wait_time=effective_wait)

    def collect_output_paths(self, outputs: Dict[str, Any]) -> List[str]:
        """Extract resulting image file paths from a workflow output payload."""

        return self.get_output_files(outputs)

    def download_image(self, filename: str, *, subfolder: str = "") -> bytes:
        """Retrieve a generated image from the ComfyUI output directory."""

        return self.read_output_file(filename, subfolder=subfolder)


__all__ = [
    "ComfyUIWorkerClient",
    "ComfyUIConnectionError",
    "ComfyUIWorkflowError",
]
