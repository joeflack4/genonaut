"""Route analytics and cache planning API routes.

These endpoints expose route analytics data and cache planning algorithms
as HTTP endpoints. They wrap the CLI tools (cache_analysis.py and
cache_analysis_relative.py) to provide programmatic access from other services.
"""

from typing import List, Dict, Any, Literal
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text, func
from sqlalchemy.orm import Session

from genonaut.api.dependencies import get_database_session
from genonaut.cli.cache_analysis import get_top_routes_for_caching
from genonaut.cli.cache_analysis_relative import get_top_routes_relative

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/routes/cache-priorities")
async def get_cache_priorities(
    n: int = Query(10, ge=1, le=100, description="Number of top routes to return"),
    days: int = Query(7, ge=1, le=90, description="Days of history to analyze"),
    system: Literal["absolute", "relative"] = Query(
        "absolute",
        description="Analysis system: 'absolute' (production) or 'relative' (development)"
    ),
    min_requests: int = Query(
        10,
        ge=0,
        description="Minimum avg requests/hour (absolute system only)"
    ),
    min_latency: int = Query(
        100,
        ge=0,
        description="Minimum p95 latency in ms (absolute system only)"
    ),
    db: Session = Depends(get_database_session)
):
    """Get top N routes recommended for caching.

    Supports two analysis systems:
    - **absolute**: Uses minimum thresholds for request rate and latency (production)
    - **relative**: Uses percentile-based ranking (development-friendly)

    Returns routes ranked by cache priority with detailed metrics.

    Examples:
        - /api/v1/analytics/routes/cache-priorities?n=10&system=absolute
        - /api/v1/analytics/routes/cache-priorities?n=20&system=relative&days=30
    """
    try:
        if system == "absolute":
            routes = get_top_routes_for_caching(
                n=n,
                lookback_days=days,
                min_requests_per_hour=min_requests,
                min_latency_ms=min_latency
            )
        else:  # system == "relative"
            routes = get_top_routes_relative(
                n=n,
                lookback_days=days
            )

        # Convert to JSON-serializable format
        output = []
        for route in routes:
            route_data = {
                'route': route['route'],
                'method': route['method'],
                'query_params_normalized': route.get('query_params_normalized'),
                'avg_hourly_requests': float(route['avg_hourly_requests']),
                'avg_p95_latency_ms': float(route['avg_p95_latency']),
                'avg_unique_users': float(route['avg_unique_users']),
                'success_rate': float(route['success_rate']),
                'total_requests': int(route['total_requests'])
            }

            # Add system-specific fields
            if system == "absolute":
                route_data['cache_priority_score'] = float(route['cache_priority_score'])
            else:  # relative
                route_data['priority_score'] = float(route['priority_score'])
                route_data['popularity_percentile'] = float(route['popularity_percentile'])
                route_data['latency_percentile'] = float(route['latency_percentile'])
                route_data['user_percentile'] = float(route['user_percentile'])

            output.append(route_data)

        return {
            "system": system,
            "lookback_days": days,
            "routes": output,
            "total_routes": len(output)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze cache priorities: {str(e)}"
        )


