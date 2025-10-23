#!/usr/bin/env python3
"""CLI tool for relative cache priority analysis (development-friendly).

System 2: Relative Ranking
Uses percentile-based ranking - compares each route to the distribution of all routes.
No absolute thresholds - works even with 1-2 requests per day.
Perfect for development environments with low/sporadic traffic.

Usage:
    python -m genonaut.cli.cache_analysis_relative --count 10 --days 7
    make cache-analysis-relative n=10 days=7 format=json
"""

import argparse
import json
from typing import List, Dict, Any
import numpy as np
from tabulate import tabulate
from sqlalchemy import text

from genonaut.api.dependencies import get_database_session
from genonaut.api.config import get_settings


def calculate_relative_priority_score(
    row: Dict[str, Any],
    stats: Dict[str, Any]
) -> Dict[str, Any]:
    """Calculate relative cache priority based on percentiles.

    Ranks each route by comparing to the distribution of all routes.
    No absolute thresholds - uses relative importance.

    Weights:
    - Latency: 40% (slower routes get higher priority)
    - Popularity: 40% (more frequent routes get higher priority)
    - User diversity: 20% (more users = better cache reuse)

    Args:
        row: Route statistics from route_analytics_hourly
        stats: Distribution statistics for all routes

    Returns:
        Dict with priority score and component scores
    """
    # Extract route metrics
    avg_requests = row['avg_hourly_requests']
    avg_p95_latency = row['avg_p95_latency']
    unique_users = row['avg_unique_users']

    # Calculate percentiles (0-100)
    # Higher percentile = more important
    popularity_percentile = _calculate_percentile(
        avg_requests,
        stats['request_distribution']
    )

    latency_percentile = _calculate_percentile(
        avg_p95_latency,
        stats['latency_distribution']
    )

    user_percentile = _calculate_percentile(
        unique_users,
        stats['user_distribution']
    )

    # Combined score: weighted average of percentiles
    # Latency gets 40%, popularity 40%, user diversity 20%
    priority_score = (
        (latency_percentile * 0.4) +
        (popularity_percentile * 0.4) +
        (user_percentile * 0.2)
    )

    return {
        'priority_score': priority_score,
        'popularity_percentile': popularity_percentile,
        'latency_percentile': latency_percentile,
        'user_percentile': user_percentile
    }


def _calculate_percentile(value: float, distribution: List[float]) -> float:
    """Calculate what percentile this value is in the distribution.

    Args:
        value: The value to find percentile for
        distribution: List of all values in the distribution

    Returns:
        Percentile (0-100) indicating where value falls in distribution
    """
    if not distribution:
        return 50.0  # Default to median if no distribution

    # Use numpy for percentile calculation
    percentile = (np.searchsorted(sorted(distribution), value, side='right') /
                  len(distribution)) * 100

    return min(100.0, max(0.0, percentile))


def get_top_routes_relative(
    n: int = 10,
    lookback_days: int = 7
) -> List[Dict[str, Any]]:
    """Get top N routes using relative ranking (System 2: Percentile-based).

    No absolute thresholds - ranks ALL routes by relative importance.
    Perfect for development environments with sporadic traffic.

    Args:
        n: Number of top routes to return
        lookback_days: Days of historical data to analyze

    Returns:
        List of route statistics with relative priority scores
    """
    query = text("""
        SELECT
            route,
            method,
            query_params_normalized,
            AVG(total_requests) as avg_hourly_requests,
            AVG(p95_duration_ms) as avg_p95_latency,
            AVG(p99_duration_ms) as avg_p99_latency,
            AVG(unique_users) as avg_unique_users,
            SUM(total_requests) as total_requests,
            AVG(successful_requests::FLOAT / NULLIF(total_requests, 0)) as success_rate
        FROM route_analytics_hourly
        WHERE timestamp > NOW() - INTERVAL '1 day' * :lookback_days
        GROUP BY route, method, query_params_normalized
        HAVING AVG(total_requests) > 0  -- At least some traffic
    """)

    session = next(get_database_session())
    try:
        result = session.execute(query, {'lookback_days': lookback_days})

        routes = []
        request_dist = []
        latency_dist = []
        user_dist = []

        # First pass: collect all routes and build distributions
        for row in result:
            row_dict = dict(row._mapping)
            routes.append(row_dict)
            request_dist.append(row_dict['avg_hourly_requests'])
            latency_dist.append(row_dict['avg_p95_latency'])
            user_dist.append(row_dict['avg_unique_users'])

        # Build distribution stats
        stats = {
            'request_distribution': request_dist,
            'latency_distribution': latency_dist,
            'user_distribution': user_dist
        }

        # Second pass: calculate relative scores
        for route in routes:
            scores = calculate_relative_priority_score(route, stats)
            route.update(scores)

        # Sort by priority score and return top N
        routes.sort(key=lambda x: x['priority_score'], reverse=True)
        return routes[:n]
    finally:
        session.close()


