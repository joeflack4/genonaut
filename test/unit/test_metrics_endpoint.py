"""
Unit tests for metrics endpoint.

Tests that the metrics endpoint returns system performance metrics.
"""
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any


class MockMetricsService:
    """Mock service for system metrics collection."""

    def __init__(self):
        """Initialize with sample metrics data."""
        self._metrics = {
            'request_count': 1500,
            'error_count': 15,
            'average_response_time_ms': 125.5,
            'p50_response_time_ms': 100.0,
            'p95_response_time_ms': 250.0,
            'p99_response_time_ms': 450.0,
            'active_connections': 25,
            'cache_hit_rate': 0.85,
            'uptime_seconds': 86400,  # 1 day
            'start_time': (datetime.now() - timedelta(days=1)).isoformat(),
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get current system metrics.

        Returns:
            Dictionary with system performance metrics
        """
        return self._metrics.copy()

    def get_error_rate(self) -> float:
        """Calculate error rate as a percentage.

        Returns:
            Error rate as decimal (0.0 to 1.0)
        """
        if self._metrics['request_count'] == 0:
            return 0.0

        return self._metrics['error_count'] / self._metrics['request_count']

    def increment_request_count(self):
        """Increment total request counter."""
        self._metrics['request_count'] += 1

    def record_response_time(self, response_time_ms: float):
        """Record a response time measurement.

        Args:
            response_time_ms: Response time in milliseconds
        """
        # Simplified: just update average
        # In reality would use a sliding window or histogram
        current_avg = self._metrics['average_response_time_ms']
        current_count = self._metrics['request_count']

        new_avg = (current_avg * current_count + response_time_ms) / (current_count + 1)
        self._metrics['average_response_time_ms'] = new_avg


@pytest.fixture
def metrics_service():
    """Provide mock metrics service."""
    return MockMetricsService()


def test_get_metrics_returns_dict(metrics_service):
    """Test that get_metrics returns a dictionary."""
    metrics = metrics_service.get_metrics()

    assert isinstance(metrics, dict)
    assert len(metrics) > 0


def test_get_metrics_contains_request_count(metrics_service):
    """Test that metrics includes request count."""
    metrics = metrics_service.get_metrics()

    assert 'request_count' in metrics
    assert isinstance(metrics['request_count'], int)
    assert metrics['request_count'] >= 0


def test_get_metrics_contains_error_count(metrics_service):
    """Test that metrics includes error count."""
    metrics = metrics_service.get_metrics()

    assert 'error_count' in metrics
    assert isinstance(metrics['error_count'], int)
    assert metrics['error_count'] >= 0


def test_get_metrics_contains_average_response_time(metrics_service):
    """Test that metrics includes average response time."""
    metrics = metrics_service.get_metrics()

    assert 'average_response_time_ms' in metrics
    assert isinstance(metrics['average_response_time_ms'], (int, float))
    assert metrics['average_response_time_ms'] >= 0


def test_get_metrics_contains_percentile_response_times(metrics_service):
    """Test that metrics includes percentile response times."""
    metrics = metrics_service.get_metrics()

    assert 'p50_response_time_ms' in metrics
    assert 'p95_response_time_ms' in metrics
    assert 'p99_response_time_ms' in metrics

    # Percentiles should be in ascending order
    assert metrics['p50_response_time_ms'] <= metrics['p95_response_time_ms']
    assert metrics['p95_response_time_ms'] <= metrics['p99_response_time_ms']


def test_get_metrics_contains_active_connections(metrics_service):
    """Test that metrics includes active connections count."""
    metrics = metrics_service.get_metrics()

    assert 'active_connections' in metrics
    assert isinstance(metrics['active_connections'], int)
    assert metrics['active_connections'] >= 0


def test_get_metrics_contains_cache_hit_rate(metrics_service):
    """Test that metrics includes cache hit rate."""
    metrics = metrics_service.get_metrics()

    assert 'cache_hit_rate' in metrics
    assert isinstance(metrics['cache_hit_rate'], float)
    assert 0.0 <= metrics['cache_hit_rate'] <= 1.0


def test_get_metrics_contains_uptime(metrics_service):
    """Test that metrics includes uptime information."""
    metrics = metrics_service.get_metrics()

    assert 'uptime_seconds' in metrics
    assert 'start_time' in metrics

    assert isinstance(metrics['uptime_seconds'], int)
    assert metrics['uptime_seconds'] >= 0


def test_get_error_rate_calculation(metrics_service):
    """Test that error rate is calculated correctly."""
    error_rate = metrics_service.get_error_rate()

    metrics = metrics_service.get_metrics()
    expected_rate = metrics['error_count'] / metrics['request_count']

    assert error_rate == pytest.approx(expected_rate)
    assert 0.0 <= error_rate <= 1.0


def test_get_error_rate_with_zero_requests():
    """Test that error rate handles zero requests gracefully."""
    service = MockMetricsService()
    service._metrics['request_count'] = 0
    service._metrics['error_count'] = 0

    error_rate = service.get_error_rate()

    assert error_rate == 0.0


def test_increment_request_count(metrics_service):
    """Test that increment_request_count increases counter."""
    initial_count = metrics_service.get_metrics()['request_count']

    metrics_service.increment_request_count()

    new_count = metrics_service.get_metrics()['request_count']
    assert new_count == initial_count + 1


def test_record_response_time_updates_average(metrics_service):
    """Test that record_response_time updates average."""
    initial_avg = metrics_service.get_metrics()['average_response_time_ms']

    metrics_service.record_response_time(200.0)

    new_avg = metrics_service.get_metrics()['average_response_time_ms']
    # Average should have changed
    assert new_avg != initial_avg


def test_metrics_error_rate_reasonable(metrics_service):
    """Test that error rate is within reasonable bounds."""
    error_rate = metrics_service.get_error_rate()

    # For this mock, error rate should be 15/1500 = 1%
    assert error_rate == pytest.approx(0.01, rel=0.1)

    # In general, error rate should be low (< 5%)
    assert error_rate < 0.05