@router.get("/routes/performance-trends")
async def get_performance_trends(
    route: str = Query(..., description="Route path to analyze (e.g., /api/v1/content/unified)"),
    days: int = Query(7, ge=1, le=90, description="Days of history to analyze"),
    granularity: Literal["hourly", "daily"] = Query(
        "hourly",
        description="Data granularity: 'hourly' or 'daily'"
    ),
    db: Session = Depends(get_database_session)
):
    """Get performance trends for a specific route over time.

    Returns time-series data showing request volume, latency percentiles,
    and success rates over the specified time period.

    Useful for:
    - Identifying performance degradation over time
    - Spotting traffic patterns and spikes
    - Monitoring the impact of code changes

    Examples:
        - /api/v1/analytics/routes/performance-trends?route=/api/v1/content/unified&days=7
        - /api/v1/analytics/routes/performance-trends?route=/api/v1/tags/hierarchy&days=30&granularity=daily
    """
    try:
        if granularity == "hourly":
            # Query hourly aggregated data
            # Use UTC to ensure consistent time ranges regardless of server timezone
            query = text("""
                SELECT
                    timestamp,
                    total_requests,
                    successful_requests,
                    client_errors,
                    server_errors,
                    avg_duration_ms,
                    p50_duration_ms,
                    p95_duration_ms,
                    p99_duration_ms,
                    unique_users,
                    (successful_requests::FLOAT / NULLIF(total_requests, 0)) as success_rate
                FROM route_analytics_hourly
                WHERE route = :route
                    AND timestamp > (NOW() AT TIME ZONE 'UTC') - INTERVAL '1 day' * :days
                ORDER BY timestamp ASC
            """)
            result = db.execute(query, {'route': route, 'days': days})
        else:  # daily
            # Aggregate hourly data into daily buckets
            # For daily granularity, align to calendar day boundaries to ensure exactly N days
            # We use (days - 1) to get exactly N calendar days including today
            lookback_days = days - 1
            # For daily granularity, we use UTC to ensure consistent date boundaries
            # regardless of server timezone
            query = text("""
                SELECT
                    DATE_TRUNC('day', timestamp) as timestamp,
                    SUM(total_requests) as total_requests,
                    SUM(successful_requests) as successful_requests,
                    SUM(client_errors) as client_errors,
                    SUM(server_errors) as server_errors,
                    AVG(avg_duration_ms)::INTEGER as avg_duration_ms,
                    AVG(p50_duration_ms)::INTEGER as p50_duration_ms,
                    AVG(p95_duration_ms)::INTEGER as p95_duration_ms,
                    AVG(p99_duration_ms)::INTEGER as p99_duration_ms,
                    AVG(unique_users)::INTEGER as unique_users,
                    (SUM(successful_requests)::FLOAT / NULLIF(SUM(total_requests), 0)) as success_rate
                FROM route_analytics_hourly
                WHERE route = :route
                    AND timestamp >= DATE_TRUNC('day', (NOW() AT TIME ZONE 'UTC')) - INTERVAL '1 day' * :lookback_days
                GROUP BY DATE_TRUNC('day', timestamp)
                ORDER BY timestamp ASC
            """)
            result = db.execute(query, {'route': route, 'lookback_days': lookback_days})

        trends = []
        for row in result:
            trends.append({
                'timestamp': row.timestamp.isoformat(),
                'total_requests': int(row.total_requests),
                'successful_requests': int(row.successful_requests),
                'client_errors': int(row.client_errors),
                'server_errors': int(row.server_errors),
                'avg_duration_ms': int(row.avg_duration_ms) if row.avg_duration_ms else None,
                'p50_duration_ms': int(row.p50_duration_ms) if row.p50_duration_ms else None,
                'p95_duration_ms': int(row.p95_duration_ms) if row.p95_duration_ms else None,
                'p99_duration_ms': int(row.p99_duration_ms) if row.p99_duration_ms else None,
                'unique_users': int(row.unique_users) if row.unique_users else None,
                'success_rate': float(row.success_rate) if row.success_rate else None
            })

        return {
            "route": route,
            "granularity": granularity,
            "lookback_days": days,
            "data_points": len(trends),
            "trends": trends
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance trends: {str(e)}"
        )


@router.get("/routes/peak-hours")
async def get_peak_hours(
    route: str = Query(None, description="Filter by specific route (optional)"),
    days: int = Query(30, ge=7, le=90, description="Days of history to analyze"),
    min_requests: int = Query(50, ge=1, description="Minimum avg requests for a route to be included"),
    db: Session = Depends(get_database_session)
):
    """Get peak traffic hours analysis.

    Identifies which hours of the day have the highest traffic and latency
    for each route. Useful for planning cache warming and scaling strategies.

    Can analyze:
    - A specific route (pass route parameter)
    - All routes (omit route parameter)

    Returns hourly statistics showing when traffic peaks occur and
    which hours have the slowest performance.

    Examples:
        - /api/v1/analytics/routes/peak-hours?days=30
        - /api/v1/analytics/routes/peak-hours?route=/api/v1/content/unified&days=30
    """
    try:
        if route:
            # Analyze specific route
            query = text("""
                SELECT
                    route,
                    EXTRACT(HOUR FROM timestamp) as hour_of_day,
                    AVG(total_requests) as avg_requests,
                    AVG(p95_duration_ms) as avg_p95_latency,
                    AVG(unique_users) as avg_unique_users,
                    COUNT(*) as data_points
                FROM route_analytics_hourly
                WHERE route = :route
                    AND timestamp > NOW() - INTERVAL '1 day' * :days
                GROUP BY route, EXTRACT(HOUR FROM timestamp)
                ORDER BY avg_requests DESC
            """)
            result = db.execute(query, {'route': route, 'days': days})
        else:
            # Analyze all routes
            query = text("""
                SELECT
                    route,
                    EXTRACT(HOUR FROM timestamp) as hour_of_day,
                    AVG(total_requests) as avg_requests,
                    AVG(p95_duration_ms) as avg_p95_latency,
                    AVG(unique_users) as avg_unique_users,
                    COUNT(*) as data_points
                FROM route_analytics_hourly
                WHERE timestamp > NOW() - INTERVAL '1 day' * :days
                GROUP BY route, EXTRACT(HOUR FROM timestamp)
                HAVING AVG(total_requests) >= :min_requests
                ORDER BY route, avg_requests DESC
            """)
            result = db.execute(query, {'days': days, 'min_requests': min_requests})

        peak_hours = []
        for row in result:
            peak_hours.append({
                'route': row.route,
                'hour_of_day': int(row.hour_of_day),
                'avg_requests': float(row.avg_requests),
                'avg_p95_latency_ms': float(row.avg_p95_latency) if row.avg_p95_latency else None,
                'avg_unique_users': float(row.avg_unique_users) if row.avg_unique_users else None,
                'data_points': int(row.data_points)
            })

        return {
            "route": route,
            "lookback_days": days,
            "min_requests_threshold": min_requests,
            "total_patterns": len(peak_hours),
            "peak_hours": peak_hours
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze peak hours: {str(e)}"
        )
