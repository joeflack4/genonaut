"""Mock ComfyUI server for testing.

This server mimics the ComfyUI API for integration testing without requiring
a real ComfyUI instance. It simulates workflow submission, status tracking,
and file generation.
"""

import json
import shutil
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel


# Request/Response Models
class PromptRequest(BaseModel):
    """Request model for POST /prompt"""
    prompt: Dict[str, Any]
    client_id: Optional[str] = None


class PromptResponse(BaseModel):
    """Response model for POST /prompt"""
    prompt_id: str


# Mock Server State
class MockComfyUIServer:
    """State management for mock ComfyUI server.

    Args:
        input_dir: Directory containing input files for mock generation
        output_dir: Directory to write generated output files
        processing_delay: Minimum time in seconds before job completion (default 0.5)
    """

    def __init__(self, input_dir: Path, output_dir: Path, processing_delay: float = 0.5):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.processing_delay = processing_delay
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.queue_running: List[tuple] = []
        self.queue_pending: List[tuple] = []
        self.job_counter = 1

    def submit_job(self, workflow: Dict[str, Any], client_id: Optional[str] = None) -> str:
        """Submit a new job and return prompt_id."""
        prompt_id = str(uuid.uuid4())

        # Extract filename_prefix from workflow if present
        filename_prefix = "genonaut_gen"
        for node_id, node_data in workflow.items():
            if node_data.get("class_type") == "SaveImage":
                filename_prefix = node_data.get("inputs", {}).get("filename_prefix", "genonaut_gen")
                break

        # Create job record
        self.jobs[prompt_id] = {
            "workflow": workflow,
            "client_id": client_id,
            "status": "queued",
            "filename_prefix": filename_prefix,
            "output_files": [],
            "created_at": datetime.utcnow().isoformat(),
            "submitted_at": time.time(),
            "completed": False,
            "messages": []
        }

        # Add to pending queue
        self.queue_pending.append((0, prompt_id))

        return prompt_id

    def process_job(self, prompt_id: str) -> None:
        """Process a job by generating mock output file."""
        if prompt_id not in self.jobs:
            return

        job = self.jobs[prompt_id]

        # Move from pending to running
        self.queue_pending = [item for item in self.queue_pending if item[1] != prompt_id]
        self.queue_running.append((0, prompt_id))

        # Update status
        job["status"] = "running"

        # Simulate file generation - copy input file to output with new name
        input_file = self.input_dir / "kernie_512x768.jpg"
        if input_file.exists():
            # Generate output filename
            prefix = job["filename_prefix"]
            counter = str(self.job_counter).zfill(5)
            self.job_counter += 1
            output_filename = f"{prefix}_{counter}_.png"
            output_path = self.output_dir / output_filename

            # Copy file
            shutil.copy(input_file, output_path)

            # Record output file
            job["output_files"].append({
                "filename": output_filename,
                "subfolder": "",
                "type": "output"
            })

        # Mark as completed
        job["status"] = "completed"
        job["completed"] = True

        # Remove from running queue
        self.queue_running = [item for item in self.queue_running if item[1] != prompt_id]

    def get_history(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """Get job history.

        Returns empty dict if job is still processing (hasn't reached processing_delay).
        Returns full history with status and outputs once processing is complete.

        Response structure matches real ComfyUI:
        - prompt: [number, prompt_id, workflow, extra_data, output_nodes]
        - outputs: {node_id: {images: [{filename, subfolder, type}]}}
        - status: {status_str, completed, messages}
        - meta: {node_id: {node metadata}}
        """
        if prompt_id not in self.jobs:
            return None

        job = self.jobs[prompt_id]

        # Check if enough time has elapsed
        elapsed_time = time.time() - job["submitted_at"]
        if elapsed_time < self.processing_delay:
            # Job is still "running" - return empty response like real ComfyUI
            return {}

        # Auto-process if still queued and enough time has passed
        if job["status"] == "queued":
            self.process_job(prompt_id)

        # Build outputs structure
        outputs = {}
        if job["output_files"]:
            outputs["9"] = {  # Mock node ID
                "images": job["output_files"]
            }

        # Build prompt structure (matches real ComfyUI format)
        prompt_data = [
            0,  # number
            prompt_id,
            job["workflow"],
            {"client_id": job["client_id"] or "mock-client"},
            ["9"]  # output nodes
        ]

        # Build status with status_str field
        status_str = "success" if job["completed"] and job["status"] == "completed" else "failed"

        # Build meta structure
        meta = {}
        if job["output_files"]:
            meta["9"] = {
                "node_id": "9",
                "display_node": "9",
                "parent_node": None,
                "real_node_id": "9"
            }

        return {
            "prompt": prompt_data,
            "outputs": outputs,
            "status": {
                "status_str": status_str,
                "completed": job["completed"],
                "messages": job["messages"]
            },
            "meta": meta
        }

    def get_queue(self) -> Dict[str, List]:
        """Get queue status."""
        return {
            "queue_running": self.queue_running,
            "queue_pending": self.queue_pending
        }

    def interrupt(self) -> None:
        """Interrupt current processing."""
        # In mock, we just clear the queues
        self.queue_running.clear()
        # Mark any running jobs as failed
        for job in self.jobs.values():
            if job["status"] == "running":
                job["status"] = "failed"
                job["completed"] = False
                job["messages"].append("Interrupted by user")


# Initialize server state
BASE_DIR = Path(__file__).parent
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"

# Ensure directories exist
INPUT_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Create server instance
mock_server = MockComfyUIServer(INPUT_DIR, OUTPUT_DIR)

# Create FastAPI app
app = FastAPI(title="Mock ComfyUI Server")


@app.get("/system_stats")
async def system_stats():
    """Health check endpoint."""
    return {
        "system": {
            "os": "mock",
            "comfyui_version": "mock-0.1.0"
        },
        "devices": []
    }


@app.post("/prompt")
async def submit_prompt(request: PromptRequest):
    """Submit a workflow for execution."""
    try:
        prompt_id = mock_server.submit_job(request.prompt, request.client_id)
        return {
            "prompt_id": prompt_id,
            "number": 0,
            "node_errors": {}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history/{prompt_id}")
async def get_history(prompt_id: str):
    """Get workflow execution history.

    Returns:
        - {} if job not found or still processing
        - {prompt_id: {...}} if job is completed with full history
    """
    history = mock_server.get_history(prompt_id)

    if history is None or history == {}:
        # Return empty history if not found or still processing
        return {}

    return {prompt_id: history}


@app.get("/queue")
async def get_queue():
    """Get current queue status."""
    return mock_server.get_queue()


@app.get("/object_info")
async def get_object_info():
    """Get available models and object information."""
    return {
        "CheckpointLoaderSimple": {
            "input": {
                "required": {
                    "ckpt_name": [
                        ["test_checkpoint.safetensors", "mock_model_v1.ckpt"],
                        {}
                    ]
                }
            }
        },
        "LoraLoader": {
            "input": {
                "required": {
                    "lora_name": [
                        ["test_lora.safetensors", "mock_lora_v1.safetensors"],
                        {}
                    ]
                }
            }
        }
    }


@app.post("/interrupt")
async def interrupt():
    """Interrupt current workflow execution."""
    mock_server.interrupt()
    return {"status": "interrupted"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "status": "ok",
        "server": "Mock ComfyUI Server",
        "version": "0.1.0"
    }


# Cleanup function for tests
def cleanup_outputs():
    """Remove all generated output files."""
    for file in OUTPUT_DIR.glob("*"):
        if file.is_file():
            file.unlink()


def reset_server():
    """Reset server state."""
    mock_server.jobs.clear()
    mock_server.queue_running.clear()
    mock_server.queue_pending.clear()
    mock_server.job_counter = 1
    cleanup_outputs()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8189)
