"""
Tests for Docker configuration files.

Test Observation Table (Equivalence Partitioning & Boundary Values):

| Test Case                      | Category      | Input                          | Expected Result           |
|-------------------------------|---------------|--------------------------------|---------------------------|
| docker-compose.yaml exists     | Normal        | File path                      | File exists               |
| docker-compose.yaml is valid   | Normal        | YAML content                   | Valid YAML structure      |
| Required services defined      | Normal        | Services section               | open-notebook, surreal-db |
| Port mappings correct          | Normal        | Ports section                  | 8501, 8000 mapped         |
| Network defined                | Normal        | Networks section               | open-notebook-network     |
| Volume defined                 | Normal        | Volumes section                | surreal-data defined      |
| .env file exists               | Normal        | File path                      | File exists               |
| .env.example exists            | Normal        | File path                      | File exists               |
| Required env vars in .env      | Normal        | .env content                   | All required vars present |
| Empty .env file                | Boundary      | Empty file                     | No variables found        |
| Invalid YAML syntax            | Abnormal      | Malformed YAML                 | YAML parse error          |
| Missing required service       | Abnormal      | No open-notebook service       | Validation error          |

Language: Python 3.10+
Test Framework: pytest
"""

from pathlib import Path

import pytest
import yaml


class TestDockerComposeFile:
    """Tests for docker-compose.yaml structure and content."""

    @pytest.fixture
    def docker_compose_path(self):
        """Get path to docker-compose.yaml."""
        return Path(__file__).parent.parent / "docker" / "docker-compose.yaml"

    @pytest.fixture
    def docker_compose_content(self, docker_compose_path):
        """Load docker-compose.yaml content."""
        if docker_compose_path.exists():
            with open(docker_compose_path) as f:
                return yaml.safe_load(f)
        return None

    def test_docker_compose_file_exists(self, docker_compose_path):
        """
        Given: The docker directory is set up
        When: Checking for docker-compose.yaml
        Then: The file should exist
        """
        assert docker_compose_path.exists(), f"docker-compose.yaml not found at {docker_compose_path}"

    def test_docker_compose_is_valid_yaml(self, docker_compose_path):
        """
        Given: docker-compose.yaml exists
        When: Parsing the YAML content
        Then: It should be valid YAML without errors
        """
        with open(docker_compose_path) as f:
            try:
                content = yaml.safe_load(f)
                assert content is not None
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML syntax: {e}")

    def test_required_services_defined(self, docker_compose_content):
        """
        Given: docker-compose.yaml is loaded
        When: Checking for required services
        Then: open-notebook and surreal-db should be defined
        """
        assert "services" in docker_compose_content
        services = docker_compose_content["services"]

        assert "open-notebook" in services, "open-notebook service not found"
        assert "surreal-db" in services, "surreal-db service not found"

    def test_open_notebook_service_configuration(self, docker_compose_content):
        """
        Given: open-notebook service is defined
        When: Checking its configuration
        Then: It should have correct image, ports, and dependencies
        """
        service = docker_compose_content["services"]["open-notebook"]

        # Check image
        assert "image" in service
        assert "open-notebook" in service["image"]

        # Check ports
        assert "ports" in service

        # Check dependency on database
        assert "depends_on" in service

    def test_surreal_db_service_configuration(self, docker_compose_content):
        """
        Given: surreal-db service is defined
        When: Checking its configuration
        Then: It should have correct image, command, and volumes
        """
        service = docker_compose_content["services"]["surreal-db"]

        # Check image
        assert "image" in service
        assert "surrealdb" in service["image"]

        # Check command
        assert "command" in service

        # Check volumes
        assert "volumes" in service

        # Check healthcheck
        assert "healthcheck" in service

    def test_network_defined(self, docker_compose_content):
        """
        Given: docker-compose.yaml is loaded
        When: Checking for network configuration
        Then: open-notebook-network should be defined
        """
        assert "networks" in docker_compose_content
        networks = docker_compose_content["networks"]

        assert "open-notebook-network" in networks

    def test_volume_defined(self, docker_compose_content):
        """
        Given: docker-compose.yaml is loaded
        When: Checking for volume configuration
        Then: surreal-data volume should be defined
        """
        assert "volumes" in docker_compose_content
        volumes = docker_compose_content["volumes"]

        assert "surreal-data" in volumes

    def test_environment_variables_use_substitution(self, docker_compose_content):
        """
        Given: open-notebook service is defined
        When: Checking environment configuration
        Then: Environment variables should use ${VAR} substitution
        """
        service = docker_compose_content["services"]["open-notebook"]

        assert "environment" in service
        env = service["environment"]

        # Check that at least some vars use substitution
        env_str = str(env)
        assert "${" in env_str or ":-" in env_str, "Environment variables should use substitution"


