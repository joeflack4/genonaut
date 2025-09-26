"""Metrics and monitoring service for ComfyUI operations."""

import time
import threading
from collections import defaultdict, deque
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics we can track."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class MetricsService:
    """Service for collecting and reporting metrics."""

    def __init__(self, max_history: int = 1000):
        """Initialize metrics service.

        Args:
            max_history: Maximum number of historical data points to keep
        """
        self.max_history = max_history
        self.lock = threading.RLock()

        # Metric storage
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.timers: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))

        # Generation-specific metrics
        self.generation_stats = {
            "total_requests": 0,
            "successful_generations": 0,
            "failed_generations": 0,
            "cancelled_generations": 0,
            "average_generation_time": 0.0,
            "active_generations": 0,
            "queue_length": 0
        }

        # Performance metrics
        self.performance_metrics = {
            "response_times": deque(maxlen=max_history),
            "error_rates": deque(maxlen=max_history),
            "throughput": deque(maxlen=max_history),
            "resource_usage": {}
        }

        # User activity metrics
        self.user_activity = {
            "active_users": set(),
            "user_generation_counts": defaultdict(int),
            "user_last_activity": {},
            "hourly_activity": defaultdict(int)
        }

    def increment_counter(self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric.

        Args:
            name: Counter name
            value: Value to increment by
            labels: Optional labels for the metric
        """
        with self.lock:
            metric_key = self._build_metric_key(name, labels)
            self.counters[metric_key] += value
            logger.debug(f"Counter '{metric_key}' incremented by {value} to {self.counters[metric_key]}")

    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric value.

        Args:
            name: Gauge name
            value: Gauge value
            labels: Optional labels for the metric
        """
        with self.lock:
            metric_key = self._build_metric_key(name, labels)
            self.gauges[metric_key] = value
            logger.debug(f"Gauge '{metric_key}' set to {value}")

    def record_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record a value in a histogram.

        Args:
            name: Histogram name
            value: Value to record
            labels: Optional labels for the metric
        """
        with self.lock:
            metric_key = self._build_metric_key(name, labels)
            self.histograms[metric_key].append({
                "value": value,
                "timestamp": time.time()
            })
            logger.debug(f"Histogram '{metric_key}' recorded value {value}")

    def start_timer(self, name: str, labels: Optional[Dict[str, str]] = None) -> Callable[[], None]:
        """Start a timer and return a function to stop it.

        Args:
            name: Timer name
            labels: Optional labels for the metric

        Returns:
            Function to call to stop the timer
        """
        start_time = time.time()
        metric_key = self._build_metric_key(name, labels)

        def stop_timer():
            duration = time.time() - start_time
            with self.lock:
                self.timers[metric_key].append({
                    "duration": duration,
                    "timestamp": start_time
                })
            logger.debug(f"Timer '{metric_key}' recorded duration {duration:.3f}s")

        return stop_timer

    def record_generation_request(self, user_id: str, generation_type: str = "standard") -> None:
        """Record a new generation request.

        Args:
            user_id: ID of requesting user
            generation_type: Type of generation
        """
        with self.lock:
            self.generation_stats["total_requests"] += 1
            self.generation_stats["active_generations"] += 1

            # Update user activity
            self.user_activity["active_users"].add(user_id)
            self.user_activity["user_generation_counts"][user_id] += 1
            self.user_activity["user_last_activity"][user_id] = datetime.utcnow()

            # Update hourly activity
            current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
            self.user_activity["hourly_activity"][current_hour] += 1

            # Increment counter with labels
            self.increment_counter("generation_requests", labels={"type": generation_type, "user": user_id})

    def record_generation_completion(
        self,
        user_id: str,
        success: bool,
        duration: float,
        error_type: Optional[str] = None
    ) -> None:
        """Record completion of a generation request.

        Args:
            user_id: ID of requesting user
            success: Whether generation was successful
            duration: Generation duration in seconds
            error_type: Type of error if failed
        """
        with self.lock:
            self.generation_stats["active_generations"] = max(0, self.generation_stats["active_generations"] - 1)

            if success:
                self.generation_stats["successful_generations"] += 1
                self.increment_counter("successful_generations", labels={"user": user_id})
            else:
                self.generation_stats["failed_generations"] += 1
                self.increment_counter("failed_generations", labels={"user": user_id, "error_type": error_type or "unknown"})

            # Update average generation time
            total_completed = self.generation_stats["successful_generations"] + self.generation_stats["failed_generations"]
            if total_completed > 0:
                current_avg = self.generation_stats["average_generation_time"]
                self.generation_stats["average_generation_time"] = (
                    (current_avg * (total_completed - 1) + duration) / total_completed
                )

            # Record timing
            self.record_histogram("generation_duration", duration, labels={"success": str(success)})

    def record_generation_cancelled(self, user_id: str) -> None:
        """Record cancellation of a generation request.

        Args:
            user_id: ID of requesting user
        """
        with self.lock:
            self.generation_stats["cancelled_generations"] += 1
            self.generation_stats["active_generations"] = max(0, self.generation_stats["active_generations"] - 1)
            self.increment_counter("cancelled_generations", labels={"user": user_id})

    def update_queue_length(self, length: int) -> None:
        """Update the current queue length.

        Args:
            length: Current queue length
        """
        with self.lock:
            self.generation_stats["queue_length"] = length
            self.set_gauge("queue_length", float(length))

    def record_response_time(self, endpoint: str, duration: float) -> None:
        """Record API response time.

        Args:
            endpoint: API endpoint name
            duration: Response time in seconds
        """
        with self.lock:
            self.performance_metrics["response_times"].append({
                "endpoint": endpoint,
                "duration": duration,
                "timestamp": time.time()
            })
            self.record_histogram("api_response_time", duration, labels={"endpoint": endpoint})

    def record_error_rate(self, endpoint: str, error_count: int, total_requests: int) -> None:
        """Record error rate for an endpoint.

        Args:
            endpoint: API endpoint name
            error_count: Number of errors
            total_requests: Total requests
        """
        if total_requests > 0:
            error_rate = error_count / total_requests
            with self.lock:
                self.performance_metrics["error_rates"].append({
                    "endpoint": endpoint,
                    "error_rate": error_rate,
                    "timestamp": time.time()
                })
                self.set_gauge("error_rate", error_rate, labels={"endpoint": endpoint})

    def update_resource_usage(self, resource_type: str, usage: float) -> None:
        """Update resource usage metrics.

        Args:
            resource_type: Type of resource (cpu, memory, disk, etc.)
            usage: Usage percentage (0-100)
        """
        with self.lock:
            self.performance_metrics["resource_usage"][resource_type] = {
                "usage": usage,
                "timestamp": time.time()
            }
            self.set_gauge("resource_usage", usage, labels={"type": resource_type})

    def get_generation_success_rate(self, time_window_hours: int = 24) -> float:
        """Calculate generation success rate over a time window.

        Args:
            time_window_hours: Time window in hours

        Returns:
            Success rate as percentage (0-100)
        """
        with self.lock:
            total = self.generation_stats["successful_generations"] + self.generation_stats["failed_generations"]
            if total == 0:
                return 0.0
            return (self.generation_stats["successful_generations"] / total) * 100

    def get_average_response_time(self, endpoint: Optional[str] = None, minutes: int = 60) -> float:
        """Get average response time over a time period.

        Args:
            endpoint: Specific endpoint to check (None for all)
            minutes: Time window in minutes

        Returns:
            Average response time in seconds
        """
        with self.lock:
            cutoff_time = time.time() - (minutes * 60)
            relevant_times = []

            for entry in self.performance_metrics["response_times"]:
                if entry["timestamp"] >= cutoff_time:
                    if endpoint is None or entry["endpoint"] == endpoint:
                        relevant_times.append(entry["duration"])

            if not relevant_times:
                return 0.0

            return sum(relevant_times) / len(relevant_times)

    def get_active_user_count(self, minutes: int = 60) -> int:
        """Get count of active users in the last N minutes.

        Args:
            minutes: Time window in minutes

        Returns:
            Number of active users
        """
        with self.lock:
            cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
            active_count = 0

            for user_id, last_activity in self.user_activity["user_last_activity"].items():
                if last_activity >= cutoff_time:
                    active_count += 1

            return active_count

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a comprehensive metrics summary.

        Returns:
            Dictionary with all current metrics
        """
        with self.lock:
            # Calculate derived metrics
            success_rate = self.get_generation_success_rate()
            avg_response_time = self.get_average_response_time()
            active_users = self.get_active_user_count()

            return {
                "generation_metrics": {
                    **self.generation_stats,
                    "success_rate_percentage": success_rate
                },
                "performance_metrics": {
                    "average_response_time": avg_response_time,
                    "current_resource_usage": self.performance_metrics["resource_usage"]
                },
                "user_activity": {
                    "active_users_count": active_users,
                    "total_registered_users": len(self.user_activity["user_generation_counts"]),
                    "total_user_generations": sum(self.user_activity["user_generation_counts"].values())
                },
                "system_health": {
                    "queue_length": self.generation_stats["queue_length"],
                    "active_generations": self.generation_stats["active_generations"],
                    "error_rate": self._calculate_recent_error_rate()
                }
            }

    def get_alerts(self) -> List[Dict[str, Any]]:
        """Get current alerts based on metric thresholds.

        Returns:
            List of alert dictionaries
        """
        alerts = []

        with self.lock:
            # High error rate alert
            error_rate = self._calculate_recent_error_rate()
            if error_rate > 0.1:  # 10% error rate threshold
                alerts.append({
                    "type": "high_error_rate",
                    "severity": "high",
                    "message": f"Error rate is {error_rate:.1%}, exceeding 10% threshold",
                    "metric_value": error_rate
                })

            # Long queue alert
            queue_length = self.generation_stats["queue_length"]
            if queue_length > 50:
                alerts.append({
                    "type": "long_queue",
                    "severity": "medium",
                    "message": f"Generation queue length is {queue_length}, exceeding 50 requests",
                    "metric_value": queue_length
                })

            # Slow response time alert
            avg_response = self.get_average_response_time(minutes=15)
            if avg_response > 5.0:  # 5 second threshold
                alerts.append({
                    "type": "slow_response",
                    "severity": "medium",
                    "message": f"Average response time is {avg_response:.2f}s, exceeding 5s threshold",
                    "metric_value": avg_response
                })

            # Low success rate alert
            success_rate = self.get_generation_success_rate(time_window_hours=1)
            if success_rate < 80 and self.generation_stats["total_requests"] > 10:
                alerts.append({
                    "type": "low_success_rate",
                    "severity": "high",
                    "message": f"Generation success rate is {success_rate:.1f}%, below 80% threshold",
                    "metric_value": success_rate
                })

        return alerts

    def _calculate_recent_error_rate(self, minutes: int = 15) -> float:
        """Calculate recent error rate.

        Args:
            minutes: Time window in minutes

        Returns:
            Error rate as decimal (0-1)
        """
        cutoff_time = time.time() - (minutes * 60)
        recent_errors = []

        for entry in self.performance_metrics["error_rates"]:
            if entry["timestamp"] >= cutoff_time:
                recent_errors.append(entry["error_rate"])

        if not recent_errors:
            return 0.0

        return sum(recent_errors) / len(recent_errors)

    def _build_metric_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
        """Build a metric key with labels.

        Args:
            name: Metric name
            labels: Optional labels

        Returns:
            Formatted metric key
        """
        if not labels:
            return name

        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def clear_metrics(self) -> None:
        """Clear all metrics (useful for testing)."""
        with self.lock:
            self.counters.clear()
            self.gauges.clear()
            self.histograms.clear()
            self.timers.clear()

            self.generation_stats = {
                "total_requests": 0,
                "successful_generations": 0,
                "failed_generations": 0,
                "cancelled_generations": 0,
                "average_generation_time": 0.0,
                "active_generations": 0,
                "queue_length": 0
            }

            self.performance_metrics = {
                "response_times": deque(maxlen=self.max_history),
                "error_rates": deque(maxlen=self.max_history),
                "throughput": deque(maxlen=self.max_history),
                "resource_usage": {}
            }

            self.user_activity = {
                "active_users": set(),
                "user_generation_counts": defaultdict(int),
                "user_last_activity": {},
                "hourly_activity": defaultdict(int)
            }


# Global metrics service instance
_metrics_service = MetricsService()


def get_metrics_service() -> MetricsService:
    """Get the global metrics service instance."""
    return _metrics_service


def track_generation_request(user_id: str, generation_type: str = "standard"):
    """Convenience function to track generation requests."""
    _metrics_service.record_generation_request(user_id, generation_type)


def track_generation_completion(user_id: str, success: bool, duration: float, error_type: Optional[str] = None):
    """Convenience function to track generation completions."""
    _metrics_service.record_generation_completion(user_id, success, duration, error_type)


def timer(name: str, labels: Optional[Dict[str, str]] = None):
    """Context manager for timing operations."""
    class TimerContext:
        def __init__(self, timer_name: str, timer_labels: Optional[Dict[str, str]]):
            self.name = timer_name
            self.labels = timer_labels
            self.stop_func = None

        def __enter__(self):
            self.stop_func = _metrics_service.start_timer(self.name, self.labels)
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.stop_func:
                self.stop_func()

    return TimerContext(name, labels)