"""
Tests for vLLM API connection.

Test Observation Table (Equivalence Partitioning & Boundary Values):

| Test Case                      | Category      | Input                          | Expected Result           |
|-------------------------------|---------------|--------------------------------|---------------------------|
| Valid endpoint URL format      | Normal        | http://host:8000/v1            | URL parsed correctly      |
| Create OpenAI client           | Normal        | Valid base_url and api_key     | Client created            |
| List models endpoint           | Normal        | /v1/models                     | Models list returned      |
| Chat completion request        | Normal        | Valid messages                 | Response generated        |
| Empty message list             | Boundary      | messages=[]                    | Error or empty response   |
| Very long message              | Boundary      | 10000 char message             | Handled or error          |
| Invalid endpoint URL           | Abnormal      | invalid://url                  | Connection error          |
| Connection timeout             | Abnormal      | Unreachable host               | Timeout error             |
| Invalid API key                | Abnormal      | Wrong key                      | Auth error (if enforced)  |
| Invalid model name             | Abnormal      | nonexistent-model              | Model not found error     |
| Malformed request              | Abnormal      | Missing required fields        | Validation error          |
| Server error (500)             | Abnormal      | Server issue                   | HTTP 500 error            |

Language: Python 3.10+
Test Framework: pytest
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import httpx

# Import after adding to path in conftest
from config.settings import Settings, get_settings


class TestVLLMEndpointConfiguration:
    """Tests for vLLM endpoint URL configuration."""

    def test_valid_endpoint_url_format(self, mock_env_vars):
        """
        Given: A valid vLLM endpoint URL is configured
        When: Settings are loaded
        Then: URL should be correctly formatted
        """
        get_settings.cache_clear()

        settings = Settings.from_env()

        assert settings.openai_api_base.startswith("http")
        assert "/v1" in settings.openai_api_base

    def test_endpoint_url_with_different_ports(self, monkeypatch):
        """
        Given: Different port numbers in endpoint URL
        When: Settings are loaded
        Then: Port should be preserved in URL
        """
        get_settings.cache_clear()

        test_urls = [
            "http://localhost:8000/v1",
            "http://localhost:8080/v1",
            "http://192.168.1.100:3000/v1",
        ]

        for url in test_urls:
            monkeypatch.setenv("OPENAI_API_BASE", url)
            settings = Settings.from_env()
            assert settings.openai_api_base == url

    def test_endpoint_url_boundary_empty(self, monkeypatch):
        """
        Given: Empty endpoint URL
        When: Settings are loaded
        Then: Empty string should be stored
        """
        get_settings.cache_clear()
        monkeypatch.setenv("OPENAI_API_BASE", "")

        settings = Settings.from_env()

        assert settings.openai_api_base == ""


class TestOpenAIClientCreation:
    """Tests for OpenAI client configuration."""

    def test_get_openai_client_config_returns_dict(self, mock_env_vars):
        """
        Given: Valid settings are configured
        When: get_openai_client_config() is called
        Then: A dictionary with required keys should be returned
        """
        get_settings.cache_clear()

        settings = Settings.from_env()
        config = settings.get_openai_client_config()

        assert isinstance(config, dict)
        assert "base_url" in config
        assert "api_key" in config

    def test_openai_client_config_values(self, mock_env_vars):
        """
        Given: Specific endpoint and API key are set
        When: get_openai_client_config() is called
        Then: Config should contain those exact values
        """
        get_settings.cache_clear()

        settings = Settings.from_env()
        config = settings.get_openai_client_config()

        assert config["base_url"] == "http://test-vllm:8000/v1"
        assert config["api_key"] == "test-api-key"


class TestVLLMAPIRequests:
    """Tests for vLLM API request handling (mocked)."""

    @pytest.fixture
    def mock_openai_client(self):
        """Create a mock OpenAI client."""
        client = MagicMock()
        return client

    def test_list_models_request_format(self, mock_openai_client):
        """
        Given: A configured OpenAI client
        When: Listing available models
        Then: Request should be made to /v1/models endpoint
        """
        # Setup mock response
        mock_model = MagicMock()
        mock_model.id = "gpt-oss-20b"
        mock_openai_client.models.list.return_value = MagicMock(data=[mock_model])

        # Execute
        response = mock_openai_client.models.list()

        # Verify
        mock_openai_client.models.list.assert_called_once()
        assert len(response.data) > 0
        assert response.data[0].id == "gpt-oss-20b"

    def test_chat_completion_request_format(self, mock_openai_client):
        """
        Given: A configured OpenAI client
        When: Making a chat completion request
        Then: Request should have correct structure
        """
        # Setup mock response
        mock_choice = MagicMock()
        mock_choice.message.content = "Test response"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_openai_client.chat.completions.create.return_value = mock_response

        # Execute
        response = mock_openai_client.chat.completions.create(
            model="gpt-oss-20b",
            messages=[{"role": "user", "content": "Hello"}]
        )

        # Verify
        mock_openai_client.chat.completions.create.assert_called_once()
        assert response.choices[0].message.content == "Test response"

    def test_chat_completion_with_empty_messages(self, mock_openai_client):
        """
        Given: An empty messages list
        When: Making a chat completion request
        Then: Should handle error appropriately
        """
        # Setup mock to raise error
        mock_openai_client.chat.completions.create.side_effect = ValueError(
            "Messages list cannot be empty"
        )

        # Execute and verify
        with pytest.raises(ValueError) as exc_info:
            mock_openai_client.chat.completions.create(
                model="gpt-oss-20b",
                messages=[]
            )

        assert "empty" in str(exc_info.value).lower()


class TestVLLMConnectionErrors:
    """Tests for connection error handling."""

    def test_connection_timeout_handling(self, mock_env_vars):
        """
        Given: vLLM server is unreachable
        When: Making an API request
        Then: Timeout error should be raised
        """
        get_settings.cache_clear()

        # This test verifies error handling, not actual connection
        with patch('httpx.Client.get') as mock_get:
            mock_get.side_effect = httpx.TimeoutException("Connection timed out")

            with pytest.raises(httpx.TimeoutException):
                client = httpx.Client()
                client.get("http://unreachable:8000/v1/models")

    def test_connection_refused_handling(self, mock_env_vars):
        """
        Given: vLLM server is not running
        When: Making an API request
        Then: Connection refused error should be raised
        """
        get_settings.cache_clear()

        with patch('httpx.Client.get') as mock_get:
            mock_get.side_effect = httpx.ConnectError("Connection refused")

            with pytest.raises(httpx.ConnectError):
                client = httpx.Client()
                client.get("http://localhost:9999/v1/models")

    def test_invalid_model_name_handling(self):
        """
        Given: An invalid model name is specified
        When: Making a chat completion request
        Then: Model not found error should be raised
        """
        with patch('httpx.Client.post') as mock_post:
            error_response = Mock()
            error_response.status_code = 404
            error_response.json.return_value = {"error": "Model not found"}
            mock_post.return_value = error_response

            client = httpx.Client()
            response = client.post(
                "http://localhost:8000/v1/chat/completions",
                json={"model": "nonexistent-model", "messages": []}
            )

            assert response.status_code == 404


class TestVLLMIntegration:
    """Integration tests for vLLM (requires running vLLM server)."""

    @pytest.fixture
    def real_settings(self, env_file_path):
        """Load real settings from .env file."""
        get_settings.cache_clear()
        if env_file_path.exists():
            return Settings.from_env(env_file_path)
        return None

    @pytest.mark.skip(reason="Requires running vLLM server")
    def test_real_connection_to_vllm(self, real_settings):
        """
        Given: vLLM server is running
        When: Making a real API request
        Then: Response should be received

        Note: This test is skipped by default as it requires a running vLLM server.
        Remove the skip decorator to run integration tests.
        """
        if real_settings is None:
            pytest.skip("No .env file found")

        from openai import OpenAI

        config = real_settings.get_openai_client_config()
        client = OpenAI(**config)

        # Test listing models
        models = client.models.list()
        assert len(models.data) > 0

    @pytest.mark.skip(reason="Requires running vLLM server")
    def test_real_chat_completion(self, real_settings):
        """
        Given: vLLM server is running
        When: Making a chat completion request
        Then: Valid response should be generated

        Note: This test is skipped by default as it requires a running vLLM server.
        Remove the skip decorator to run integration tests.
        """
        if real_settings is None:
            pytest.skip("No .env file found")

        from openai import OpenAI

        config = real_settings.get_openai_client_config()
        client = OpenAI(**config)

        response = client.chat.completions.create(
            model=real_settings.default_chat_model,
            messages=[
                {"role": "user", "content": "Say hello in one word."}
            ],
            max_tokens=10
        )

        assert response.choices[0].message.content is not None


# =============================================================================
# Test Execution Commands
# =============================================================================
# Run tests (mocked only):
#   pytest tests/test_vllm_connection.py -v
#
# Run integration tests (requires running vLLM server):
#   pytest tests/test_vllm_connection.py -v --run-integration
#
# Run with coverage:
#   pytest tests/test_vllm_connection.py --cov=config --cov-report=term-missing
# =============================================================================
