"""Unit tests for worker ComfyUI client helpers."""

from unittest.mock import MagicMock


import pytest

from genonaut.worker.comfyui_client import ComfyUIWorkerClient


def test_worker_client_method_delegation():
    client = ComfyUIWorkerClient()

    client.submit_workflow = MagicMock(return_value="prompt-xyz")  # type: ignore[method-assign]
    client.wait_for_completion = MagicMock(return_value={"status": "completed"})  # type: ignore[method-assign]
    client.get_output_files = MagicMock(return_value=["path.png"])  # type: ignore[method-assign]

    assert client.submit_generation({"prompt": {}}) == "prompt-xyz"
    assert client.wait_for_outputs("prompt-xyz") == {"status": "completed"}
    client.read_output_file = MagicMock(return_value=b"bytes")  # type: ignore[method-assign]

    assert client.collect_output_paths({}) == ["path.png"]
    assert client.download_image("image.png") == b"bytes"

    client.submit_workflow.assert_called_once()
    client.wait_for_completion.assert_called_once()
    client.get_output_files.assert_called_once()
    client.read_output_file.assert_called_once()


def test_worker_client_download_image_reads_bytes(tmp_path):
    client = ComfyUIWorkerClient()
    client.settings.comfyui_output_dir = str(tmp_path)

    target = tmp_path / "image.png"
    target.write_bytes(b"example")

    assert client.download_image("image.png") == b"example"

    nested_dir = tmp_path / "nested"
    nested_dir.mkdir()
    nested_file = nested_dir / "nested.png"
    nested_file.write_bytes(b"nested-bytes")

    assert client.download_image("nested.png", subfolder="nested") == b"nested-bytes"

    with pytest.raises(FileNotFoundError):
        client.download_image("missing.png")
