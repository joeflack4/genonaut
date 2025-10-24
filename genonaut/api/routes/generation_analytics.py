"""Generation analytics API routes.

These endpoints expose generation analytics data collected from the
generation service via Redis Streams and aggregated in PostgreSQL.

The data pipeline:
1. MetricsService writes events to Redis Streams (< 1ms overhead)
2. Celery task transfers events to PostgreSQL (every 10 minutes)
3. Celery task aggregates hourly metrics (every hour)
4. These endpoints query the aggregated data
"""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, Path
from sqlalchemy.orm import Session

from genonaut.api.dependencies import get_database_session
from genonaut.api.services.generation_analytics_service import GenerationAnalyticsService

router = APIRouter(prefix="/api/v1/analytics/generation", tags=["analytics", "generation"])


@router.get("/overview")
async def get_generation_overview(
    days: int = Query(7, ge=1, le=90, description="Days of history to analyze"),
    db: Session = Depends(get_database_session)
):
    """Get high-level overview of generation activity.

    Returns dashboard-style metrics including:
    - Total requests, completions, failures, cancellations
    - Success rate percentage
    - Duration percentiles (avg/p50/p95/p99)
    - Total images generated
    - Unique users

    **Examples:**
    - `/api/v1/analytics/generation/overview?days=7` - Last week overview
    - `/api/v1/analytics/generation/overview?days=30` - Last month overview

    **Response:**
    ```json
    {
      "lookback_days": 7,
      "total_requests": 1500,
      "successful_generations": 1425,
      "failed_generations": 50,
      "cancelled_generations": 25,
      "success_rate_pct": 95.0,
      "avg_duration_ms": 3500,
      "p50_duration_ms": 3200,
      "p95_duration_ms": 5800,
      "p99_duration_ms": 7200,
      "total_images_generated": 1425
    }
    ```
    """
    try:
        service = GenerationAnalyticsService(db)
        return service.get_generation_overview(days=days)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get generation overview: {str(e)}"
        )


@router.get("/trends")
async def get_generation_trends(
    days: int = Query(7, ge=1, le=90, description="Days of history to analyze"),
    interval: Literal["hourly", "daily"] = Query(
        "hourly",
        description="Data granularity: 'hourly' or 'daily'"
    ),
    db: Session = Depends(get_database_session)
):
    """Get time-series trends for generation metrics.

    Returns time-series data showing generation activity over time.
    Useful for identifying patterns, spikes, and performance changes.

    **Granularity Options:**
    - `hourly`: Returns data points for each hour (max 90 days)
    - `daily`: Returns aggregated daily data (max 90 days)

    **Examples:**
    - `/api/v1/analytics/generation/trends?days=7&interval=hourly`
    - `/api/v1/analytics/generation/trends?days=30&interval=daily`

    **Response:**
    ```json
    {
      "interval": "hourly",
      "lookback_days": 7,
      "total_data_points": 168,
      "data_points": [
        {
          "timestamp": "2025-10-23T00:00:00",
          "total_requests": 45,
          "successful_generations": 43,
          "failed_generations": 2,
          "cancelled_generations": 0,
          "avg_duration_ms": 3200,
          "p95_duration_ms": 5500,
          "success_rate": 0.956
        }
      ]
    }
    ```
    """
    try:
        service = GenerationAnalyticsService(db)
        return service.get_generation_trends(days=days, interval=interval)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get generation trends: {str(e)}"
        )


@router.get("/users/{user_id}")
async def get_user_generation_analytics(
    user_id: UUID = Path(..., description="User ID to analyze"),
    days: int = Query(30, ge=1, le=90, description="Days of history to analyze"),
    db: Session = Depends(get_database_session)
):
    """Get generation analytics for a specific user.

    Analyzes a user's generation history including:
    - Total generations and success rate
    - Performance metrics (duration percentiles)
    - Recent activity timeline (last 20 generations)
    - Failure patterns and error breakdown

    **Examples:**
    - `/api/v1/analytics/generation/users/550e8400-e29b-41d4-a716-446655440000?days=30`

    **Response:**
    ```json
    {
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "lookback_days": 30,
      "total_requests": 125,
      "successful_generations": 118,
      "failed_generations": 5,
      "cancelled_generations": 2,
      "success_rate_pct": 94.4,
      "avg_duration_ms": 3450,
      "p50_duration_ms": 3300,
      "p95_duration_ms": 5200,
      "last_generation_at": "2025-10-23T14:30:00",
      "recent_activity": [...],
      "failure_breakdown": [
        {"error_type": "timeout", "count": 3},
        {"error_type": "oom", "count": 2}
      ]
    }
    ```
    """
    try:
        service = GenerationAnalyticsService(db)
        return service.get_user_generation_analytics(
            user_id=str(user_id),
            days=days
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user generation analytics: {str(e)}"
        )


