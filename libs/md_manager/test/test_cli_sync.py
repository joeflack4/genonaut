"""Tests for GitHub sync CLI commands."""

import os
import tempfile
import pytest
import responses
from pathlib import Path
from unittest.mock import patch
from click.testing import CliRunner

from md_manager.cli import cli
from md_manager.collate import collate_files


class TestSyncCLI:
    """Test cases for GitHub sync CLI commands."""

    @pytest.fixture
    def temp_dir_with_issues(self):
        """Create temporary directory with issue files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create issue files
            issues_dir = temp_path / "issues"
            issues_dir.mkdir()

            (issues_dir / "001-login-bug.md").write_text("# Login Bug\nUsers cannot log in")
            (issues_dir / "feature-123.md").write_text("# New Feature\nAdd dark mode")

            yield temp_path

    @pytest.fixture
    def test_database(self, temp_dir_with_issues):
        """Database with files already collated."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        try:
            # Collate files first
            collate_files([str(temp_dir_with_issues)], db_path, recursive=True)
            yield db_path
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_sync_command_missing_config(self, test_database):
        """Test sync command with missing GitHub configuration."""
        runner = CliRunner()

        # Clear environment variables that might be set
        with patch.dict(os.environ, {}, clear=True):
            result = runner.invoke(cli, ['sync', '--db-path', test_database])

        assert result.exit_code != 0
        assert "Sync error" in result.output
        assert "GitHub sync is not enabled" in result.output

    @responses.activate
    def test_sync_command_with_env_vars(self, test_database):
        """Test sync command with environment variables."""
        # Mock GitHub API response
        responses.add(
            responses.GET,
            "https://api.github.com/repos/test_owner/test_repo/issues",
            json=[
                {
                    "number": 1,
                    "title": "Test Issue",
                    "body": "Test description",
                    "html_url": "https://github.com/test_owner/test_repo/issues/1",
                    "state": "open",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-02T00:00:00Z",
                    "closed_at": None,
                    "labels": [],
                    "assignees": [],
                    "milestone": None
                }
            ],
            status=200
        )

        runner = CliRunner()

        # Set environment variables
        env_vars = {
            'MD_MANAGER_TOKEN': 'test_token',
            'MD_MANAGER_REPO_OWNER': 'test_owner',
            'MD_MANAGER_REPO_NAME': 'test_repo',
            'MD_MANAGER_SYNC_ENABLED': 'true'
        }

        with patch.dict(os.environ, env_vars):
            result = runner.invoke(cli, ['sync', '--db-path', test_database])

        assert result.exit_code == 0
        assert "Sync completed successfully" in result.output
        assert "Issues fetched: 1" in result.output

    @responses.activate
    def test_sync_command_dry_run(self, test_database):
        """Test sync command with dry run mode."""
        # Mock GitHub API response
        responses.add(
            responses.GET,
            "https://api.github.com/repos/test_owner/test_repo/issues",
            json=[
                {
                    "number": 123,
                    "title": "Feature Request",
                    "body": "Add new feature",
                    "html_url": "https://github.com/test_owner/test_repo/issues/123",
                    "state": "open",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-02T00:00:00Z",
                    "closed_at": None,
                    "labels": [],
                    "assignees": [],
                    "milestone": None
                }
            ],
            status=200
        )

        runner = CliRunner()

        env_vars = {
            'MD_MANAGER_TOKEN': 'test_token',
            'MD_MANAGER_REPO_OWNER': 'test_owner',
            'MD_MANAGER_REPO_NAME': 'test_repo',
            'MD_MANAGER_SYNC_ENABLED': 'true'
        }

        with patch.dict(os.environ, env_vars):
            result = runner.invoke(cli, ['sync', '--db-path', test_database, '--dry-run'])

        assert result.exit_code == 0
        assert "DRY RUN: No changes will be made" in result.output
        assert "Would process 1 issues" in result.output
        assert "#123: Feature Request" in result.output
        assert "Dry run complete" in result.output

    @responses.activate
    def test_sync_command_force_full_sync(self, test_database):
        """Test sync command with force full sync."""
        # Mock GitHub API response
        responses.add(
            responses.GET,
            "https://api.github.com/repos/test_owner/test_repo/issues",
            json=[],
            status=200
        )

        runner = CliRunner()

        env_vars = {
            'MD_MANAGER_TOKEN': 'test_token',
            'MD_MANAGER_REPO_OWNER': 'test_owner',
            'MD_MANAGER_REPO_NAME': 'test_repo',
            'MD_MANAGER_SYNC_ENABLED': 'true'
        }

        with patch.dict(os.environ, env_vars):
            result = runner.invoke(cli, ['sync', '--db-path', test_database, '--force'])

        assert result.exit_code == 0
        assert "Sync mode: Full" in result.output
        assert "Sync completed successfully" in result.output

    def test_sync_command_cli_options_override(self, test_database):
        """Test that CLI options override environment variables."""
        runner = CliRunner()

        # Set different values in environment
        env_vars = {
            'MD_MANAGER_TOKEN': 'env_token',
            'MD_MANAGER_REPO_OWNER': 'env_owner',
            'MD_MANAGER_REPO_NAME': 'env_repo',
            'MD_MANAGER_SYNC_ENABLED': 'true'
        }

        # CLI should override with different values
        with patch.dict(os.environ, env_vars):
            result = runner.invoke(cli, [
                'sync',
                '--db-path', test_database,
                '--token', 'cli_token',
                '--repo-owner', 'cli_owner',
                '--repo-name', 'cli_repo',
                '--dry-run'
            ])

        # Should show CLI values in output
        assert "GitHub Repository: cli_owner/cli_repo" in result.output

    def test_sync_command_no_database(self):
        """Test sync command when no database is found."""
        runner = CliRunner()

        env_vars = {
            'MD_MANAGER_TOKEN': 'test_token',
            'MD_MANAGER_REPO_OWNER': 'test_owner',
            'MD_MANAGER_REPO_NAME': 'test_repo',
            'MD_MANAGER_SYNC_ENABLED': 'true'
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('os.getcwd', return_value=temp_dir):
                with patch.dict(os.environ, env_vars):
                    result = runner.invoke(cli, ['sync'])

        assert result.exit_code != 0
        assert "No database found" in result.output

    @responses.activate
    def test_sync_command_api_error(self, test_database):
        """Test sync command with GitHub API error."""
        # Mock GitHub API error response
        responses.add(
            responses.GET,
            "https://api.github.com/repos/test_owner/test_repo/issues",
            json={"message": "Not Found"},
            status=404
        )

        runner = CliRunner()

        env_vars = {
            'MD_MANAGER_TOKEN': 'test_token',
            'MD_MANAGER_REPO_OWNER': 'test_owner',
            'MD_MANAGER_REPO_NAME': 'test_repo',
            'MD_MANAGER_SYNC_ENABLED': 'true'
        }

        with patch.dict(os.environ, env_vars):
            result = runner.invoke(cli, ['sync', '--db-path', test_database])

        assert result.exit_code != 0
        assert "Sync error" in result.output


class TestCreateSampleConfigCLI:
    """Test cases for create-sample-config CLI command."""

    def test_create_sample_config_default(self):
        """Test creating sample config with default settings."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'test-config.yml')

            result = runner.invoke(cli, ['create-sample-config', config_path])

            assert result.exit_code == 0
            assert f"Created sample configuration file: {config_path}" in result.output
            assert "To get started with GitHub sync" in result.output

            # Verify file was created
            assert os.path.exists(config_path)

            # Verify content is valid YAML
            import yaml
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)

            assert 'github' in config_data
            assert 'token' in config_data['github']

    def test_create_sample_config_json_format(self):
        """Test creating sample config in JSON format."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'test-config.json')

            result = runner.invoke(cli, ['create-sample-config', config_path, '--format', 'json'])

            assert result.exit_code == 0
            assert "Created sample configuration file" in result.output

            # Verify file was created
            assert os.path.exists(config_path)

            # Verify content is valid JSON
            import json
            with open(config_path, 'r') as f:
                config_data = json.load(f)

            assert 'github' in config_data

    def test_create_sample_config_auto_format_detection(self):
        """Test that format is auto-detected from file extension."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as temp_dir:
            # Test YAML auto-detection
            yaml_path = os.path.join(temp_dir, 'config.yml')
            result = runner.invoke(cli, ['create-sample-config', yaml_path])
            assert result.exit_code == 0
            assert os.path.exists(yaml_path)

            # Test JSON auto-detection
            json_path = os.path.join(temp_dir, 'config.json')
            result = runner.invoke(cli, ['create-sample-config', json_path])
            assert result.exit_code == 0
            assert os.path.exists(json_path)

    def test_create_sample_config_default_name(self):
        """Test creating config with default filename."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory and run command
            with runner.isolated_filesystem(temp_dir=temp_dir):
                result = runner.invoke(cli, ['create-sample-config'])

                assert result.exit_code == 0

                # Should create md-manager.yml by default
                assert os.path.exists('md-manager.yml')

    def test_create_sample_config_existing_file(self):
        """Test behavior when config file already exists."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'existing.yml')

            # Create existing file
            with open(config_path, 'w') as f:
                f.write("existing content")

            # Should overwrite existing file
            result = runner.invoke(cli, ['create-sample-config', config_path])

            assert result.exit_code == 0
            assert "Created sample configuration file" in result.output

            # Verify content was replaced
            import yaml
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)

            assert 'github' in config_data