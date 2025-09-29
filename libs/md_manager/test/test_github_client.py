"""Tests for GitHub API client functionality."""

import os
import json
import time
import pytest
import responses
from unittest.mock import patch, MagicMock

from md_manager.github_client import GitHubClient, GitHubError, RateLimitError


class TestGitHubClient:
    """Test cases for GitHubClient."""

    def test_client_initialization(self):
        """Test GitHubClient initialization with token."""
        client = GitHubClient(token="test_token", repo_owner="test", repo_name="repo")

        assert client.token == "test_token"
        assert client.repo_owner == "test"
        assert client.repo_name == "repo"
        assert client.base_url == "https://api.github.com"

    def test_client_initialization_with_custom_base_url(self):
        """Test GitHubClient initialization with custom base URL for GitHub Enterprise."""
        client = GitHubClient(
            token="test_token",
            repo_owner="test",
            repo_name="repo",
            base_url="https://github.enterprise.com/api/v3"
        )

        assert client.base_url == "https://github.enterprise.com/api/v3"

    def test_client_initialization_without_token(self):
        """Test that GitHubClient raises error without token."""
        with pytest.raises(ValueError, match="Either auth_provider or token is required"):
            GitHubClient(repo_owner="test", repo_name="repo")

    @responses.activate
    def test_successful_api_request(self):
        """Test successful API request."""
        responses.add(
            responses.GET,
            "https://api.github.com/repos/test/repo/issues",
            json={"test": "data"},
            status=200,
            headers={"X-RateLimit-Remaining": "5000", "X-RateLimit-Reset": str(int(time.time()) + 3600)}
        )

        client = GitHubClient(token="test_token", repo_owner="test", repo_name="repo")
        result = client._make_request("GET", "/repos/test/repo/issues")

        assert result == {"test": "data"}

    @responses.activate
    def test_rate_limit_tracking(self):
        """Test that rate limit information is tracked."""
        responses.add(
            responses.GET,
            "https://api.github.com/repos/test/repo/issues",
            json={"test": "data"},
            status=200,
            headers={"X-RateLimit-Remaining": "4999", "X-RateLimit-Reset": str(int(time.time()) + 3600)}
        )

        client = GitHubClient(token="test_token", repo_owner="test", repo_name="repo")
        client._make_request("GET", "/repos/test/repo/issues")

        assert client.rate_limit_remaining == 4999
        assert client.rate_limit_reset > time.time()

    @responses.activate
    def test_rate_limit_exceeded_handling(self):
        """Test handling of rate limit exceeded."""
        reset_time = int(time.time()) + 60  # Reset in 1 minute
        responses.add(
            responses.GET,
            "https://api.github.com/repos/test/repo/issues",
            json={"message": "API rate limit exceeded"},
            status=403,
            headers={
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_time)
            }
        )

        client = GitHubClient(token="test_token", repo_owner="test", repo_name="repo")

        with pytest.raises(RateLimitError) as exc_info:
            client._make_request("GET", "/repos/test/repo/issues")

        assert "Rate limit exceeded" in str(exc_info.value)
        assert exc_info.value.reset_time == reset_time

    @responses.activate
    def test_404_error_handling(self):
        """Test handling of 404 errors."""
        responses.add(
            responses.GET,
            "https://api.github.com/repos/test/repo/issues",
            json={"message": "Not Found"},
            status=404
        )

        client = GitHubClient(token="test_token", repo_owner="test", repo_name="repo")

        with pytest.raises(GitHubError) as exc_info:
            client._make_request("GET", "/repos/test/repo/issues")

        assert exc_info.value.status_code == 404
        assert "Not Found" in str(exc_info.value)

    @responses.activate
    def test_authentication_headers(self):
        """Test that proper authentication headers are sent."""
        responses.add(
            responses.GET,
            "https://api.github.com/repos/test/repo/issues",
            json={"test": "data"},
            status=200
        )

        client = GitHubClient(token="test_token", repo_owner="test", repo_name="repo")
        client._make_request("GET", "/repos/test/repo/issues")

        # Check that the request was made with proper authorization header
        assert len(responses.calls) == 1
        assert responses.calls[0].request.headers["Authorization"] == "Bearer test_token"
        assert responses.calls[0].request.headers["Accept"] == "application/vnd.github.v3+json"

    @responses.activate
    def test_pagination_handling(self):
        """Test handling of paginated responses."""
        # First page
        responses.add(
            responses.GET,
            "https://api.github.com/repos/test/repo/issues",
            json=[{"number": 1}, {"number": 2}],
            status=200,
            headers={
                "Link": '<https://api.github.com/repos/test/repo/issues?page=2>; rel="next"',
                "X-RateLimit-Remaining": "5000"
            }
        )

        # Second page
        responses.add(
            responses.GET,
            "https://api.github.com/repos/test/repo/issues?page=2",
            json=[{"number": 3}, {"number": 4}],
            status=200,
            headers={"X-RateLimit-Remaining": "4999"}
        )

        client = GitHubClient(token="test_token", repo_owner="test", repo_name="repo")
        results = list(client._paginate_request("GET", "/repos/test/repo/issues"))

        assert len(results) == 4
        assert results[0]["number"] == 1
        assert results[3]["number"] == 4

    @responses.activate
    def test_retry_on_server_error(self):
        """Test retry mechanism on server errors."""
        # First request fails with 500
        responses.add(
            responses.GET,
            "https://api.github.com/repos/test/repo/issues",
            json={"message": "Server Error"},
            status=500
        )

        # Second request succeeds
        responses.add(
            responses.GET,
            "https://api.github.com/repos/test/repo/issues",
            json={"test": "data"},
            status=200,
            headers={"X-RateLimit-Remaining": "5000"}
        )

        client = GitHubClient(token="test_token", repo_owner="test", repo_name="repo")

        with patch('time.sleep'):  # Mock sleep to speed up test
            result = client._make_request("GET", "/repos/test/repo/issues")

        assert result == {"test": "data"}
        assert len(responses.calls) == 2

    @responses.activate
    def test_exponential_backoff(self):
        """Test exponential backoff for retries."""
        # All requests fail with 500
        for _ in range(4):  # max_retries + 1
            responses.add(
                responses.GET,
                "https://api.github.com/repos/test/repo/issues",
                json={"message": "Server Error"},
                status=500
            )

        client = GitHubClient(token="test_token", repo_owner="test", repo_name="repo")

        with patch('time.sleep') as mock_sleep:
            with pytest.raises(GitHubError):
                client._make_request("GET", "/repos/test/repo/issues")

            # Should have called sleep with increasing delays
            assert mock_sleep.call_count == 3  # 3 retries
            # Check exponential backoff: 1, 2, 4 seconds
            expected_delays = [1, 2, 4]
            actual_delays = [call.args[0] for call in mock_sleep.call_args_list]
            assert actual_delays == expected_delays

    def test_get_headers(self):
        """Test that proper headers are generated."""
        client = GitHubClient(token="test_token", repo_owner="test", repo_name="repo")
        headers = client._get_headers()

        expected_headers = {
            "Authorization": "Bearer test_token",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "md-manager/1.0"
        }

        assert headers == expected_headers

    def test_get_headers_with_custom_user_agent(self):
        """Test headers with custom user agent."""
        client = GitHubClient(
            token="test_token",
            repo_owner="test",
            repo_name="repo",
            user_agent="custom-agent/2.0"
        )
        headers = client._get_headers()

        assert headers["User-Agent"] == "custom-agent/2.0"

    @responses.activate
    def test_rate_limit_preemptive_delay(self):
        """Test that client waits when rate limit is low."""
        # First response with very low rate limit
        responses.add(
            responses.GET,
            "https://api.github.com/repos/test/repo/issues",
            json={"test": "data"},
            status=200,
            headers={
                "X-RateLimit-Remaining": "5",  # Very low
                "X-RateLimit-Reset": str(int(time.time()) + 10)
            }
        )

        # Second response - this request should be delayed
        responses.add(
            responses.GET,
            "https://api.github.com/repos/test/repo/comments",
            json={"test": "data2"},
            status=200,
            headers={
                "X-RateLimit-Remaining": "4",
                "X-RateLimit-Reset": str(int(time.time()) + 10)
            }
        )

        client = GitHubClient(token="test_token", repo_owner="test", repo_name="repo")

        # First request - establishes low rate limit
        client._make_request("GET", "/repos/test/repo/issues")

        with patch('time.sleep') as mock_sleep:
            # Second request - should trigger delay due to low rate limit from first request
            client._make_request("GET", "/repos/test/repo/comments")

            # Should have slept to avoid hitting rate limit
            assert mock_sleep.called