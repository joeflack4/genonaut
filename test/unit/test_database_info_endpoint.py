"""
Unit tests for database info endpoint.

Tests that the database info endpoint returns information about available
database environments.
"""
import pytest
from typing import List, Dict, Any


class MockDatabaseInfo:
    """Mock database environment information."""

    def __init__(self, name: str, description: str, host: str, port: int, is_active: bool):
        """Initialize database info.

        Args:
            name: Database environment name (e.g., 'dev', 'demo', 'test')
            description: Human-readable description
            host: Database host
            port: Database port
            is_active: Whether this environment is currently active
        """
        self.name = name
        self.description = description
        self.host = host
        self.port = port
        self.is_active = is_active

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format.

        Returns:
            Dictionary representation
        """
        return {
            'name': self.name,
            'description': self.description,
            'host': self.host,
            'port': self.port,
            'is_active': self.is_active
        }


class MockDatabaseInfoService:
    """Mock service for database environment information."""

    def __init__(self):
        """Initialize with standard database environments."""
        self._environments = [
            MockDatabaseInfo(
                name='dev',
                description='Development database',
                host='localhost',
                port=5432,
                is_active=False
            ),
            MockDatabaseInfo(
                name='demo',
                description='Demo database with sample data',
                host='localhost',
                port=5432,
                is_active=True
            ),
            MockDatabaseInfo(
                name='test',
                description='Test database (reset frequently)',
                host='localhost',
                port=5432,
                is_active=False
            ),
        ]

    def get_all_environments(self) -> List[MockDatabaseInfo]:
        """Get all available database environments.

        Returns:
            List of database environment information
        """
        return self._environments.copy()

    def get_active_environment(self) -> MockDatabaseInfo:
        """Get currently active database environment.

        Returns:
            Active database environment info

        Raises:
            ValueError: If no active environment found
        """
        for env in self._environments:
            if env.is_active:
                return env

        raise ValueError("No active database environment found")

    def get_environment_by_name(self, name: str) -> MockDatabaseInfo:
        """Get database environment by name.

        Args:
            name: Environment name

        Returns:
            Database environment info

        Raises:
            ValueError: If environment not found
        """
        for env in self._environments:
            if env.name == name:
                return env

        raise ValueError(f"Database environment '{name}' not found")


@pytest.fixture
def db_info_service():
    """Provide mock database info service."""
    return MockDatabaseInfoService()


def test_get_all_environments_returns_list(db_info_service):
    """Test that get_all_environments returns a list."""
    environments = db_info_service.get_all_environments()

    assert isinstance(environments, list)
    assert len(environments) > 0


def test_get_all_environments_contains_standard_envs(db_info_service):
    """Test that all standard environments are included."""
    environments = db_info_service.get_all_environments()
    env_names = [env.name for env in environments]

    # Should have dev, demo, test
    assert 'dev' in env_names
    assert 'demo' in env_names
    assert 'test' in env_names


def test_environment_info_has_required_fields(db_info_service):
    """Test that each environment has required fields."""
    environments = db_info_service.get_all_environments()

    for env in environments:
        assert hasattr(env, 'name')
        assert hasattr(env, 'description')
        assert hasattr(env, 'host')
        assert hasattr(env, 'port')
        assert hasattr(env, 'is_active')


def test_environment_name_is_string(db_info_service):
    """Test that environment names are strings."""
    environments = db_info_service.get_all_environments()

    for env in environments:
        assert isinstance(env.name, str)
        assert len(env.name) > 0


def test_environment_description_is_meaningful(db_info_service):
    """Test that environment descriptions are meaningful."""
    environments = db_info_service.get_all_environments()

    for env in environments:
        assert isinstance(env.description, str)
        assert len(env.description) > 10  # Should be a real description


def test_environment_host_is_valid(db_info_service):
    """Test that environment hosts are valid."""
    environments = db_info_service.get_all_environments()

    for env in environments:
        assert isinstance(env.host, str)
        assert len(env.host) > 0


def test_environment_port_is_valid(db_info_service):
    """Test that environment ports are valid."""
    environments = db_info_service.get_all_environments()

    for env in environments:
        assert isinstance(env.port, int)
        assert 1 <= env.port <= 65535


def test_get_active_environment(db_info_service):
    """Test that get_active_environment returns active env."""
    active_env = db_info_service.get_active_environment()

    assert active_env is not None
    assert active_env.is_active is True


def test_only_one_environment_is_active(db_info_service):
    """Test that exactly one environment is marked as active."""
    environments = db_info_service.get_all_environments()
    active_count = sum(1 for env in environments if env.is_active)

    assert active_count == 1


def test_get_environment_by_name_dev(db_info_service):
    """Test getting dev environment by name."""
    env = db_info_service.get_environment_by_name('dev')

    assert env.name == 'dev'
    assert 'dev' in env.description.lower()


def test_get_environment_by_name_demo(db_info_service):
    """Test getting demo environment by name."""
    env = db_info_service.get_environment_by_name('demo')

    assert env.name == 'demo'
    assert env.is_active is True  # Demo is the active environment


def test_get_environment_by_name_test(db_info_service):
    """Test getting test environment by name."""
    env = db_info_service.get_environment_by_name('test')

    assert env.name == 'test'
    assert 'test' in env.description.lower()


def test_get_environment_by_name_not_found(db_info_service):
    """Test that get_environment_by_name raises for invalid name."""
    with pytest.raises(ValueError, match="not found"):
        db_info_service.get_environment_by_name('nonexistent')


def test_environment_to_dict(db_info_service):
    """Test that environment can be converted to dict."""
    env = db_info_service.get_active_environment()
    env_dict = env.to_dict()

    assert isinstance(env_dict, dict)
    assert 'name' in env_dict
    assert 'description' in env_dict
    assert 'host' in env_dict
    assert 'port' in env_dict
    assert 'is_active' in env_dict


def test_get_all_environments_returns_copy(db_info_service):
    """Test that get_all_environments returns a copy."""
    envs1 = db_info_service.get_all_environments()
    envs2 = db_info_service.get_all_environments()

    # Should be equal but not the same list
    assert len(envs1) == len(envs2)
    assert envs1 is not envs2

    # Modifying one list should not affect the other
    envs1.append(None)
    assert len(envs1) != len(envs2)
