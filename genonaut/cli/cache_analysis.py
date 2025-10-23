#!/usr/bin/env python3
"""CLI tool for analyzing route analytics and recommending cache targets.

System 1: Absolute Thresholds
Uses minimum request frequency and latency thresholds to filter routes.
Best for production environments with established traffic patterns.

Usage:
    python -m genonaut.cli.cache_analysis --count 10 --days 7
    make cache-analysis n=10 days=7 format=json
"""

import argparse
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from tabulate import tabulate
from sqlalchemy import text

from genonaut.api.dependencies import get_database_session
from genonaut.api.config import get_settings


def calculate_cache_priority_score(row: Dict[str, Any]) -> float:
    """Calculate cache priority score for a route.

    Higher score = higher priority for caching.

    Components:
    - Frequency: Higher traffic = higher priority
    - Latency: Slower queries = higher benefit from caching
    - User diversity: More users = better cache reuse

    Args:
        row: Route statistics from route_analytics_hourly

    Returns:
        Priority score (0-10000+)
    """
    # Extract metrics
    avg_requests = row['avg_hourly_requests']
    avg_p95_latency = row['avg_p95_latency']
    unique_users = row['avg_unique_users']

    # Component scores
    frequency_score = avg_requests * 10          # High traffic = higher priority
    latency_score = avg_p95_latency / 100        # Slow queries = higher benefit
    user_diversity_score = min(unique_users / 10, 10)  # More users = better cache reuse

    # Combined priority score
    return frequency_score + latency_score + user_diversity_score


def get_top_routes_for_caching(
    n: int = 10,
    lookback_days: int = 7,
    min_requests_per_hour: int = 10,
    min_latency_ms: int = 100
) -> List[Dict[str, Any]]:
    """Get top N routes that should be cached (System 1: Absolute Thresholds).

    Applies absolute minimum thresholds for frequency and latency,
    then ranks by cache priority score.

    Args:
        n: Number of top routes to return
        lookback_days: Days of historical data to analyze
        min_requests_per_hour: Minimum average requests/hour to consider
        min_latency_ms: Minimum p95 latency to benefit from caching

    Returns:
        List of route statistics with cache priority scores
    """
    settings = get_settings()

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
        HAVING AVG(total_requests) >= :min_requests_per_hour
            AND AVG(p95_duration_ms) >= :min_latency_ms
        ORDER BY AVG(total_requests) * AVG(p95_duration_ms) DESC
        LIMIT :limit
    """)

    session = next(get_database_session())
    try:
        result = session.execute(query, {
            'lookback_days': lookback_days,
            'min_requests_per_hour': min_requests_per_hour,
            'min_latency_ms': min_latency_ms,
            'limit': n * 2  # Get more, then filter by priority
        })

        routes = []
        for row in result:
            row_dict = dict(row._mapping)
            row_dict['cache_priority_score'] = calculate_cache_priority_score(row_dict)
            routes.append(row_dict)

        # Sort by priority score and return top N
        routes.sort(key=lambda x: x['cache_priority_score'], reverse=True)
        return routes[:n]
    finally:
        session.close()


def format_output_table(routes: List[Dict[str, Any]]) -> str:
    """Format routes as human-readable table."""
    table_data = []
    for i, route in enumerate(routes, 1):
        params_str = json.dumps(route.get('query_params_normalized') or {})
        if len(params_str) > 40:
            params_str = params_str[:37] + "..."

        table_data.append([
            i,
            route['method'],
            route['route'],
            params_str,
            f"{route['avg_hourly_requests']:.0f}",
            f"{route['avg_p95_latency']:.0f}ms",
            f"{route['avg_unique_users']:.0f}",
            f"{route['cache_priority_score']:.1f}",
            f"{route['success_rate']*100:.1f}%"
        ])

    headers = [
        "Rank", "Method", "Route", "Normalized Params",
        "Avg Req/Hr", "P95 Latency", "Unique Users", "Priority Score", "Success Rate"
    ]

    return tabulate(table_data, headers=headers, tablefmt="grid")


def format_output_json(routes: List[Dict[str, Any]]) -> str:
    """Format routes as JSON for programmatic consumption."""
    # Convert to JSON-serializable format
    output = []
    for route in routes:
        output.append({
            'route': route['route'],
            'method': route['method'],
            'query_params_normalized': route.get('query_params_normalized'),
            'avg_hourly_requests': float(route['avg_hourly_requests']),
            'avg_p95_latency_ms': float(route['avg_p95_latency']),
            'avg_unique_users': float(route['avg_unique_users']),
            'cache_priority_score': float(route['cache_priority_score']),
            'success_rate': float(route['success_rate']),
            'total_requests': int(route['total_requests'])
        })

    return json.dumps(output, indent=2)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze route analytics and identify top routes to cache (System 1: Absolute Thresholds)"
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
    parser.add_argument(
        '--min-requests',
        type=int,
        default=10,
        help="Minimum avg requests/hour to consider (default: 10)"
    )
    parser.add_argument(
        '--min-latency',
        type=int,
        default=100,
        help="Minimum p95 latency in ms to benefit from caching (default: 100)"
    )

    args = parser.parse_args()

    print(f"Analyzing route analytics (last {args.days} days)...")
    print(f"System 1: Absolute Thresholds")
    print(f"Filters: min {args.min_requests} req/hr, min {args.min_latency}ms latency\n")

    routes = get_top_routes_for_caching(
        n=args.count,
        lookback_days=args.days,
        min_requests_per_hour=args.min_requests,
        min_latency_ms=args.min_latency
    )

    if not routes:
        print("No routes found matching criteria.")
        return

    print(f"Top {len(routes)} routes recommended for caching:\n")

    if args.format == 'json':
        print(format_output_json(routes))
    else:
        print(format_output_table(routes))
        print(f"\nTotal routes analyzed: {len(routes)}")
        print(f"Use --format=json for machine-readable output")


if __name__ == '__main__':
    main()
