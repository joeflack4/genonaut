"""GitHub API client with authentication, rate limiting, and error handling."""

import time
import json
import logging
import requests
from datetime import datetime
from typing import Dict, Any, Optional, Iterator, Union, List
from urllib.parse import urljoin, urlparse, parse_qs

from .auth import AuthenticationProvider
from .cache import APICache, create_cache_provider


class GitHubError(Exception):
    """Base exception for GitHub API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response

    def is_retryable(self) -> bool:
        """Check if this error is retryable."""
        return False


class RateLimitError(GitHubError):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, message: str, reset_time: int):
        super().__init__(message)
        self.reset_time = reset_time

    def is_retryable(self) -> bool:
        """Rate limit errors are retryable after waiting."""
        return True


class AuthenticationError(GitHubError):
    """Exception raised for authentication issues."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class AuthorizationError(GitHubError):
    """Exception raised for authorization/permission issues."""

    def __init__(self, message: str = "Access denied"):
        super().__init__(message, status_code=403)


class NotFoundError(GitHubError):
    """Exception raised when resource is not found."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class ValidationError(GitHubError):
    """Exception raised for input validation errors."""

    def __init__(self, message: str = "Invalid input"):
        super().__init__(message, status_code=422)


class ServerError(GitHubError):
    """Exception raised for server-side errors."""

    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message, status_code)

    def is_retryable(self) -> bool:
        """Server errors are generally retryable."""
        return True


class NetworkError(GitHubError):
    """Exception raised for network-related issues."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error

    def is_retryable(self) -> bool:
        """Network errors are usually retryable."""
        return True


