"""Tests for authentication providers."""

import os
import pytest
from unittest.mock import Mock, patch, mock_open

from md_manager.auth import (
    AuthenticationProvider, TokenAuth, GitHubAppAuth, OAuthAuth,
    AuthenticationFactory, get_authentication_provider
)


class TestTokenAuth:
    """Test cases for TokenAuth provider."""

    def test_token_auth_valid(self):
        """Test TokenAuth with valid token."""
        auth = TokenAuth(token="test-token")

        assert auth.is_valid()
        headers = auth.get_auth_headers()
        assert headers["Authorization"] == "Bearer test-token"
        assert headers["Accept"] == "application/vnd.github.v3+json"

    def test_token_auth_empty(self):
        """Test TokenAuth with empty token."""
        auth = TokenAuth(token="")
        assert not auth.is_valid()

    def test_token_auth_none(self):
        """Test TokenAuth with None token."""
        auth = TokenAuth(token=None)
        assert not auth.is_valid()


class TestGitHubAppAuth:
    """Test cases for GitHubAppAuth provider."""

    def test_github_app_auth_valid_with_content(self):
        """Test GitHubAppAuth with private key content."""
        auth = GitHubAppAuth(
            app_id="12345",
            private_key_content="-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----"
        )

        assert auth.is_valid()

    def test_github_app_auth_valid_with_path(self):
        """Test GitHubAppAuth with private key path."""
        with patch('os.path.exists', return_value=True):
            auth = GitHubAppAuth(
                app_id="12345",
                private_key_path="/path/to/key.pem"
            )

            assert auth.is_valid()

    def test_github_app_auth_invalid_no_app_id(self):
        """Test GitHubAppAuth without app_id."""
        auth = GitHubAppAuth(
            app_id="",
            private_key_content="test-key"
        )

        assert not auth.is_valid()

    def test_github_app_auth_invalid_no_key(self):
        """Test GitHubAppAuth without private key."""
        auth = GitHubAppAuth(app_id="12345")
        assert not auth.is_valid()

    def test_github_app_auth_headers_placeholder(self):
        """Test GitHubAppAuth headers return placeholder."""
        auth = GitHubAppAuth(
            app_id="12345",
            private_key_content="test-key"
        )

        headers = auth.get_auth_headers()
        assert headers["Authorization"] == "Bearer placeholder-token"
        assert headers["Accept"] == "application/vnd.github.v3+json"

    def test_get_private_key_from_content(self):
        """Test getting private key from content."""
        key_content = "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----"
        auth = GitHubAppAuth(
            app_id="12345",
            private_key_content=key_content
        )

        assert auth._get_private_key() == key_content

    def test_get_private_key_from_file(self):
        """Test getting private key from file."""
        key_content = "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----"

        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=key_content)):
                auth = GitHubAppAuth(
                    app_id="12345",
                    private_key_path="/path/to/key.pem"
                )

                assert auth._get_private_key() == key_content

    def test_get_private_key_file_not_found(self):
        """Test getting private key when file doesn't exist."""
        with patch('os.path.exists', return_value=False):
            auth = GitHubAppAuth(
                app_id="12345",
                private_key_path="/path/to/nonexistent.pem"
            )

            with pytest.raises(ValueError, match="No valid private key found"):
                auth._get_private_key()

    def test_generate_jwt_not_implemented(self):
        """Test JWT generation raises NotImplementedError."""
        auth = GitHubAppAuth(
            app_id="12345",
            private_key_content="test-key"
        )

        with pytest.raises(NotImplementedError, match="JWT generation requires PyJWT library"):
            auth._generate_jwt()

    def test_get_installation_token_not_implemented(self):
        """Test installation token retrieval raises NotImplementedError."""
        auth = GitHubAppAuth(
            app_id="12345",
            private_key_content="test-key"
        )

        with pytest.raises(NotImplementedError, match="Installation token retrieval not implemented"):
            auth._get_installation_token()


class TestOAuthAuth:
    """Test cases for OAuthAuth provider."""

    def test_oauth_auth_valid(self):
        """Test OAuthAuth with valid credentials."""
        auth = OAuthAuth(
            client_id="test-client-id",
            client_secret="test-client-secret"
        )

        assert auth.is_valid()

    def test_oauth_auth_invalid_no_client_id(self):
        """Test OAuthAuth without client_id."""
        auth = OAuthAuth(
            client_id="",
            client_secret="test-client-secret"
        )

        assert not auth.is_valid()

    def test_oauth_auth_invalid_no_client_secret(self):
        """Test OAuthAuth without client_secret."""
        auth = OAuthAuth(
            client_id="test-client-id",
            client_secret=""
        )

        assert not auth.is_valid()

    def test_oauth_auth_headers_no_token(self):
        """Test OAuthAuth headers without access token."""
        auth = OAuthAuth(
            client_id="test-client-id",
            client_secret="test-client-secret"
        )

        headers = auth.get_auth_headers()
        assert headers == {}

    def test_oauth_auth_headers_with_token(self):
        """Test OAuthAuth headers with access token."""
        auth = OAuthAuth(
            client_id="test-client-id",
            client_secret="test-client-secret",
            access_token="test-access-token"
        )

        headers = auth.get_auth_headers()
        assert headers["Authorization"] == "Bearer test-access-token"
        assert headers["Accept"] == "application/vnd.github.v3+json"

    def test_oauth_auth_default_scopes(self):
        """Test OAuthAuth with default scopes."""
        auth = OAuthAuth(
            client_id="test-client-id",
            client_secret="test-client-secret"
        )

        assert auth.scopes == ["repo"]

    def test_oauth_auth_custom_scopes(self):
        """Test OAuthAuth with custom scopes."""
        custom_scopes = ["repo", "user", "admin:org"]
        auth = OAuthAuth(
            client_id="test-client-id",
            client_secret="test-client-secret",
            scopes=custom_scopes
        )

        assert auth.scopes == custom_scopes

    def test_get_authorization_url(self):
        """Test OAuth authorization URL generation."""
        auth = OAuthAuth(
            client_id="test-client-id",
            client_secret="test-client-secret",
            redirect_uri="http://localhost:8080/callback",
            scopes=["repo", "user"]
        )

        url = auth.get_authorization_url()

        assert "https://github.com/login/oauth/authorize" in url
        assert "client_id=test-client-id" in url
        assert "redirect_uri=http://localhost:8080/callback" in url
        assert "scope=repo,user" in url
        assert "state=md-manager-auth" in url

    def test_start_oauth_flow(self):
        """Test starting OAuth flow returns authorization URL."""
        auth = OAuthAuth(
            client_id="test-client-id",
            client_secret="test-client-secret"
        )

        url = auth.start_oauth_flow()
        assert "https://github.com/login/oauth/authorize" in url

    def test_exchange_code_for_token_not_implemented(self):
        """Test OAuth code exchange raises NotImplementedError."""
        auth = OAuthAuth(
            client_id="test-client-id",
            client_secret="test-client-secret"
        )

        with pytest.raises(NotImplementedError, match="OAuth token exchange not implemented"):
            auth.exchange_code_for_token("test-code")


