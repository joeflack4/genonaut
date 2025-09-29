"""Project board integration utilities for GitHub Projects.

This module provides utilities for working with GitHub Projects data,
including filtering and organizing issues by project board information.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from enum import Enum


class ProjectFilter(Enum):
    """Enumeration of available project filtering options."""
    ALL = "all"
    ASSIGNED = "assigned"
    UNASSIGNED = "unassigned"
    BY_STATUS = "by_status"
    BY_PRIORITY = "by_priority"


@dataclass
class ProjectBoardInfo:
    """Information about a project board."""
    id: int
    name: str
    url: str
    description: Optional[str] = None
    fields: Optional[Dict[str, Any]] = None


class ProjectBoardManager:
    """Manager for project board operations and filtering."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize project board manager.

        Args:
            logger: Logger instance for debugging
        """
        self.logger = logger or logging.getLogger(__name__)

    def filter_issues_by_project(
        self,
        issues: List[Dict[str, Any]],
        filter_type: ProjectFilter,
        filter_value: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter issues based on project board criteria.

        Args:
            issues: List of issue dictionaries with project_key_vals
            filter_type: Type of filtering to apply
            filter_value: Value to filter by (for specific filters)

        Returns:
            Filtered list of issues
        """
        if filter_type == ProjectFilter.ALL:
            return issues

        filtered_issues = []

        for issue in issues:
            project_data = issue.get("project_key_vals", {})

            # Handle string JSON data
            if isinstance(project_data, str):
                try:
                    project_data = json.loads(project_data)
                except json.JSONDecodeError:
                    project_data = {}

            if filter_type == ProjectFilter.ASSIGNED:
                if project_data:  # Has any project data
                    filtered_issues.append(issue)
            elif filter_type == ProjectFilter.UNASSIGNED:
                if not project_data:  # No project data
                    filtered_issues.append(issue)
            elif filter_type == ProjectFilter.BY_STATUS:
                status = project_data.get("status", "").lower()
                if filter_value and status == filter_value.lower():
                    filtered_issues.append(issue)
            elif filter_type == ProjectFilter.BY_PRIORITY:
                priority = project_data.get("priority", "").lower()
                if filter_value and priority == filter_value.lower():
                    filtered_issues.append(issue)

        self.logger.debug(f"Filtered {len(issues)} issues to {len(filtered_issues)} using {filter_type.value}")
        return filtered_issues

    def organize_issues_by_project_field(
        self,
        issues: List[Dict[str, Any]],
        field_name: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Organize issues by a specific project field value.

        Args:
            issues: List of issue dictionaries
            field_name: Name of the project field to organize by

        Returns:
            Dictionary mapping field values to lists of issues
        """
        organized = {}

        for issue in issues:
            project_data = issue.get("project_key_vals", {})

            # Handle string JSON data
            if isinstance(project_data, str):
                try:
                    project_data = json.loads(project_data)
                except json.JSONDecodeError:
                    project_data = {}

            field_value = project_data.get(field_name, "unassigned")
            if field_value not in organized:
                organized[field_value] = []
            organized[field_value].append(issue)

        self.logger.debug(f"Organized {len(issues)} issues by {field_name} into {len(organized)} groups")
        return organized

    def get_project_field_values(
        self,
        issues: List[Dict[str, Any]],
        field_name: str
    ) -> Set[str]:
        """
        Get all unique values for a project field across issues.

        Args:
            issues: List of issue dictionaries
            field_name: Name of the project field

        Returns:
            Set of unique field values
        """
        values = set()

        for issue in issues:
            project_data = issue.get("project_key_vals", {})

            # Handle string JSON data
            if isinstance(project_data, str):
                try:
                    project_data = json.loads(project_data)
                except json.JSONDecodeError:
                    project_data = {}

            field_value = project_data.get(field_name)
            if field_value:
                values.add(str(field_value))

        return values

    def generate_project_summary(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a summary of project board usage across issues.

        Args:
            issues: List of issue dictionaries

        Returns:
            Summary dictionary with project statistics
        """
        total_issues = len(issues)
        assigned_to_projects = 0
        project_fields = {}

        for issue in issues:
            project_data = issue.get("project_key_vals", {})

            # Handle string JSON data
            if isinstance(project_data, str):
                try:
                    project_data = json.loads(project_data)
                except json.JSONDecodeError:
                    project_data = {}

            if project_data:
                assigned_to_projects += 1

                # Count field usage
                for field_name, field_value in project_data.items():
                    if field_name not in project_fields:
                        project_fields[field_name] = {}

                    value_str = str(field_value)
                    if value_str not in project_fields[field_name]:
                        project_fields[field_name][value_str] = 0
                    project_fields[field_name][value_str] += 1

        return {
            "total_issues": total_issues,
            "assigned_to_projects": assigned_to_projects,
            "unassigned_issues": total_issues - assigned_to_projects,
            "project_assignment_rate": assigned_to_projects / total_issues if total_issues > 0 else 0,
            "project_fields": project_fields
        }


def extract_project_status(project_data: Dict[str, Any]) -> Optional[str]:
    """
    Extract status from project data with common field name variations.

    Args:
        project_data: Project key-value data

    Returns:
        Status string or None if not found
    """
    status_fields = ["status", "Status", "state", "State", "column", "Column"]

    for field in status_fields:
        if field in project_data:
            return str(project_data[field])

    return None


def extract_project_priority(project_data: Dict[str, Any]) -> Optional[str]:
    """
    Extract priority from project data with common field name variations.

    Args:
        project_data: Project key-value data

    Returns:
        Priority string or None if not found
    """
    priority_fields = ["priority", "Priority", "pri", "Pri", "importance", "Importance"]

    for field in priority_fields:
        if field in project_data:
            return str(project_data[field])

    return None