class GitHubClient:
    """
    GitHub API client with authentication, rate limiting, and error handling.

    Features:
    - Bearer token authentication
    - Automatic rate limiting with exponential backoff
    - Pagination support
    - Retry logic for server errors
    - GitHub Enterprise support
    """

    def __init__(
        self,
        auth_provider: Optional[AuthenticationProvider] = None,
        token: Optional[str] = None,
        repo_owner: Optional[str] = None,
        repo_name: Optional[str] = None,
        base_url: str = "https://api.github.com",
        user_agent: str = "md-manager/1.0",
        max_retries: int = 3,
        rate_limit_threshold: int = 10,
        enable_caching: bool = True,
        cache_ttl: int = 300
    ):
        """
        Initialize GitHub client.

        Args:
            auth_provider: Authentication provider instance
            token: GitHub personal access token (deprecated, use auth_provider)
            repo_owner: Repository owner (username or organization)
            repo_name: Repository name
            base_url: GitHub API base URL (for GitHub Enterprise)
            user_agent: User agent string for requests
            max_retries: Maximum number of retries for failed requests
            rate_limit_threshold: Threshold below which to proactively delay
            enable_caching: Enable response caching (default: True)
            cache_ttl: Cache time-to-live in seconds (default: 300)
        """
        # Handle backward compatibility with token parameter
        if auth_provider is None and token:
            from .auth import TokenAuth
            auth_provider = TokenAuth(token=token)
        elif auth_provider is None:
            raise ValueError("Either auth_provider or token is required")

        if not auth_provider.is_valid():
            raise ValueError("Invalid authentication provider")

        self.auth_provider = auth_provider
        self.token = token  # Keep for backward compatibility
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.base_url = base_url.rstrip('/')
        self.user_agent = user_agent
        self.max_retries = max_retries
        self.rate_limit_threshold = rate_limit_threshold
        self.enable_caching = enable_caching
        self.cache_ttl = cache_ttl

        # Initialize caching
        self.cache = None
        if enable_caching:
            cache_provider = create_cache_provider("memory")  # Use in-memory for simplicity
            self.cache = APICache(cache_provider, default_ttl=cache_ttl)

        # Rate limiting state
        self.rate_limit_remaining: Optional[int] = None
        self.rate_limit_reset: Optional[int] = None
        self.rate_limit_limit: Optional[int] = None

        # Rate limiting monitoring
        self.rate_limit_stats = {
            "requests_made": 0,
            "rate_limit_hits": 0,
            "delays_triggered": 0,
            "total_delay_time": 0.0,
            "last_reset_time": None
        }

        # Requests session for connection pooling
        self.session = requests.Session()

        # Set up logging
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for GitHub API requests."""
        headers = self.auth_provider.get_auth_headers()
        headers["User-Agent"] = self.user_agent
        return headers

    def _get_cache_ttl(self, endpoint: str, response_data: Dict[str, Any]) -> int:
        """
        Determine cache TTL based on endpoint and response characteristics.

        Args:
            endpoint: API endpoint
            response_data: Response data

        Returns:
            Cache TTL in seconds
        """
        # Repository information changes infrequently - cache longer
        if "/repos/" in endpoint and endpoint.endswith(("/repos", "/repository")):
            return 3600  # 1 hour

        # Issue lists can change frequently - shorter cache
        if "/issues" in endpoint and isinstance(response_data, list):
            return 300  # 5 minutes

        # Individual issues change less frequently than lists
        if "/issues/" in endpoint and not endpoint.endswith("/issues"):
            return 600  # 10 minutes

        # Project data changes infrequently
        if "/projects" in endpoint:
            return 1800  # 30 minutes

        # Rate limit status changes frequently
        if "rate_limit" in endpoint:
            return 60  # 1 minute

        # Default TTL
        return self.cache_ttl

    def _update_rate_limit_info(self, response: requests.Response) -> None:
        """Update rate limit information from response headers."""
        # Track total requests made
        self.rate_limit_stats["requests_made"] += 1

        # Update rate limit values
        if "X-RateLimit-Remaining" in response.headers:
            prev_remaining = self.rate_limit_remaining
            self.rate_limit_remaining = int(response.headers["X-RateLimit-Remaining"])

            # Log significant rate limit changes
            if prev_remaining is not None and prev_remaining > 100 and self.rate_limit_remaining <= 100:
                self.logger.warning(f"Rate limit dropping: {self.rate_limit_remaining} requests remaining")
            elif prev_remaining is not None and prev_remaining > 10 and self.rate_limit_remaining <= 10:
                self.logger.warning(f"Rate limit critically low: {self.rate_limit_remaining} requests remaining")

        if "X-RateLimit-Reset" in response.headers:
            new_reset = int(response.headers["X-RateLimit-Reset"])
            if self.rate_limit_reset != new_reset:
                self.rate_limit_stats["last_reset_time"] = new_reset
            self.rate_limit_reset = new_reset

        if "X-RateLimit-Limit" in response.headers:
            self.rate_limit_limit = int(response.headers["X-RateLimit-Limit"])

        # Log rate limit status at debug level
        self.logger.debug(
            f"Rate limit status: {self.rate_limit_remaining}/{self.rate_limit_limit} remaining, "
            f"resets at {self.rate_limit_reset}"
        )

    def _check_rate_limit(self) -> None:
        """Check if we should delay to avoid hitting rate limit."""
        if self.rate_limit_remaining is None:
            return  # No rate limit info available yet

        # Calculate adaptive threshold based on remaining time until reset
        adaptive_threshold = self._calculate_adaptive_threshold()

        if self.rate_limit_remaining <= adaptive_threshold:
            self.rate_limit_stats["delays_triggered"] += 1

            if self.rate_limit_reset is not None:
                delay = max(0, self.rate_limit_reset - int(time.time()) + 1)
                if delay > 0:
                    self.logger.info(f"Rate limit threshold reached. Waiting {delay}s until reset...")
                    self.rate_limit_stats["total_delay_time"] += delay
                    time.sleep(delay)
                    self.logger.info("Rate limit reset. Resuming requests.")
            else:
                # If no reset time, do a progressive delay based on remaining requests
                delay = min(60, max(1, (self.rate_limit_threshold - self.rate_limit_remaining) * 2))
                self.logger.info(f"Rate limit threshold reached. Waiting {delay}s...")
                self.rate_limit_stats["total_delay_time"] += delay
                time.sleep(delay)

    def _calculate_adaptive_threshold(self) -> int:
        """Calculate adaptive rate limit threshold based on current conditions."""
        if self.rate_limit_reset is None or self.rate_limit_remaining is None:
            return self.rate_limit_threshold

        # Calculate time until reset
        time_until_reset = max(0, self.rate_limit_reset - int(time.time()))

        # If reset is very soon (< 1 minute), be more conservative
        if time_until_reset < 60:  # 1 minute
            return min(self.rate_limit_threshold, max(self.rate_limit_threshold // 2, self.rate_limit_remaining // 2))

        # If reset is soon (< 10 minutes), be somewhat conservative
        elif time_until_reset < 600:  # 10 minutes
            return min(self.rate_limit_threshold, max(5, int(self.rate_limit_threshold * 0.8)))

        # If plenty of time, use standard threshold
        return self.rate_limit_threshold

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict, str]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make a request to GitHub API with retry logic and rate limiting.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            endpoint: API endpoint (e.g., "/repos/owner/repo/issues")
            params: Query parameters
            data: Request body data
            headers: Additional headers

        Returns:
            JSON response data

        Raises:
            GitHubError: For API errors
            RateLimitError: When rate limit is exceeded
        """
        url = urljoin(self.base_url, endpoint.lstrip('/'))
        request_headers = self._get_headers()

        if headers:
            request_headers.update(headers)

        # For GET requests with caching enabled, check cache first
        if method == "GET" and self.cache:
            cached_response = self.cache.get_cached_response(endpoint, params)
            if cached_response:
                self.logger.debug(f"Cache hit for {endpoint}")
                return cached_response

            # Add conditional headers for ETag support
            conditional_headers = self.cache.get_conditional_headers(endpoint, params)
            request_headers.update(conditional_headers)

        # Check rate limit before making request
        self._check_rate_limit()

        self.logger.debug(f"Making {method} request to {url}")

        for attempt in range(self.max_retries + 1):
            try:
                if isinstance(data, dict):
                    data = json.dumps(data)
                    request_headers["Content-Type"] = "application/json"

                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    data=data,
                    headers=request_headers,
                    timeout=30
                )

                # Update rate limit info
                self._update_rate_limit_info(response)

                # Handle rate limiting
                if response.status_code == 403 and "rate limit" in response.text.lower():
                    self.rate_limit_stats["rate_limit_hits"] += 1
                    reset_time = int(response.headers.get("X-RateLimit-Reset", time.time() + 60))
                    self.logger.warning(f"Rate limit exceeded! Reset at {reset_time}")
                    raise RateLimitError(
                        f"Rate limit exceeded. Resets at {reset_time}",
                        reset_time
                    )

                # Handle 304 Not Modified (cached response is still valid)
                if response.status_code == 304 and method == "GET" and self.cache:
                    cached_response = self.cache.get_cached_response(endpoint, params)
                    if cached_response:
                        self.logger.debug(f"304 Not Modified for {endpoint}, returning cached response")
                        return cached_response

                # Handle successful responses
                if 200 <= response.status_code < 300:
                    try:
                        response_data = response.json()

                        # Cache GET responses if caching is enabled
                        if method == "GET" and self.cache:
                            etag = response.headers.get("ETag")
                            last_modified = response.headers.get("Last-Modified")

                            # Use custom TTL based on response type
                            cache_ttl = self._get_cache_ttl(endpoint, response_data)

                            self.cache.cache_response(
                                endpoint, response_data, params,
                                etag=etag, last_modified=last_modified, ttl=cache_ttl
                            )

                        return response_data
                    except json.JSONDecodeError:
                        # Some endpoints return empty responses
                        return {}

                # Handle specific client errors with appropriate exception types
                if response.status_code == 401:
                    try:
                        error_data = response.json()
                        message = error_data.get("message", "Authentication failed")
                    except json.JSONDecodeError:
                        message = "Authentication failed"
                    raise AuthenticationError(message)

                elif response.status_code == 403:
                    try:
                        error_data = response.json()
                        message = error_data.get("message", "Access denied")
                    except json.JSONDecodeError:
                        message = "Access denied"
                    # Check if it's a rate limit error (different from auth error)
                    if "rate limit" not in message.lower():
                        raise AuthorizationError(message)

                elif response.status_code == 404:
                    try:
                        error_data = response.json()
                        message = error_data.get("message", "Resource not found")
                    except json.JSONDecodeError:
                        message = "Resource not found"
                    raise NotFoundError(message)

                elif response.status_code == 422:
                    try:
                        error_data = response.json()
                        message = error_data.get("message", "Invalid input")
                        # Include validation errors if available
                        if "errors" in error_data:
                            error_details = [err.get("message", str(err)) for err in error_data["errors"]]
                            message += f": {', '.join(error_details)}"
                    except json.JSONDecodeError:
                        message = "Invalid input"
                    raise ValidationError(message)

                # Handle other client errors (don't retry)
                elif 400 <= response.status_code < 500:
                    try:
                        error_data = response.json()
                        message = error_data.get("message", f"HTTP {response.status_code}")
                    except json.JSONDecodeError:
                        message = f"HTTP {response.status_code}: {response.text}"
                    raise GitHubError(message, response.status_code, error_data if 'error_data' in locals() else None)

                # Handle server errors (retry with backoff)
                elif response.status_code >= 500:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    if attempt < self.max_retries:
                        delay = 2 ** attempt  # Exponential backoff: 1, 2, 4 seconds
                        self.logger.warning(f"Server error (attempt {attempt + 1}/{self.max_retries + 1}): {error_msg}. Retrying in {delay}s")
                        time.sleep(delay)
                        continue
                    # Final attempt failed
                    self.logger.error(f"Server error after {self.max_retries + 1} attempts: {error_msg}")
                    raise ServerError(error_msg, response.status_code)

                # Handle other status codes
                else:
                    if attempt < self.max_retries:
                        delay = 2 ** attempt
                        time.sleep(delay)
                        continue
                    raise GitHubError(f"HTTP {response.status_code}: {response.text}", response.status_code)

            except requests.exceptions.Timeout as e:
                if attempt < self.max_retries:
                    delay = 2 ** attempt
                    time.sleep(delay)
                    continue
                raise NetworkError(f"Request timed out after 30 seconds", e)

            except requests.exceptions.ConnectionError as e:
                if attempt < self.max_retries:
                    delay = 2 ** attempt
                    time.sleep(delay)
                    continue
                raise NetworkError(f"Connection failed: {str(e)}", e)

            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries:
                    delay = 2 ** attempt
                    time.sleep(delay)
                    continue
                raise NetworkError(f"Request failed: {str(e)}", e)

    def _parse_link_header(self, link_header: str) -> Optional[str]:
        """Parse Link header to extract next page URL."""
        if not link_header:
            return None

        links = {}
        for link in link_header.split(','):
            try:
                url_part, rel_part = link.strip().split(';', 1)
                url = url_part.strip('<>')
                rel = rel_part.split('=')[1].strip('"')
                links[rel] = url
            except (ValueError, IndexError):
                continue

        return links.get('next')

    def _paginate_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Iterator[Dict[str, Any]]:
        """
        Make paginated requests to GitHub API.

        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters

        Yields:
            Individual items from paginated response
        """
        current_url = endpoint
        query_params = params.copy() if params else {}

        while current_url:
            # Make request - but we need the raw response to get headers
            url = urljoin(self.base_url, current_url.lstrip('/'))
            request_headers = self._get_headers()

            # Check rate limit before making request
            self._check_rate_limit()

            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=query_params if current_url == endpoint else None,
                    headers=request_headers,
                    timeout=30
                )

                # Update rate limit info
                self._update_rate_limit_info(response)

                # Handle error responses with specific error types
                if response.status_code == 401:
                    raise AuthenticationError("Authentication failed during pagination")
                elif response.status_code == 403:
                    if "rate limit" in response.text.lower():
                        reset_time = int(response.headers.get("X-RateLimit-Reset", time.time() + 60))
                        raise RateLimitError(f"Rate limit exceeded during pagination", reset_time)
                    else:
                        raise AuthorizationError("Access denied during pagination")
                elif response.status_code == 404:
                    raise NotFoundError("Resource not found during pagination")
                elif not (200 <= response.status_code < 300):
                    if response.status_code >= 500:
                        raise ServerError(f"HTTP {response.status_code}: {response.text}", response.status_code)
                    else:
                        raise GitHubError(f"HTTP {response.status_code}: {response.text}", response.status_code)

            except requests.exceptions.Timeout:
                raise NetworkError("Request timed out during pagination")
            except requests.exceptions.ConnectionError as e:
                raise NetworkError(f"Connection failed during pagination: {str(e)}")
            except requests.exceptions.RequestException as e:
                raise NetworkError(f"Request failed during pagination: {str(e)}")

            try:
                data = response.json()
            except json.JSONDecodeError:
                data = {}

            # GitHub API returns list for most paginated endpoints
            if isinstance(data, list):
                for item in data:
                    yield item
            else:
                # Some endpoints return objects with items
                items = data.get('items', [])
                for item in items:
                    yield item

            # Parse Link header for next page
            link_header = response.headers.get('Link', '')
            next_url = self._parse_link_header(link_header)

            if next_url:
                # Extract just the path and query from the next URL
                parsed = urlparse(next_url)
                current_url = parsed.path
                if parsed.query:
                    current_url += '?' + parsed.query
                query_params = {}  # URL already includes params
            else:
                current_url = None

    def get_repo_info(self) -> Dict[str, Any]:
        """Get repository information."""
        if not self.repo_owner or not self.repo_name:
            raise ValueError("Repository owner and name must be set")

        return self._make_request("GET", f"/repos/{self.repo_owner}/{self.repo_name}")

    def test_connection(self) -> bool:
        """
        Test GitHub API connection and authentication.

        Returns:
            True if connection is successful
        """
        try:
            self._make_request("GET", "/user")
            return True
        except GitHubError:
            return False

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get current rate limit status.

        Returns:
            Dictionary with rate limit information
        """
        return {
            "remaining": self.rate_limit_remaining,
            "limit": self.rate_limit_limit,
            "reset_time": self.rate_limit_reset,
            "reset_datetime": datetime.fromtimestamp(self.rate_limit_reset) if self.rate_limit_reset else None,
            "time_until_reset": max(0, self.rate_limit_reset - int(time.time())) if self.rate_limit_reset else None,
            "percentage_used": (
                round((self.rate_limit_limit - self.rate_limit_remaining) / self.rate_limit_limit * 100, 1)
                if self.rate_limit_limit and self.rate_limit_remaining is not None
                else None
            )
        }

    def get_rate_limit_stats(self) -> Dict[str, Any]:
        """
        Get rate limiting statistics for monitoring.

        Returns:
            Dictionary with rate limit statistics
        """
        stats = self.rate_limit_stats.copy()

        # Add calculated metrics
        if stats["requests_made"] > 0:
            stats["rate_limit_hit_rate"] = round(stats["rate_limit_hits"] / stats["requests_made"] * 100, 2)
            stats["delay_rate"] = round(stats["delays_triggered"] / stats["requests_made"] * 100, 2)
            stats["average_delay_time"] = (
                round(stats["total_delay_time"] / stats["delays_triggered"], 2)
                if stats["delays_triggered"] > 0 else 0
            )
        else:
            stats["rate_limit_hit_rate"] = 0
            stats["delay_rate"] = 0
            stats["average_delay_time"] = 0

        return stats

    def reset_rate_limit_stats(self) -> None:
        """Reset rate limiting statistics."""
        self.rate_limit_stats = {
            "requests_made": 0,
            "rate_limit_hits": 0,
            "delays_triggered": 0,
            "total_delay_time": 0.0,
            "last_reset_time": None
        }

    def is_rate_limited(self) -> bool:
        """
        Check if we're currently at or near rate limit.

        Returns:
            True if rate limited or close to limit
        """
        if self.rate_limit_remaining is None:
            return False

        return self.rate_limit_remaining <= self._calculate_adaptive_threshold()

    def log_rate_limit_summary(self) -> None:
        """Log a summary of rate limit usage and statistics."""
        status = self.get_rate_limit_status()
        stats = self.get_rate_limit_stats()

        self.logger.info("=== Rate Limit Summary ===")
        if status["remaining"] is not None:
            self.logger.info(f"Current: {status['remaining']}/{status['limit']} remaining ({status['percentage_used']}% used)")
            if status["time_until_reset"]:
                reset_time = datetime.fromtimestamp(status["reset_time"])
                self.logger.info(f"Resets in {status['time_until_reset']}s at {reset_time}")

        self.logger.info(f"Session stats: {stats['requests_made']} requests, "
                        f"{stats['rate_limit_hits']} rate limit hits ({stats['rate_limit_hit_rate']}%), "
                        f"{stats['delays_triggered']} delays ({stats['delay_rate']}%)")

        if stats["total_delay_time"] > 0:
            self.logger.info(f"Total delay time: {stats['total_delay_time']}s "
                           f"(avg {stats['average_delay_time']}s per delay)")

        self.logger.info("==========================")

    # Project Board Integration Methods

    def get_repository_projects(self) -> List[Dict[str, Any]]:
        """
        Fetch all projects associated with the repository.

        Returns:
            List of project dictionaries with basic project info

        Raises:
            GitHubError: If fetching projects fails
        """
        try:
            all_projects = []

            # Try organization-level projects first
            try:
                org_projects = self._paginate_request(f"/orgs/{self.repo_owner}/projects")
                all_projects.extend(org_projects)
            except GitHubError:
                # Not an organization or no access, continue
                pass

            # Try user-level projects
            try:
                user_projects = self._paginate_request(f"/users/{self.repo_owner}/projects")
                all_projects.extend(user_projects)
            except GitHubError:
                # No user projects or no access, continue
                pass

            # Try repository-specific projects (legacy)
            try:
                repo_projects = self._paginate_request(f"/repos/{self.repo_owner}/{self.repo_name}/projects")
                all_projects.extend(repo_projects)
            except GitHubError:
                # No repo projects or no access, continue
                pass

            # Remove duplicates based on project ID
            seen_ids = set()
            unique_projects = []
            for project in all_projects:
                if project['id'] not in seen_ids:
                    seen_ids.add(project['id'])
                    unique_projects.append(project)

            self.logger.debug(f"Found {len(unique_projects)} unique projects")
            return unique_projects

        except Exception as e:
            self.logger.warning(f"Could not fetch repository projects: {e}")
            return []  # Return empty list if projects aren't accessible

    def get_issue_project_items(self, issue_number: int) -> Dict[str, Any]:
        """
        Get project board information for a specific issue.

        Args:
            issue_number: GitHub issue number

        Returns:
            Dictionary with project board data for the issue
        """
        try:
            # For now, return empty dict as GitHub Projects v2 requires GraphQL
            # This is a placeholder for future GraphQL implementation
            self.logger.debug(f"Project data for issue #{issue_number} requires GraphQL API (not yet implemented)")
            return {}

        except Exception as e:
            self.logger.warning(f"Could not fetch project data for issue #{issue_number}: {e}")
            return {}

    def update_issue_project_fields(self, issue_number: int, project_data: Dict[str, Any]) -> bool:
        """
        Update project board fields for an issue.

        Args:
            issue_number: GitHub issue number
            project_data: Dictionary with project field updates

        Returns:
            True if update was successful, False otherwise
        """
        try:
            # For now, return False as GitHub Projects v2 requires GraphQL
            # This is a placeholder for future GraphQL implementation
            self.logger.debug(f"Updating project data for issue #{issue_number} requires GraphQL API (not yet implemented)")
            return False

        except Exception as e:
            self.logger.warning(f"Could not update project data for issue #{issue_number}: {e}")
            return False

    # Cache Management Methods

    def invalidate_cache(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> bool:
        """
        Invalidate cached response for a specific endpoint.

        Args:
            endpoint: API endpoint to invalidate
            params: Query parameters

        Returns:
            True if cache entry was removed, False if not found or caching disabled
        """
        if not self.cache:
            return False

        return self.cache.invalidate_cache(endpoint, params)

    def clear_cache(self) -> None:
        """Clear all cached responses."""
        if self.cache:
            self.cache.clear_all()
            self.logger.info("Cleared all cached API responses")

    def cleanup_expired_cache(self) -> int:
        """
        Remove expired cache entries.

        Returns:
            Number of entries removed
        """
        if not self.cache:
            return 0

        removed_count = self.cache.cleanup_expired()
        if removed_count > 0:
            self.logger.debug(f"Cleaned up {removed_count} expired cache entries")
        return removed_count

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        if not self.cache:
            return {"caching_enabled": False}

        # For in-memory cache, get current entry count
        if hasattr(self.cache.cache_provider, '_cache'):
            entry_count = len(self.cache.cache_provider._cache)
        else:
            entry_count = "unknown"

        return {
            "caching_enabled": True,
            "default_ttl": self.cache_ttl,
            "entry_count": entry_count
        }