@router.get("/models")
async def get_model_performance(
    days: int = Query(30, ge=1, le=90, description="Days of history to analyze"),
    db: Session = Depends(get_database_session)
):
    """Get performance comparison across different models.

    Analyzes generation performance broken down by model checkpoint:
    - Total generations per model
    - Success rates
    - Duration percentiles
    - Last used timestamp

    Useful for:
    - Comparing model reliability
    - Identifying problematic models
    - Capacity planning by model

    **Examples:**
    - `/api/v1/analytics/generation/models?days=30`
    - `/api/v1/analytics/generation/models?days=7`

    **Response:**
    ```json
    {
      "lookback_days": 30,
      "total_models": 5,
      "models": [
        {
          "model_checkpoint": "sd_xl_base_1.0.safetensors",
          "total_generations": 850,
          "successful_generations": 825,
          "failed_generations": 25,
          "success_rate_pct": 97.06,
          "avg_duration_ms": 3200,
          "p50_duration_ms": 3100,
          "p95_duration_ms": 4800,
          "last_used_at": "2025-10-23T14:30:00"
        }
      ]
    }
    ```
    """
    try:
        service = GenerationAnalyticsService(db)
        return service.get_model_performance(days=days)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model performance: {str(e)}"
        )


@router.get("/failures")
async def get_failure_analysis(
    days: int = Query(7, ge=1, le=90, description="Days of history to analyze"),
    db: Session = Depends(get_database_session)
):
    """Get detailed analysis of generation failures.

    Analyzes failure patterns to help identify issues:
    - Breakdown by error type with counts
    - Sample error messages for each type
    - Daily failure rate trends
    - Total failure counts

    Useful for:
    - Debugging recurring issues
    - Identifying system bottlenecks
    - Monitoring service health
    - Planning infrastructure improvements

    **Examples:**
    - `/api/v1/analytics/generation/failures?days=7`
    - `/api/v1/analytics/generation/failures?days=30`

    **Response:**
    ```json
    {
      "lookback_days": 7,
      "total_error_types": 4,
      "error_types": [
        {
          "error_type": "timeout",
          "count": 45,
          "avg_duration_ms": 30000,
          "sample_messages": [
            "ComfyUI request timeout after 30s",
            "Generation queue timeout"
          ]
        },
        {
          "error_type": "oom",
          "count": 12,
          "avg_duration_ms": 15000,
          "sample_messages": ["Out of memory on GPU"]
        }
      ],
      "failure_trends": [
        {
          "date": "2025-10-23",
          "total_completions": 250,
          "failures": 8,
          "failure_rate": 0.032
        }
      ]
    }
    ```
    """
    try:
        service = GenerationAnalyticsService(db)
        return service.get_failure_analysis(days=days)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get failure analysis: {str(e)}"
        )


@router.get("/peak-hours")
async def get_peak_usage_times(
    days: int = Query(30, ge=7, le=90, description="Days of history to analyze"),
    db: Session = Depends(get_database_session)
):
    """Get analysis of peak generation times.

    Identifies when generation load is highest by hour of day (0-23):
    - Peak hours by request volume
    - Average queue lengths during each hour
    - Performance metrics (p95 duration) by hour
    - Unique users per hour

    Useful for:
    - Capacity planning and resource allocation
    - Identifying bottleneck hours
    - Planning maintenance windows
    - Understanding user behavior patterns

    **Examples:**
    - `/api/v1/analytics/generation/peak-hours?days=30`
    - `/api/v1/analytics/generation/peak-hours?days=7`

    **Response:**
    ```json
    {
      "lookback_days": 30,
      "total_hours_analyzed": 24,
      "peak_hours": [
        {
          "hour_of_day": 14,
          "avg_requests": 85.5,
          "avg_queue_length": 3.2,
          "avg_max_queue_length": 8.5,
          "avg_p95_duration_ms": 5200,
          "avg_unique_users": 25.3,
          "data_points": 30
        },
        {
          "hour_of_day": 15,
          "avg_requests": 78.2,
          "avg_queue_length": 2.8,
          "avg_max_queue_length": 7.1,
          "avg_p95_duration_ms": 4900,
          "avg_unique_users": 22.7,
          "data_points": 30
        }
      ]
    }
    ```
    """
    try:
        service = GenerationAnalyticsService(db)
        return service.get_peak_usage_times(days=days)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get peak usage times: {str(e)}"
        )