class TestAuthenticationFactory:
    """Test cases for AuthenticationFactory."""

    def test_create_token_auth(self):
        """Test creating TokenAuth from config."""
        config = {
            "auth_method": "token",
            "token": "test-token"
        }

        auth = AuthenticationFactory.create_from_config(config)

        assert isinstance(auth, TokenAuth)
        assert auth.token == "test-token"

    def test_create_github_app_auth(self):
        """Test creating GitHubAppAuth from config."""
        config = {
            "auth_method": "app",
            "app_config": {
                "app_id": "12345",
                "private_key_content": "test-key",
                "installation_id": "67890"
            }
        }

        auth = AuthenticationFactory.create_from_config(config)

        assert isinstance(auth, GitHubAppAuth)
        assert auth.app_id == "12345"
        assert auth.private_key_content == "test-key"
        assert auth.installation_id == "67890"

    def test_create_oauth_auth(self):
        """Test creating OAuthAuth from config."""
        config = {
            "auth_method": "oauth",
            "oauth_config": {
                "client_id": "test-client-id",
                "client_secret": "test-client-secret",
                "redirect_uri": "http://localhost:9000/callback",
                "scopes": ["repo", "user"]
            }
        }

        auth = AuthenticationFactory.create_from_config(config)

        assert isinstance(auth, OAuthAuth)
        assert auth.client_id == "test-client-id"
        assert auth.client_secret == "test-client-secret"
        assert auth.redirect_uri == "http://localhost:9000/callback"
        assert auth.scopes == ["repo", "user"]

    def test_create_oauth_auth_with_defaults(self):
        """Test creating OAuthAuth with default values."""
        config = {
            "auth_method": "oauth",
            "oauth_config": {
                "client_id": "test-client-id",
                "client_secret": "test-client-secret"
            }
        }

        auth = AuthenticationFactory.create_from_config(config)

        assert isinstance(auth, OAuthAuth)
        assert auth.redirect_uri == "http://localhost:8080/callback"
        assert auth.scopes == ["repo"]

    def test_create_invalid_auth_method(self):
        """Test creating auth with invalid method returns None."""
        config = {
            "auth_method": "invalid",
            "token": "test-token"
        }

        auth = AuthenticationFactory.create_from_config(config)
        assert auth is None

    def test_create_token_auth_missing_token(self):
        """Test creating TokenAuth without token returns None."""
        config = {
            "auth_method": "token"
        }

        auth = AuthenticationFactory.create_from_config(config)
        assert auth is None

    def test_create_app_auth_missing_app_id(self):
        """Test creating GitHubAppAuth without app_id returns None."""
        config = {
            "auth_method": "app",
            "app_config": {
                "private_key_content": "test-key"
            }
        }

        auth = AuthenticationFactory.create_from_config(config)
        assert auth is None

    def test_create_oauth_auth_missing_credentials(self):
        """Test creating OAuthAuth without credentials returns None."""
        config = {
            "auth_method": "oauth",
            "oauth_config": {
                "client_id": "test-client-id"
                # Missing client_secret
            }
        }

        auth = AuthenticationFactory.create_from_config(config)
        assert auth is None

    def test_create_with_default_auth_method(self):
        """Test creating auth with default token method."""
        config = {
            "token": "test-token"
        }

        auth = AuthenticationFactory.create_from_config(config)

        assert isinstance(auth, TokenAuth)
        assert auth.token == "test-token"


class TestGetAuthenticationProvider:
    """Test cases for get_authentication_provider function."""

    def test_get_authentication_provider_token(self):
        """Test getting TokenAuth provider."""
        config = {
            "auth_method": "token",
            "token": "test-token"
        }

        auth = get_authentication_provider(config)

        assert isinstance(auth, TokenAuth)
        assert auth.token == "test-token"

    def test_get_authentication_provider_none(self):
        """Test getting None when no valid auth found."""
        config = {
            "auth_method": "invalid"
        }

        auth = get_authentication_provider(config)
        assert auth is None

    def test_get_authentication_provider_with_enum(self):
        """Test getting auth provider when auth_method is an enum."""
        from md_manager.config import AuthMethod

        config = {
            "auth_method": AuthMethod.TOKEN,
            "token": "test-token"
        }

        auth = get_authentication_provider(config)

        assert isinstance(auth, TokenAuth)
        assert auth.token == "test-token"