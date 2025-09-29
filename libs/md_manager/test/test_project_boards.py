"""Tests for project board integration functionality."""

import json
import pytest
from unittest.mock import Mock, patch

from md_manager.project_boards import (
    ProjectBoardManager, ProjectFilter, ProjectBoardInfo,
    extract_project_status, extract_project_priority
)


class TestProjectBoardManager:
    """Test cases for ProjectBoardManager class."""

    @pytest.fixture
    def manager(self):
        """ProjectBoardManager instance for testing."""
        return ProjectBoardManager()

    @pytest.fixture
    def sample_issues(self):
        """Sample issues with project data for testing."""
        return [
            {
                "number": 1,
                "title": "Issue 1",
                "project_key_vals": {"status": "In Progress", "priority": "High"}
            },
            {
                "number": 2,
                "title": "Issue 2",
                "project_key_vals": {"status": "Done", "priority": "Low"}
            },
            {
                "number": 3,
                "title": "Issue 3",
                "project_key_vals": {}  # No project data
            },
            {
                "number": 4,
                "title": "Issue 4",
                "project_key_vals": {"status": "Todo", "priority": "Medium"}
            }
        ]

    def test_filter_all_issues(self, manager, sample_issues):
        """Test filtering with ALL filter returns all issues."""
        result = manager.filter_issues_by_project(sample_issues, ProjectFilter.ALL)
        assert len(result) == 4
        assert result == sample_issues

    def test_filter_assigned_issues(self, manager, sample_issues):
        """Test filtering for issues assigned to projects."""
        result = manager.filter_issues_by_project(sample_issues, ProjectFilter.ASSIGNED)
        assert len(result) == 3  # Issues 1, 2, 4 have project data
        assert all(issue["project_key_vals"] for issue in result)

    def test_filter_unassigned_issues(self, manager, sample_issues):
        """Test filtering for issues not assigned to projects."""
        result = manager.filter_issues_by_project(sample_issues, ProjectFilter.UNASSIGNED)
        assert len(result) == 1  # Only issue 3 has no project data
        assert result[0]["number"] == 3

    def test_filter_by_status(self, manager, sample_issues):
        """Test filtering by project status."""
        result = manager.filter_issues_by_project(
            sample_issues, ProjectFilter.BY_STATUS, "In Progress"
        )
        assert len(result) == 1
        assert result[0]["number"] == 1

    def test_filter_by_priority(self, manager, sample_issues):
        """Test filtering by project priority."""
        result = manager.filter_issues_by_project(
            sample_issues, ProjectFilter.BY_PRIORITY, "High"
        )
        assert len(result) == 1
        assert result[0]["number"] == 1

    def test_filter_with_json_string_data(self, manager):
        """Test filtering with project data as JSON string."""
        issues = [
            {
                "number": 1,
                "title": "Issue 1",
                "project_key_vals": '{"status": "Done", "priority": "High"}'
            },
            {
                "number": 2,
                "title": "Issue 2",
                "project_key_vals": ""  # Empty string
            }
        ]

        result = manager.filter_issues_by_project(issues, ProjectFilter.BY_STATUS, "Done")
        assert len(result) == 1
        assert result[0]["number"] == 1

    def test_organize_by_project_field(self, manager, sample_issues):
        """Test organizing issues by project field."""
        result = manager.organize_issues_by_project_field(sample_issues, "status")

        assert "In Progress" in result
        assert len(result["In Progress"]) == 1
        assert result["In Progress"][0]["number"] == 1

        assert "Done" in result
        assert len(result["Done"]) == 1

        assert "Todo" in result
        assert len(result["Todo"]) == 1

        assert "unassigned" in result  # Issue 3
        assert len(result["unassigned"]) == 1

    def test_get_project_field_values(self, manager, sample_issues):
        """Test getting unique values for a project field."""
        status_values = manager.get_project_field_values(sample_issues, "status")
        assert status_values == {"In Progress", "Done", "Todo"}

        priority_values = manager.get_project_field_values(sample_issues, "priority")
        assert priority_values == {"High", "Low", "Medium"}

    def test_generate_project_summary(self, manager, sample_issues):
        """Test generating project summary statistics."""
        summary = manager.generate_project_summary(sample_issues)

        assert summary["total_issues"] == 4
        assert summary["assigned_to_projects"] == 3  # Issues 1, 2, 4
        assert summary["unassigned_issues"] == 1     # Issue 3
        assert summary["project_assignment_rate"] == 0.75  # 3/4

        # Check field usage counts
        assert "status" in summary["project_fields"]
        assert "priority" in summary["project_fields"]
        assert summary["project_fields"]["status"]["In Progress"] == 1
        assert summary["project_fields"]["priority"]["High"] == 1


class TestProjectBoardInfo:
    """Test cases for ProjectBoardInfo dataclass."""

    def test_project_board_info_creation(self):
        """Test ProjectBoardInfo creation with all fields."""
        info = ProjectBoardInfo(
            id=123,
            name="Test Project",
            url="https://github.com/org/repo/projects/1",
            description="Test project description",
            fields={"status": ["Todo", "In Progress", "Done"]}
        )

        assert info.id == 123
        assert info.name == "Test Project"
        assert info.url == "https://github.com/org/repo/projects/1"
        assert info.description == "Test project description"
        assert "status" in info.fields

    def test_project_board_info_minimal(self):
        """Test ProjectBoardInfo creation with minimal fields."""
        info = ProjectBoardInfo(
            id=456,
            name="Minimal Project",
            url="https://github.com/user/repo/projects/2"
        )

        assert info.id == 456
        assert info.name == "Minimal Project"
        assert info.description is None
        assert info.fields is None


class TestProjectExtractors:
    """Test cases for project data extraction functions."""

    def test_extract_project_status(self):
        """Test extracting status from project data."""
        # Test different field name variations
        assert extract_project_status({"status": "In Progress"}) == "In Progress"
        assert extract_project_status({"Status": "Done"}) == "Done"
        assert extract_project_status({"state": "Open"}) == "Open"
        assert extract_project_status({"column": "Todo"}) == "Todo"

        # Test missing status
        assert extract_project_status({"priority": "High"}) is None
        assert extract_project_status({}) is None

    def test_extract_project_priority(self):
        """Test extracting priority from project data."""
        # Test different field name variations
        assert extract_project_priority({"priority": "High"}) == "High"
        assert extract_project_priority({"Priority": "Low"}) == "Low"
        assert extract_project_priority({"pri": "Medium"}) == "Medium"
        assert extract_project_priority({"importance": "Critical"}) == "Critical"

        # Test missing priority
        assert extract_project_priority({"status": "Done"}) is None
        assert extract_project_priority({}) is None

    def test_extract_with_type_conversion(self):
        """Test extraction with non-string values."""
        # Numbers should be converted to strings
        assert extract_project_status({"status": 1}) == "1"
        assert extract_project_priority({"priority": 5}) == "5"

        # Booleans should be converted to strings
        assert extract_project_status({"status": True}) == "True"


class TestProjectFilter:
    """Test cases for ProjectFilter enum."""

    def test_project_filter_values(self):
        """Test ProjectFilter enum values."""
        assert ProjectFilter.ALL.value == "all"
        assert ProjectFilter.ASSIGNED.value == "assigned"
        assert ProjectFilter.UNASSIGNED.value == "unassigned"
        assert ProjectFilter.BY_STATUS.value == "by_status"
        assert ProjectFilter.BY_PRIORITY.value == "by_priority"