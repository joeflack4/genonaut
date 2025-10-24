"""Service for querying generation analytics data.

This service provides methods for analyzing generation events and metrics
from PostgreSQL tables populated by Celery background tasks.

The service queries two main tables:
- generation_events: Raw event data (requests, completions, cancellations)
- generation_metrics_hourly: Pre-aggregated hourly statistics
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Literal
from sqlalchemy import text
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


class GenerationAnalyticsService:
    """Service for generation analytics queries."""

    def __init__(self, db: Session):
        """Initialize service with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def get_generation_overview(self, days: int = 7) -> Dict[str, Any]:
        """Get high-level overview of generation activity.

        Provides dashboard-style metrics for the specified time period:
        - Total requests, completions, failures, cancellations
        - Success rate percentage
        - Average/p50/p95/p99 duration
        - Unique users count
        - Total images generated

        Args:
            days: Number of days to look back (default: 7)

        Returns:
            Dictionary with overview metrics

        Example:
            >>> service = GenerationAnalyticsService(db)
            >>> overview = service.get_generation_overview(days=30)
            >>> print(f"Success rate: {overview['success_rate_pct']:.1f}%")
        """
        # Query aggregated hourly data for the time period
        query = text("""
            SELECT
                SUM(total_requests) as total_requests,
                SUM(successful_generations) as successful_generations,
                SUM(failed_generations) as failed_generations,
                SUM(cancelled_generations) as cancelled_generations,
                AVG(avg_duration_ms)::INTEGER as avg_duration_ms,
                AVG(p50_duration_ms)::INTEGER as p50_duration_ms,
                AVG(p95_duration_ms)::INTEGER as p95_duration_ms,
                AVG(p99_duration_ms)::INTEGER as p99_duration_ms,
                SUM(total_images_generated) as total_images_generated,
                COUNT(DISTINCT timestamp) as hours_with_data,
                MAX(timestamp) as latest_data_timestamp
            FROM generation_metrics_hourly
            WHERE timestamp >= (NOW() AT TIME ZONE 'UTC') - INTERVAL '1 day' * :days
        """)

        result = self.db.execute(query, {'days': days}).fetchone()

        if not result or not result.total_requests:
            return {
                'lookback_days': days,
                'total_requests': 0,
                'successful_generations': 0,
                'failed_generations': 0,
                'cancelled_generations': 0,
                'success_rate_pct': 0.0,
                'avg_duration_ms': None,
                'p50_duration_ms': None,
                'p95_duration_ms': None,
                'p99_duration_ms': None,
                'total_images_generated': 0,
                'hours_with_data': 0,
                'latest_data_timestamp': None
            }

        # Calculate success rate percentage
        total_requests = int(result.total_requests)
        successful = int(result.successful_generations) if result.successful_generations else 0
        success_rate_pct = (successful / total_requests * 100) if total_requests > 0 else 0.0

        return {
            'lookback_days': days,
            'total_requests': total_requests,
            'successful_generations': successful,
            'failed_generations': int(result.failed_generations) if result.failed_generations else 0,
            'cancelled_generations': int(result.cancelled_generations) if result.cancelled_generations else 0,
            'success_rate_pct': round(success_rate_pct, 2),
            'avg_duration_ms': int(result.avg_duration_ms) if result.avg_duration_ms else None,
            'p50_duration_ms': int(result.p50_duration_ms) if result.p50_duration_ms else None,
            'p95_duration_ms': int(result.p95_duration_ms) if result.p95_duration_ms else None,
            'p99_duration_ms': int(result.p99_duration_ms) if result.p99_duration_ms else None,
            'total_images_generated': int(result.total_images_generated) if result.total_images_generated else 0,
            'hours_with_data': int(result.hours_with_data) if result.hours_with_data else 0,
            'latest_data_timestamp': result.latest_data_timestamp.isoformat() if result.latest_data_timestamp else None
        }

    def get_generation_trends(
        self,
        days: int = 7,
        interval: Literal["hourly", "daily"] = "hourly"
    ) -> Dict[str, Any]:
        """Get time-series trends for generation metrics.

        Returns time-series data showing generation activity over time.
        Useful for identifying patterns, spikes, and performance changes.

        Args:
            days: Number of days to look back (default: 7)
            interval: Granularity - "hourly" or "daily" (default: "hourly")

        Returns:
            Dictionary with trend data including:
            - Array of time-series data points
            - Metadata about the query

        Example:
            >>> trends = service.get_generation_trends(days=30, interval="daily")
            >>> for point in trends['data_points']:
            ...     print(f"{point['timestamp']}: {point['total_requests']} requests")
        """
        if interval == "hourly":
            # Return hourly data directly from the aggregated table
            query = text("""
                SELECT
                    timestamp,
                    total_requests,
                    successful_generations,
                    failed_generations,
                    cancelled_generations,
                    avg_duration_ms,
                    p50_duration_ms,
                    p95_duration_ms,
                    p99_duration_ms,
                    unique_users,
                    avg_queue_length,
                    max_queue_length,
                    total_images_generated,
                    (successful_generations::FLOAT / NULLIF(total_requests, 0)) as success_rate
                FROM generation_metrics_hourly
                WHERE timestamp >= (NOW() AT TIME ZONE 'UTC') - INTERVAL '1 day' * :days
                ORDER BY timestamp ASC
            """)
            result = self.db.execute(query, {'days': days})
        else:  # daily
            # Aggregate hourly data into daily buckets
            lookback_days = days - 1
            query = text("""
                SELECT
                    DATE_TRUNC('day', timestamp) as timestamp,
                    SUM(total_requests) as total_requests,
                    SUM(successful_generations) as successful_generations,
                    SUM(failed_generations) as failed_generations,
                    SUM(cancelled_generations) as cancelled_generations,
                    AVG(avg_duration_ms)::INTEGER as avg_duration_ms,
                    AVG(p50_duration_ms)::INTEGER as p50_duration_ms,
                    AVG(p95_duration_ms)::INTEGER as p95_duration_ms,
                    AVG(p99_duration_ms)::INTEGER as p99_duration_ms,
                    AVG(unique_users)::INTEGER as unique_users,
                    AVG(avg_queue_length) as avg_queue_length,
                    AVG(max_queue_length)::INTEGER as max_queue_length,
                    SUM(total_images_generated) as total_images_generated,
                    (SUM(successful_generations)::FLOAT / NULLIF(SUM(total_requests), 0)) as success_rate
                FROM generation_metrics_hourly
                WHERE timestamp >= DATE_TRUNC('day', (NOW() AT TIME ZONE 'UTC')) - INTERVAL '1 day' * :lookback_days
                GROUP BY DATE_TRUNC('day', timestamp)
                ORDER BY timestamp ASC
            """)
            result = self.db.execute(query, {'lookback_days': lookback_days})

        # Format results
        data_points = []
        for row in result:
            data_points.append({
                'timestamp': row.timestamp.isoformat(),
                'total_requests': int(row.total_requests) if row.total_requests else 0,
                'successful_generations': int(row.successful_generations) if row.successful_generations else 0,
                'failed_generations': int(row.failed_generations) if row.failed_generations else 0,
                'cancelled_generations': int(row.cancelled_generations) if row.cancelled_generations else 0,
                'avg_duration_ms': int(row.avg_duration_ms) if row.avg_duration_ms else None,
                'p50_duration_ms': int(row.p50_duration_ms) if row.p50_duration_ms else None,
                'p95_duration_ms': int(row.p95_duration_ms) if row.p95_duration_ms else None,
                'p99_duration_ms': int(row.p99_duration_ms) if row.p99_duration_ms else None,
                'unique_users': int(row.unique_users) if row.unique_users else None,
                'avg_queue_length': float(row.avg_queue_length) if row.avg_queue_length else None,
                'max_queue_length': int(row.max_queue_length) if row.max_queue_length else None,
                'total_images_generated': int(row.total_images_generated) if row.total_images_generated else 0,
                'success_rate': float(row.success_rate) if row.success_rate else None
            })

        return {
            'interval': interval,
            'lookback_days': days,
            'total_data_points': len(data_points),
            'data_points': data_points
        }

    def get_user_generation_analytics(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get generation analytics for a specific user.

        Analyzes a user's generation history including:
        - Total generations and success rate
        - Average duration and performance metrics
        - Recent activity timeline
        - Common failure patterns

        Args:
            user_id: UUID of the user to analyze
            days: Number of days to look back (default: 30)

        Returns:
            Dictionary with user-specific analytics

        Example:
            >>> analytics = service.get_user_generation_analytics(
            ...     user_id="550e8400-e29b-41d4-a716-446655440000",
            ...     days=30
            ... )
            >>> print(f"User success rate: {analytics['success_rate_pct']:.1f}%")
        """
        # Query user-specific events from raw events table
        query = text("""
            WITH user_events AS (
                SELECT
                    event_type,
                    timestamp,
                    duration_ms,
                    success,
                    error_type,
                    generation_type,
                    model_checkpoint,
                    batch_size
                FROM generation_events
                WHERE user_id = :user_id
                    AND timestamp >= (NOW() AT TIME ZONE 'UTC') - INTERVAL '1 day' * :days
            ),
            summary AS (
                SELECT
                    COUNT(*) FILTER (WHERE event_type = 'request') as total_requests,
                    COUNT(*) FILTER (WHERE event_type = 'completion' AND success = true) as successful,
                    COUNT(*) FILTER (WHERE event_type = 'completion' AND success = false) as failed,
                    COUNT(*) FILTER (WHERE event_type = 'cancellation') as cancelled,
                    AVG(duration_ms) FILTER (WHERE event_type = 'completion' AND duration_ms IS NOT NULL)::INTEGER as avg_duration_ms,
                    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY duration_ms) FILTER (WHERE event_type = 'completion' AND duration_ms IS NOT NULL)::INTEGER as p50_duration_ms,
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) FILTER (WHERE event_type = 'completion' AND duration_ms IS NOT NULL)::INTEGER as p95_duration_ms,
                    MAX(timestamp) as last_generation_at,
                    MIN(timestamp) as first_generation_at
                FROM user_events
            ),
            recent_activity AS (
                SELECT
                    timestamp,
                    event_type,
                    duration_ms,
                    success,
                    error_type,
                    generation_type
                FROM user_events
                WHERE event_type = 'completion'
                ORDER BY timestamp DESC
                LIMIT 20
            ),
            failure_breakdown AS (
                SELECT
                    error_type,
                    COUNT(*) as error_count
                FROM user_events
                WHERE event_type = 'completion' AND success = false AND error_type IS NOT NULL
                GROUP BY error_type
                ORDER BY error_count DESC
            )
            SELECT
                (SELECT row_to_json(summary.*) FROM summary) as summary,
                (SELECT json_agg(recent_activity.*) FROM recent_activity) as recent_activity,
                (SELECT json_agg(failure_breakdown.*) FROM failure_breakdown) as failure_breakdown
        """)

        result = self.db.execute(query, {'user_id': user_id, 'days': days}).fetchone()

        # Parse results
        summary = result.summary if result.summary else {}
        recent_activity = result.recent_activity if result.recent_activity else []
        failure_breakdown = result.failure_breakdown if result.failure_breakdown else []

        # Calculate success rate
        total_requests = summary.get('total_requests', 0)
        successful = summary.get('successful', 0)
        success_rate_pct = (successful / total_requests * 100) if total_requests > 0 else 0.0

        return {
            'user_id': user_id,
            'lookback_days': days,
            'total_requests': total_requests,
            'successful_generations': successful,
            'failed_generations': summary.get('failed', 0),
            'cancelled_generations': summary.get('cancelled', 0),
            'success_rate_pct': round(success_rate_pct, 2),
            'avg_duration_ms': summary.get('avg_duration_ms'),
            'p50_duration_ms': summary.get('p50_duration_ms'),
            'p95_duration_ms': summary.get('p95_duration_ms'),
            'last_generation_at': summary.get('last_generation_at').isoformat() if summary.get('last_generation_at') else None,
            'first_generation_at': summary.get('first_generation_at').isoformat() if summary.get('first_generation_at') else None,
            'recent_activity': [
                {
                    'timestamp': activity['timestamp'],
                    'event_type': activity['event_type'],
                    'duration_ms': activity['duration_ms'],
                    'success': activity['success'],
                    'error_type': activity['error_type'],
                    'generation_type': activity['generation_type']
                }
                for activity in recent_activity
            ],
            'failure_breakdown': [
                {
                    'error_type': failure['error_type'],
                    'count': failure['error_count']
                }
                for failure in failure_breakdown
            ]
        }

    def get_model_performance(self, days: int = 30) -> Dict[str, Any]:
        """Get performance comparison across different models.

        Analyzes generation performance broken down by model checkpoint:
        - Total generations per model
        - Success rates
        - Average durations
        - Performance trends

        Args:
            days: Number of days to look back (default: 30)

        Returns:
            Dictionary with model performance comparison

        Example:
            >>> models = service.get_model_performance(days=30)
            >>> for model in models['models']:
            ...     print(f"{model['model']}: {model['success_rate_pct']:.1f}% success")
        """
        query = text("""
            SELECT
                model_checkpoint,
                COUNT(*) FILTER (WHERE event_type = 'completion') as total_generations,
                COUNT(*) FILTER (WHERE event_type = 'completion' AND success = true) as successful,
                COUNT(*) FILTER (WHERE event_type = 'completion' AND success = false) as failed,
                AVG(duration_ms) FILTER (WHERE event_type = 'completion' AND duration_ms IS NOT NULL)::INTEGER as avg_duration_ms,
                PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY duration_ms) FILTER (WHERE event_type = 'completion' AND duration_ms IS NOT NULL)::INTEGER as p50_duration_ms,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) FILTER (WHERE event_type = 'completion' AND duration_ms IS NOT NULL)::INTEGER as p95_duration_ms,
                MAX(timestamp) as last_used_at
            FROM generation_events
            WHERE timestamp >= (NOW() AT TIME ZONE 'UTC') - INTERVAL '1 day' * :days
                AND model_checkpoint IS NOT NULL
            GROUP BY model_checkpoint
            ORDER BY total_generations DESC
        """)

        result = self.db.execute(query, {'days': days})

        models = []
        for row in result:
            total_generations = int(row.total_generations) if row.total_generations else 0
            successful = int(row.successful) if row.successful else 0
            success_rate_pct = (successful / total_generations * 100) if total_generations > 0 else 0.0

            models.append({
                'model_checkpoint': row.model_checkpoint,
                'total_generations': total_generations,
                'successful_generations': successful,
                'failed_generations': int(row.failed) if row.failed else 0,
                'success_rate_pct': round(success_rate_pct, 2),
                'avg_duration_ms': int(row.avg_duration_ms) if row.avg_duration_ms else None,
                'p50_duration_ms': int(row.p50_duration_ms) if row.p50_duration_ms else None,
                'p95_duration_ms': int(row.p95_duration_ms) if row.p95_duration_ms else None,
                'last_used_at': row.last_used_at.isoformat() if row.last_used_at else None
            })

        return {
            'lookback_days': days,
            'total_models': len(models),
            'models': models
        }

    def get_failure_analysis(self, days: int = 7) -> Dict[str, Any]:
        """Get detailed analysis of generation failures.

        Analyzes failure patterns to help identify issues:
        - Breakdown by error type
        - Failure rate trends over time
        - Common error messages
        - Time-based patterns (certain hours with more failures)

        Args:
            days: Number of days to look back (default: 7)

        Returns:
            Dictionary with failure analysis data

        Example:
            >>> failures = service.get_failure_analysis(days=7)
            >>> for error in failures['error_types']:
            ...     print(f"{error['error_type']}: {error['count']} failures")
        """
        # Query error type breakdown
        error_type_query = text("""
            SELECT
                error_type,
                COUNT(*) as error_count,
                AVG(duration_ms)::INTEGER as avg_duration_ms,
                array_agg(DISTINCT error_message) FILTER (WHERE error_message IS NOT NULL) as sample_messages
            FROM generation_events
            WHERE event_type = 'completion'
                AND success = false
                AND timestamp >= (NOW() AT TIME ZONE 'UTC') - INTERVAL '1 day' * :days
            GROUP BY error_type
            ORDER BY error_count DESC
        """)

        error_types_result = self.db.execute(error_type_query, {'days': days})

        # Query failure trends over time (daily)
        trends_query = text("""
            SELECT
                DATE_TRUNC('day', timestamp) as day,
                COUNT(*) FILTER (WHERE event_type = 'completion') as total_completions,
                COUNT(*) FILTER (WHERE event_type = 'completion' AND success = false) as failures,
                (COUNT(*) FILTER (WHERE event_type = 'completion' AND success = false)::FLOAT /
                 NULLIF(COUNT(*) FILTER (WHERE event_type = 'completion'), 0)) as failure_rate
            FROM generation_events
            WHERE timestamp >= (NOW() AT TIME ZONE 'UTC') - INTERVAL '1 day' * :days
            GROUP BY DATE_TRUNC('day', timestamp)
            ORDER BY day ASC
        """)

        trends_result = self.db.execute(trends_query, {'days': days})

        # Format error types
        error_types = []
        for row in error_types_result:
            # Limit sample messages to first 3
            sample_messages = row.sample_messages[:3] if row.sample_messages else []

            error_types.append({
                'error_type': row.error_type,
                'count': int(row.error_count),
                'avg_duration_ms': int(row.avg_duration_ms) if row.avg_duration_ms else None,
                'sample_messages': sample_messages
            })

        # Format failure trends
        failure_trends = []
        for row in trends_result:
            failure_trends.append({
                'date': row.day.isoformat(),
                'total_completions': int(row.total_completions) if row.total_completions else 0,
                'failures': int(row.failures) if row.failures else 0,
                'failure_rate': float(row.failure_rate) if row.failure_rate else 0.0
            })

        return {
            'lookback_days': days,
            'total_error_types': len(error_types),
            'error_types': error_types,
            'failure_trends': failure_trends
        }

    def get_peak_usage_times(self, days: int = 30) -> Dict[str, Any]:
        """Get analysis of peak generation times.

        Identifies when generation load is highest:
        - Peak hours by request volume
        - Peak hours by queue length
        - Performance during peak vs off-peak times

        Useful for capacity planning and identifying bottlenecks.

        Args:
            days: Number of days to look back (default: 30)

        Returns:
            Dictionary with peak usage analysis

        Example:
            >>> peaks = service.get_peak_usage_times(days=30)
            >>> for hour in peaks['peak_hours']:
            ...     print(f"Hour {hour['hour_of_day']}: {hour['avg_requests']} requests")
        """
        query = text("""
            SELECT
                EXTRACT(HOUR FROM timestamp) as hour_of_day,
                AVG(total_requests) as avg_requests,
                AVG(avg_queue_length) as avg_queue_length,
                AVG(max_queue_length) as avg_max_queue_length,
                AVG(p95_duration_ms) as avg_p95_duration_ms,
                AVG(unique_users) as avg_unique_users,
                COUNT(*) as data_points
            FROM generation_metrics_hourly
            WHERE timestamp >= (NOW() AT TIME ZONE 'UTC') - INTERVAL '1 day' * :days
            GROUP BY EXTRACT(HOUR FROM timestamp)
            ORDER BY avg_requests DESC
        """)

        result = self.db.execute(query, {'days': days})

        peak_hours = []
        for row in result:
            peak_hours.append({
                'hour_of_day': int(row.hour_of_day),
                'avg_requests': float(row.avg_requests) if row.avg_requests else 0.0,
                'avg_queue_length': float(row.avg_queue_length) if row.avg_queue_length else None,
                'avg_max_queue_length': float(row.avg_max_queue_length) if row.avg_max_queue_length else None,
                'avg_p95_duration_ms': float(row.avg_p95_duration_ms) if row.avg_p95_duration_ms else None,
                'avg_unique_users': float(row.avg_unique_users) if row.avg_unique_users else None,
                'data_points': int(row.data_points)
            })

        return {
            'lookback_days': days,
            'total_hours_analyzed': len(peak_hours),
            'peak_hours': peak_hours
        }
