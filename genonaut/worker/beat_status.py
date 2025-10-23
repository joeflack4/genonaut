#!/usr/bin/env python3
"""Display Celery Beat schedule status from RedBeat.

This script queries RedBeat in Redis to show the current status of all
scheduled periodic tasks, including their schedules, last run time, and
time until next execution.
"""

import sys
import os
from datetime import datetime, timezone

# Add project root to path so we can import genonaut modules
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from redbeat import RedBeatSchedulerEntry
    from genonaut.worker.queue_app import celery_app
    REDBEAT_AVAILABLE = True
except ImportError as e:
    REDBEAT_AVAILABLE = False
    _import_error = str(e)
except Exception as e:
    REDBEAT_AVAILABLE = False
    _import_error = f"Unexpected error: {str(e)}"


def format_timedelta(td):
    """Format a timedelta as a human-readable string."""
    if td is None:
        return "N/A"

    total_seconds = int(td.total_seconds())
    if total_seconds < 0:
        return "Overdue!"

    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}s")

    return " ".join(parts)


def format_schedule(schedule):
    """Format a crontab schedule as a human-readable string."""
    schedule_str = str(schedule)

    # Parse the crontab format: <crontab: minute hour day_of_month month_of_year day_of_week (m/h/dM/MY/d)>
    if "crontab:" in schedule_str and "(" in schedule_str:
        try:
            # Extract the cron pattern (the part before the parentheses)
            # Format is: <crontab: 0 0 * * * (m/h/dM/MY/d)>
            cron_part = schedule_str.split("crontab:")[1].split("(")[0].strip()
            parts = cron_part.split()

            if len(parts) >= 5:
                minute, hour, dom, moy, dow = parts[:5]
            else:
                # If we can't parse it, return the raw string
                return schedule_str

            # Build readable description
            if minute == "0" and hour == "0" and dom == "*" and moy == "*" and dow == "*":
                return "Daily at midnight UTC"
            elif minute == "0" and hour != "*" and dom == "*" and moy == "*" and dow == "*":
                return f"Daily at {hour.zfill(2)}:00 UTC"
            elif hour == "*" and dom == "*" and moy == "*" and dow == "*":
                if minute == "0":
                    return "Every hour (on the hour)"
                else:
                    return f"Every hour at :{str(minute).zfill(2)} past"
            elif minute != "*" and hour != "*" and dom == "*" and moy == "*" and dow == "*":
                return f"Daily at {str(hour).zfill(2)}:{str(minute).zfill(2)} UTC"
            else:
                return f"Cron: {cron_part}"
        except (IndexError, ValueError):
            # If parsing fails, just return the original string
            return schedule_str

    return schedule_str


def show_beat_status():
    """Display the status of all Celery Beat scheduled tasks."""
    if not REDBEAT_AVAILABLE:
        error_msg = "Error: RedBeat or Celery not available. Is celery-redbeat installed?"
        if '_import_error' in globals():
            error_msg += f"\nImport error: {_import_error}"
        print(error_msg)
        sys.exit(1)

    print("=" * 80)
    print("Celery Beat Schedule Status (RedBeat)")
    print("=" * 80)
    print()

    # Get the configured schedule
    beat_schedule = celery_app.conf.beat_schedule

    if not beat_schedule:
        print("No scheduled tasks configured.")
        return

    now = datetime.now(timezone.utc)

    for task_name, task_config in beat_schedule.items():
        print(f"Task: {task_name}")
        print("-" * 80)

        # Basic configuration from config/base.json
        task_path = task_config.get('task', 'N/A')
        schedule = task_config.get('schedule', 'N/A')

        print(f"  Task Path:      {task_path}")
        print(f"  Schedule:       {format_schedule(schedule)}")
        print(f"  Raw Cron:       {schedule}")

        # Try to get RedBeat state from Redis
        try:
            # RedBeat stores schedule entries in Redis with a specific key format
            entry = RedBeatSchedulerEntry.from_key(
                f"redbeat:{task_name}",
                app=celery_app
            )

            if entry:
                # Get last run time
                if hasattr(entry, 'last_run_at') and entry.last_run_at:
                    last_run = entry.last_run_at
                    last_run_str = last_run.strftime("%Y-%m-%d %H:%M:%S UTC")
                    time_since = now - last_run
                    print(f"  Last Run:       {last_run_str} ({format_timedelta(time_since)} ago)")
                else:
                    print(f"  Last Run:       Never")

                # Calculate next run time
                if hasattr(entry, 'schedule') and entry.schedule:
                    # Get the next run time
                    if hasattr(entry.schedule, 'remaining_estimate'):
                        remaining = entry.schedule.remaining_estimate(last_run if hasattr(entry, 'last_run_at') and entry.last_run_at else now)
                        next_run = now + remaining
                        print(f"  Next Run:       {next_run.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                        print(f"  Time Until:     {format_timedelta(remaining)}")
                    else:
                        print(f"  Next Run:       Unable to calculate")

                # Enabled status
                if hasattr(entry, 'enabled'):
                    status = "Enabled" if entry.enabled else "Disabled"
                    print(f"  Status:         {status}")

        except Exception as e:
            # Entry doesn't exist in Redis yet (worker hasn't started with -B flag)
            print(f"  Redis State:    Not found (worker may not have started with -B flag)")
            print(f"  Note:           Schedule will be created when worker starts")

        print()

    print("=" * 80)
    print(f"Checked at: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 80)


if __name__ == "__main__":
    show_beat_status()
