"""Generation job API routes."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from genonaut.api.dependencies import get_database_session
from genonaut.api.services.generation_service import GenerationService
from genonaut.api.models.requests import (
    GenerationJobCreateRequest, 
    GenerationJobUpdateRequest,
    GenerationJobStatusUpdateRequest,
    GenerationJobResultRequest,
    GenerationJobSearchRequest
)
from genonaut.api.models.responses import (
    GenerationJobResponse, 
    GenerationJobListResponse, 
    GenerationJobStatsResponse,
    SuccessResponse
)
from genonaut.api.exceptions import EntityNotFoundError, ValidationError, DatabaseError

router = APIRouter(prefix="/api/v1/generation-jobs", tags=["generation"])


@router.post("/", response_model=GenerationJobResponse, status_code=status.HTTP_201_CREATED)
async def create_generation_job(
    job_data: GenerationJobCreateRequest,
    db: Session = Depends(get_database_session)
):
    """Create a new generation job."""
    service = GenerationService(db)
    try:
        job = service.create_generation_job(
            user_id=job_data.user_id,
            job_type=job_data.job_type,
            prompt=job_data.prompt,
            parameters=job_data.parameters
        )
        return GenerationJobResponse.model_validate(job)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{job_id}", response_model=GenerationJobResponse)
async def get_generation_job(
    job_id: int,
    db: Session = Depends(get_database_session)
):
    """Get generation job by ID."""
    service = GenerationService(db)
    try:
        job = service.get_generation_job(job_id)
        return GenerationJobResponse.model_validate(job)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{job_id}", response_model=GenerationJobResponse)
async def update_generation_job(
    job_id: int,
    job_data: GenerationJobUpdateRequest,
    db: Session = Depends(get_database_session)
):
    """Update generation job parameters (only for pending jobs)."""
    service = GenerationService(db)
    try:
        job = service.update_job(
            job_id=job_id,
            parameters=job_data.parameters
        )
        return GenerationJobResponse.model_validate(job)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.delete("/{job_id}", response_model=SuccessResponse)
async def delete_generation_job(
    job_id: int,
    db: Session = Depends(get_database_session)
):
    """Delete a generation job (only completed or failed jobs)."""
    service = GenerationService(db)
    try:
        service.delete_job(job_id)
        return SuccessResponse(message=f"Generation job {job_id} deleted successfully")
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.put("/{job_id}/status", response_model=GenerationJobResponse)
async def update_job_status(
    job_id: int,
    status_data: GenerationJobStatusUpdateRequest,
    db: Session = Depends(get_database_session)
):
    """Update generation job status."""
    service = GenerationService(db)
    try:
        job = service.update_job_status(
            job_id=job_id,
            status=status_data.status,
            error_message=status_data.error_message
        )
        return GenerationJobResponse.model_validate(job)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.put("/{job_id}/result", response_model=GenerationJobResponse)
async def set_job_result(
    job_id: int,
    result_data: GenerationJobResultRequest,
    db: Session = Depends(get_database_session)
):
    """Set the result content for a generation job."""
    service = GenerationService(db)
    try:
        job = service.set_job_result(job_id, result_data.content_id)
        return GenerationJobResponse.model_validate(job)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/", response_model=GenerationJobListResponse)
async def get_generation_jobs(
    search_params: GenerationJobSearchRequest = Depends(),
    db: Session = Depends(get_database_session)
):
    """Get list of generation jobs with optional filtering."""
    service = GenerationService(db)
    
    jobs = []
    total = 0
    
    try:
        if search_params.user_id:
            jobs = service.get_user_jobs(
                user_id=search_params.user_id,
                skip=search_params.skip,
                limit=search_params.limit,
                status=search_params.status,
            )
            total = service.repository.count({'user_id': search_params.user_id})
        elif search_params.status:
            jobs = service.get_jobs_by_status(
                status=search_params.status,
                skip=search_params.skip,
                limit=search_params.limit,
            )
            total = service.repository.count({'status': search_params.status})
        elif search_params.job_type:
            jobs = service.get_jobs_by_type(
                job_type=search_params.job_type,
                skip=search_params.skip,
                limit=search_params.limit,
            )
            job_type_value = search_params.job_type.value if hasattr(search_params.job_type, 'value') else search_params.job_type
            total = service.repository.count({'job_type': job_type_value})
        else:
            jobs = service.repository.get_multi(
                skip=search_params.skip,
                limit=search_params.limit,
            )
            total = service.repository.count()
    except DatabaseError as exc:
        if "UndefinedTable" in str(exc):
            jobs = []
            total = 0
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
    
    return GenerationJobListResponse(
        items=[GenerationJobResponse.model_validate(job) for job in jobs],
        total=total,
        skip=search_params.skip,
        limit=search_params.limit
    )


@router.get("/user/{user_id}/jobs", response_model=GenerationJobListResponse)
async def get_user_generation_jobs(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_database_session)
):
    """Get generation jobs for a specific user."""
    service = GenerationService(db)
    try:
        jobs = service.get_user_jobs(
            user_id=user_id,
            skip=skip,
            limit=limit,
            status=status
        )
        total = service.repository.count({'user_id': user_id})
        
        return GenerationJobListResponse(
            items=[GenerationJobResponse.model_validate(job) for job in jobs],
            total=total,
            skip=skip,
            limit=limit
        )
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/status/{status}/jobs", response_model=GenerationJobListResponse)
async def get_jobs_by_status(
    status: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_database_session)
):
    """Get generation jobs by status."""
    service = GenerationService(db)
    jobs = service.get_jobs_by_status(status, skip=skip, limit=limit)
    total = service.repository.count({'status': status})
    
    return GenerationJobListResponse(
        items=[GenerationJobResponse.model_validate(job) for job in jobs],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/type/{job_type}/jobs", response_model=GenerationJobListResponse)
async def get_jobs_by_type(
    job_type: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_database_session)
):
    """Get generation jobs by type."""
    service = GenerationService(db)
    jobs = service.get_jobs_by_type(job_type, skip=skip, limit=limit)
    total = service.repository.count({'job_type': job_type})
    
    return GenerationJobListResponse(
        items=[GenerationJobResponse.model_validate(job) for job in jobs],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/pending/all", response_model=GenerationJobListResponse)
async def get_pending_jobs(
    limit: int = 50,
    db: Session = Depends(get_database_session)
):
    """Get pending generation jobs (FIFO order)."""
    service = GenerationService(db)
    jobs = service.get_pending_jobs(limit=limit)
    
    return GenerationJobListResponse(
        items=[GenerationJobResponse.model_validate(job) for job in jobs],
        total=len(jobs),
        skip=0,
        limit=limit
    )


@router.get("/running/all", response_model=GenerationJobListResponse)
async def get_running_jobs(
    db: Session = Depends(get_database_session)
):
    """Get currently running generation jobs."""
    service = GenerationService(db)
    jobs = service.get_running_jobs()
    
    return GenerationJobListResponse(
        items=[GenerationJobResponse.model_validate(job) for job in jobs],
        total=len(jobs),
        skip=0,
        limit=len(jobs)
    )


@router.get("/completed/all", response_model=GenerationJobListResponse)
async def get_completed_jobs(
    user_id: int = None,
    days: int = 30,
    limit: int = 100,
    db: Session = Depends(get_database_session)
):
    """Get completed generation jobs."""
    service = GenerationService(db)
    jobs = service.get_completed_jobs(user_id=user_id, days=days, limit=limit)
    
    return GenerationJobListResponse(
        items=[GenerationJobResponse.model_validate(job) for job in jobs],
        total=len(jobs),
        skip=0,
        limit=limit
    )


@router.get("/failed/all", response_model=GenerationJobListResponse)
async def get_failed_jobs(
    user_id: int = None,
    days: int = 7,
    limit: int = 100,
    db: Session = Depends(get_database_session)
):
    """Get failed generation jobs."""
    service = GenerationService(db)
    jobs = service.get_failed_jobs(user_id=user_id, days=days, limit=limit)
    
    return GenerationJobListResponse(
        items=[GenerationJobResponse.model_validate(job) for job in jobs],
        total=len(jobs),
        skip=0,
        limit=limit
    )


@router.get("/stats/overview", response_model=GenerationJobStatsResponse)
async def get_generation_job_stats(
    user_id: int = None,
    db: Session = Depends(get_database_session)
):
    """Get generation job statistics."""
    service = GenerationService(db)
    try:
        stats = service.get_job_statistics(user_id=user_id)
        return GenerationJobStatsResponse(user_id=user_id, **stats)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/user/{user_id}/stats", response_model=GenerationJobStatsResponse)
async def get_user_generation_stats(
    user_id: int,
    db: Session = Depends(get_database_session)
):
    """Get generation job statistics for a specific user."""
    service = GenerationService(db)
    try:
        stats = service.get_job_statistics(user_id=user_id)
        return GenerationJobStatsResponse(user_id=user_id, **stats)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/queue/process", response_model=GenerationJobListResponse)
async def process_job_queue(
    max_jobs: int = 1,
    db: Session = Depends(get_database_session)
):
    """Process the job queue by starting pending jobs."""
    service = GenerationService(db)
    started_jobs = service.process_job_queue(max_jobs=max_jobs)
    
    return GenerationJobListResponse(
        items=[GenerationJobResponse.model_validate(job) for job in started_jobs],
        total=len(started_jobs),
        skip=0,
        limit=len(started_jobs)
    )


@router.get("/queue/stats")
async def get_queue_statistics(
    db: Session = Depends(get_database_session)
):
    """Provide simple queue metrics for monitoring."""

    service = GenerationService(db)
    try:
        pending = service.repository.count({'status': 'pending'})
        running = service.repository.count({'status': 'running'})
    except DatabaseError as exc:
        if "UndefinedTable" in str(exc):
            pending = running = 0
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

    return {
        "pending_jobs": pending,
        "running_jobs": running,
    }
