"""Unit tests for generation request Pydantic models."""

import uuid

import pytest
from pydantic import ValidationError

from genonaut.api.models.enums import JobType
from genonaut.api.models.requests import GenerationJobCreateRequest


def test_generation_job_create_request_accepts_sampler_params():
    """Sampler parameters should be stored without modification."""

    request = GenerationJobCreateRequest(
        user_id=uuid.uuid4(),
        job_type=JobType.IMAGE,
        prompt="Sample",
        sampler_params={"steps": 20, "cfg": 7.0},
    )

    assert request.sampler_params == {"steps": 20, "cfg": 7.0}


def test_generation_job_create_request_rejects_non_dict_sampler_params():
    """Non-dictionary sampler params should trigger validation errors."""

    with pytest.raises(ValidationError):
        GenerationJobCreateRequest(
            user_id=uuid.uuid4(),
            job_type=JobType.IMAGE,
            prompt="Invalid",
            sampler_params=["not", "a", "dict"],
        )