def format_output_table_relative(routes: List[Dict[str, Any]]) -> str:
    """Format routes as human-readable table with percentiles."""
    table_data = []
    for i, route in enumerate(routes, 1):
        params_str = json.dumps(route.get('query_params_normalized') or {})
        if len(params_str) > 35:
            params_str = params_str[:32] + "..."

        table_data.append([
            i,
            route['method'],
            route['route'][:40],  # Truncate long routes
            params_str,
            f"{route['avg_hourly_requests']:.1f}",
            f"{route['avg_p95_latency']:.0f}ms",
            f"{route['priority_score']:.1f}",
            f"P{route['popularity_percentile']:.0f}",
            f"L{route['latency_percentile']:.0f}",
            f"U{route['user_percentile']:.0f}"
        ])

    headers = [
        "Rank", "Method", "Route", "Params",
        "Req/Hr", "P95", "Score", "Pop%", "Lat%", "User%"
    ]

    return tabulate(table_data, headers=headers, tablefmt="grid")


def format_output_json_relative(routes: List[Dict[str, Any]]) -> str:
    """Format routes as JSON with relative scores."""
    output = []
    for route in routes:
        output.append({
            'route': route['route'],
            'method': route['method'],
            'query_params_normalized': route.get('query_params_normalized'),
            'avg_hourly_requests': float(route['avg_hourly_requests']),
            'avg_p95_latency_ms': float(route['avg_p95_latency']),
            'priority_score': float(route['priority_score']),
            'popularity_percentile': float(route['popularity_percentile']),
            'latency_percentile': float(route['latency_percentile']),
            'user_percentile': float(route['user_percentile']),
            'success_rate': float(route['success_rate']),
            'total_requests': int(route['total_requests'])
        })

    return json.dumps(output, indent=2)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze routes using RELATIVE ranking (System 2: Development-friendly)"
    )
    parser.add_argument(
        '-n', '--count',
        type=int,
        default=10,
        help="Number of top routes to return (default: 10)"
    )
    parser.add_argument(
        '-d', '--days',
        type=int,
        default=7,
        help="Days of historical data to analyze (default: 7)"
    )
    parser.add_argument(
        '-f', '--format',
        choices=['table', 'json'],
        default='table',
        help="Output format (default: table)"
    )

    args = parser.parse_args()

    print(f"Analyzing routes with RELATIVE ranking (last {args.days} days)...")
    print("System 2: Percentile-based - comparing all routes to each other")
    print("No absolute thresholds\n")

    routes = get_top_routes_relative(
        n=args.count,
        lookback_days=args.days
    )

    if not routes:
        print("No routes found with traffic.")
        return

    print(f"Top {len(routes)} routes by relative importance:\n")

    if args.format == 'json':
        print(format_output_json_relative(routes))
    else:
        print(format_output_table_relative(routes))
        print(f"\nColumns: Pop% (popularity), Lat% (latency), User% (user diversity)")
        print(f"Higher percentile = more important relative to other routes")
        print(f"Use --format=json for machine-readable output")


if __name__ == '__main__':
    main()
