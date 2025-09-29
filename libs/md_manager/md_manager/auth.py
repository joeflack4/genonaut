"""Enhanced authentication methods for GitHub integration.

This module provides multiple authentication methods for GitHub API access:
- Personal Access Tokens (existing)
- GitHub App authentication
- OAuth flow for interactive usage
"""

import os
import time
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod


class AuthenticationProvider(ABC):
    """Abstract base class for GitHub authentication providers."""

    @abstractmethod
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for GitHub API requests."""
        pass

    @abstractmethod
    def is_valid(self) -> bool:
        """Check if the authentication is valid and can be used."""
        pass


@dataclass
class TokenAuth(AuthenticationProvider):
    """Personal Access Token authentication."""

    token: str

    def get_auth_headers(self) -> Dict[str, str]:
        """Get headers for token authentication."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def is_valid(self) -> bool:
        """Check if token is present."""
        return bool(self.token)


@dataclass
class GitHubAppAuth(AuthenticationProvider):
    """GitHub App authentication with JWT and installation tokens."""

    app_id: str
    private_key_content: Optional[str] = None
    private_key_path: Optional[str] = None
    installation_id: Optional[str] = None
    logger: Optional[logging.Logger] = None

    def __post_init__(self):
        """Initialize logger and validate configuration."""
        if not self.logger:
            self.logger = logging.getLogger(__name__)

    def get_auth_headers(self) -> Dict[str, str]:
        """Get headers for GitHub App authentication."""
        # For now, return placeholder until JWT implementation
        self.logger.warning("GitHub App authentication requires JWT implementation")
        return {
            "Authorization": "Bearer placeholder-token",
            "Accept": "application/vnd.github.v3+json"
        }

    def is_valid(self) -> bool:
        """Check if GitHub App configuration is valid."""
        return (
            bool(self.app_id) and
            (bool(self.private_key_content) or bool(self.private_key_path))
        )

    def _get_private_key(self) -> str:
        """Get the private key content."""
        if self.private_key_content:
            return self.private_key_content

        if self.private_key_path and os.path.exists(self.private_key_path):
            with open(self.private_key_path, 'r') as f:
                return f.read()

        raise ValueError("No valid private key found")

    def _generate_jwt(self) -> str:
        """Generate JWT token for GitHub App authentication."""
        # Placeholder for JWT implementation
        # This would require PyJWT or similar library
        raise NotImplementedError("JWT generation requires PyJWT library")

    def _get_installation_token(self) -> str:
        """Get installation access token using JWT."""
        # Placeholder for installation token retrieval
        raise NotImplementedError("Installation token retrieval not implemented")


@dataclass
class OAuthAuth(AuthenticationProvider):
    """OAuth authentication for interactive usage."""

    client_id: str
    client_secret: str
    redirect_uri: str = "http://localhost:8080/callback"
    scopes: list = None
    access_token: Optional[str] = None
    logger: Optional[logging.Logger] = None

    def __post_init__(self):
        """Initialize default scopes and logger."""
        if self.scopes is None:
            self.scopes = ["repo"]
        if not self.logger:
            self.logger = logging.getLogger(__name__)

    def get_auth_headers(self) -> Dict[str, str]:
        """Get headers for OAuth authentication."""
        if not self.access_token:
            self.logger.warning("OAuth flow not completed - no access token available")
            return {}

        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def is_valid(self) -> bool:
        """Check if OAuth configuration is valid."""
        return bool(self.client_id and self.client_secret)

    def get_authorization_url(self) -> str:
        """Get the GitHub OAuth authorization URL."""
        scopes_str = ",".join(self.scopes)
        return (
            f"https://github.com/login/oauth/authorize"
            f"?client_id={self.client_id}"
            f"&redirect_uri={self.redirect_uri}"
            f"&scope={scopes_str}"
            f"&state=md-manager-auth"
        )

    def exchange_code_for_token(self, code: str) -> str:
        """Exchange authorization code for access token."""
        # Placeholder for OAuth token exchange
        # This would require making HTTP requests to GitHub's OAuth endpoint
        raise NotImplementedError("OAuth token exchange not implemented")

    def start_oauth_flow(self) -> str:
        """Start the OAuth authorization flow."""
        auth_url = self.get_authorization_url()
        self.logger.info(f"Please visit the following URL to authorize the application:")
        self.logger.info(auth_url)
        return auth_url


class AuthenticationFactory:
    """Factory for creating authentication providers."""

    @staticmethod
    def create_from_config(config: Dict[str, Any]) -> Optional[AuthenticationProvider]:
        """
        Create an authentication provider from configuration.

        Args:
            config: GitHub configuration dictionary

        Returns:
            Authentication provider instance or None
        """
        auth_method = config.get('auth_method', 'token')

        # Handle enum values by converting to string
        if hasattr(auth_method, 'value'):
            auth_method = auth_method.value

        if auth_method == 'token':
            token = config.get('token')
            if token:
                return TokenAuth(token=token)

        elif auth_method == 'app':
            app_config = config.get('app_config', {})
            if app_config.get('app_id'):
                return GitHubAppAuth(
                    app_id=app_config['app_id'],
                    private_key_content=app_config.get('private_key_content'),
                    private_key_path=app_config.get('private_key_path'),
                    installation_id=app_config.get('installation_id')
                )

        elif auth_method == 'oauth':
            oauth_config = config.get('oauth_config', {})
            if oauth_config.get('client_id') and oauth_config.get('client_secret'):
                return OAuthAuth(
                    client_id=oauth_config['client_id'],
                    client_secret=oauth_config['client_secret'],
                    redirect_uri=oauth_config.get('redirect_uri', 'http://localhost:8080/callback'),
                    scopes=oauth_config.get('scopes', ['repo'])
                )

        return None


def get_authentication_provider(github_config: Dict[str, Any]) -> Optional[AuthenticationProvider]:
    """
    Get the appropriate authentication provider based on configuration.

    Args:
        github_config: GitHub configuration dictionary

    Returns:
        Authentication provider instance or None if no valid auth found
    """
    return AuthenticationFactory.create_from_config(github_config)