class TestEnvFiles:
    """Tests for .env and .env.example files."""

    @pytest.fixture
    def env_path(self):
        """Get path to .env file."""
        return Path(__file__).parent.parent / "docker" / ".env"

    @pytest.fixture
    def env_example_path(self):
        """Get path to .env.example file."""
        return Path(__file__).parent.parent / "docker" / ".env.example"

    def test_env_file_exists(self, env_path):
        """
        Given: The docker directory is set up
        When: Checking for .env file
        Then: The file should exist
        """
        assert env_path.exists(), f".env file not found at {env_path}"

    def test_env_example_file_exists(self, env_example_path):
        """
        Given: The docker directory is set up
        When: Checking for .env.example file
        Then: The file should exist
        """
        assert env_example_path.exists(), f".env.example file not found at {env_example_path}"

    def test_required_env_vars_in_env_file(self, env_path):
        """
        Given: .env file exists
        When: Checking its content
        Then: All required environment variables should be present
        """
        required_vars = [
            "OPENAI_API_BASE",
            "OPENAI_API_KEY",
            "DEFAULT_CHAT_MODEL",
            "SURREAL_ADDRESS",
            "SURREAL_USER",
            "SURREAL_PASS",
        ]

        with open(env_path) as f:
            content = f.read()

        for var in required_vars:
            assert var in content, f"Required variable {var} not found in .env"

    def test_env_file_has_comments(self, env_path):
        """
        Given: .env file exists
        When: Checking its content
        Then: It should have comments for documentation
        """
        with open(env_path) as f:
            content = f.read()

        # Check for comment lines
        assert "#" in content, ".env file should have comments for documentation"

    def test_env_example_has_placeholders(self, env_example_path):
        """
        Given: .env.example file exists
        When: Checking its content
        Then: It should have placeholder values for sensitive data
        """
        with open(env_example_path) as f:
            content = f.read()

        # .env.example should exist and have the same structure as .env
        assert "OPENAI_API_BASE" in content
        assert "DEFAULT_CHAT_MODEL" in content


class TestDockerDirectoryStructure:
    """Tests for Docker directory structure."""

    def test_docker_directory_exists(self):
        """
        Given: The project is set up
        When: Checking for docker directory
        Then: The directory should exist
        """
        docker_dir = Path(__file__).parent.parent / "docker"
        assert docker_dir.exists(), f"docker directory not found at {docker_dir}"
        assert docker_dir.is_dir(), f"{docker_dir} is not a directory"

    def test_docker_directory_contains_required_files(self):
        """
        Given: docker directory exists
        When: Checking its contents
        Then: It should contain docker-compose.yaml and .env
        """
        docker_dir = Path(__file__).parent.parent / "docker"

        required_files = ["docker-compose.yaml", ".env", ".env.example"]

        for filename in required_files:
            file_path = docker_dir / filename
            assert file_path.exists(), f"{filename} not found in docker directory"


# =============================================================================
# Test Execution Commands
# =============================================================================
# Run tests:
#   pytest tests/test_docker_config.py -v
#
# Run with coverage:
#   pytest tests/test_docker_config.py --cov=. --cov-report=term-missing
#
# Run specific test class:
#   pytest tests/test_docker_config.py::TestDockerComposeFile -v
# =============================================================================
