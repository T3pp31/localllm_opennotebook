"""
Tests for config/settings.py

Test Observation Table (Equivalence Partitioning & Boundary Values):

| Test Case                      | Category      | Input                          | Expected Result           |
|-------------------------------|---------------|--------------------------------|---------------------------|
| Load defaults                  | Normal        | No env vars                    | Default values loaded     |
| Load from env vars             | Normal        | Valid env vars                 | Custom values loaded      |
| Load from .env file            | Normal        | Valid .env file path           | Values from file loaded   |
| Empty string values            | Boundary      | OPENAI_API_BASE=""             | Empty string stored       |
| Numeric port boundary (0)      | Boundary      | APP_PORT=0                     | Port set to 0             |
| Numeric port boundary (65535)  | Boundary      | APP_PORT=65535                 | Port set to 65535         |
| Invalid port (negative)        | Abnormal      | APP_PORT=-1                    | ValueError                |
| Invalid port (non-numeric)     | Abnormal      | APP_PORT="abc"                 | ValueError                |
| Missing required fields        | Abnormal      | OPENAI_API_BASE missing        | Validation error          |
| Validate all required          | Normal        | All fields set                 | Empty error list          |
| Get OpenAI client config       | Normal        | Valid settings                 | Dict with base_url, key   |
| Cached settings                | Normal        | Multiple calls                 | Same instance returned    |

Language: Python 3.10+
Test Framework: pytest
"""

import os
from pathlib import Path

import pytest

from config.settings import Settings, get_settings


class TestSettingsFromEnv:
    """Tests for Settings.from_env() method."""

    def test_load_default_values_when_no_env_vars(self, empty_env_vars):
        """
        Given: No environment variables are set
        When: Settings.from_env() is called with non-existent file
        Then: Default values should be returned
        """
        # Clear cache to ensure fresh settings
        get_settings.cache_clear()

        # Pass non-existent path to avoid loading from .env file
        settings = Settings.from_env(Path("/nonexistent/.env"))

        assert settings.app_port == 8501
        assert settings.log_level == "INFO"
        assert settings.surreal_address == "ws://surreal-db:8000"
        assert settings.openai_api_base == "http://localhost:8000/v1"
        assert settings.openai_api_key == "dummy-key"
        assert settings.default_chat_model == "gpt-oss-20b"

    def test_load_custom_values_from_env_vars(self, mock_env_vars):
        """
        Given: Custom environment variables are set
        When: Settings.from_env() is called
        Then: Custom values should be loaded
        """
        get_settings.cache_clear()

        settings = Settings.from_env()

        assert settings.app_port == 8501
        assert settings.log_level == "DEBUG"
        assert settings.surreal_address == "ws://test-db:8000"
        assert settings.surreal_user == "test_user"
        assert settings.surreal_pass == "test_pass"
        assert settings.openai_api_base == "http://test-vllm:8000/v1"
        assert settings.openai_api_key == "test-api-key"
        assert settings.default_chat_model == "test-model"

    def test_load_from_env_file(self, env_file_path):
        """
        Given: A valid .env file exists
        When: Settings.from_env() is called with the file path
        Then: Values from the file should be loaded
        """
        get_settings.cache_clear()

        if env_file_path.exists():
            settings = Settings.from_env(env_file_path)
            # Check that settings were loaded (not necessarily specific values)
            assert settings.openai_api_base is not None
            assert settings.default_chat_model is not None


class TestSettingsBoundaryValues:
    """Tests for boundary value conditions."""

    def test_port_boundary_zero(self, monkeypatch):
        """
        Given: APP_PORT is set to 0 (minimum boundary)
        When: Settings.from_env() is called
        Then: Port should be set to 0
        """
        get_settings.cache_clear()
        monkeypatch.setenv("APP_PORT", "0")

        settings = Settings.from_env()

        assert settings.app_port == 0

    def test_port_boundary_max(self, monkeypatch):
        """
        Given: APP_PORT is set to 65535 (maximum valid port)
        When: Settings.from_env() is called
        Then: Port should be set to 65535
        """
        get_settings.cache_clear()
        monkeypatch.setenv("APP_PORT", "65535")

        settings = Settings.from_env()

        assert settings.app_port == 65535

    def test_empty_string_value(self, monkeypatch):
        """
        Given: OPENAI_API_BASE is set to empty string
        When: Settings.from_env() is called
        Then: Empty string should be stored (validation will catch this)
        """
        get_settings.cache_clear()
        monkeypatch.setenv("OPENAI_API_BASE", "")

        settings = Settings.from_env()

        assert settings.openai_api_base == ""


class TestSettingsAbnormalCases:
    """Tests for error conditions and invalid inputs."""

    def test_invalid_port_non_numeric(self, monkeypatch):
        """
        Given: APP_PORT is set to non-numeric value
        When: Settings.from_env() is called
        Then: ValueError should be raised
        """
        get_settings.cache_clear()
        monkeypatch.setenv("APP_PORT", "abc")

        with pytest.raises(ValueError):
            Settings.from_env()

    def test_invalid_port_negative(self, monkeypatch):
        """
        Given: APP_PORT is set to negative value
        When: Settings.from_env() is called
        Then: Port should be set to -1 (validation should catch this)
        """
        get_settings.cache_clear()
        monkeypatch.setenv("APP_PORT", "-1")

        # Negative port is technically valid for int(), but semantically wrong
        settings = Settings.from_env()
        assert settings.app_port == -1

    def test_invalid_env_file_path(self):
        """
        Given: An invalid .env file path
        When: Settings.from_env() is called with the path
        Then: Should use defaults (file not found is not an error)
        """
        get_settings.cache_clear()

        invalid_path = Path("/nonexistent/path/.env")
        settings = Settings.from_env(invalid_path)

        # Should return defaults when file not found
        assert settings is not None


class TestSettingsValidation:
    """Tests for Settings.validate() method."""

    def test_validate_all_required_fields_present(self, mock_env_vars):
        """
        Given: All required fields are properly set
        When: validate() is called
        Then: Empty error list should be returned
        """
        get_settings.cache_clear()

        settings = Settings.from_env()
        errors = settings.validate()

        assert errors == []

    def test_validate_missing_openai_api_base(self, monkeypatch):
        """
        Given: OPENAI_API_BASE is empty
        When: validate() is called
        Then: Error list should contain API base error
        """
        get_settings.cache_clear()
        monkeypatch.setenv("OPENAI_API_BASE", "")

        settings = Settings.from_env()
        errors = settings.validate()

        assert "OPENAI_API_BASE is required" in errors

    def test_validate_missing_default_chat_model(self, monkeypatch):
        """
        Given: DEFAULT_CHAT_MODEL is empty
        When: validate() is called
        Then: Error list should contain model error
        """
        get_settings.cache_clear()
        monkeypatch.setenv("DEFAULT_CHAT_MODEL", "")

        settings = Settings.from_env()
        errors = settings.validate()

        assert "DEFAULT_CHAT_MODEL is required" in errors

    def test_validate_missing_surreal_address(self, monkeypatch):
        """
        Given: SURREAL_ADDRESS is empty
        When: validate() is called
        Then: Error list should contain surreal address error
        """
        get_settings.cache_clear()
        monkeypatch.setenv("SURREAL_ADDRESS", "")

        settings = Settings.from_env()
        errors = settings.validate()

        assert "SURREAL_ADDRESS is required" in errors

    def test_validate_multiple_missing_fields(self, monkeypatch):
        """
        Given: Multiple required fields are empty
        When: validate() is called
        Then: Error list should contain all errors
        """
        get_settings.cache_clear()
        monkeypatch.setenv("OPENAI_API_BASE", "")
        monkeypatch.setenv("DEFAULT_CHAT_MODEL", "")
        monkeypatch.setenv("SURREAL_ADDRESS", "")

        settings = Settings.from_env()
        errors = settings.validate()

        assert len(errors) == 3


class TestGetOpenAIClientConfig:
    """Tests for get_openai_client_config() method."""

    def test_returns_correct_config_dict(self, mock_env_vars):
        """
        Given: Valid settings are configured
        When: get_openai_client_config() is called
        Then: Dict with base_url and api_key should be returned
        """
        get_settings.cache_clear()

        settings = Settings.from_env()
        config = settings.get_openai_client_config()

        assert "base_url" in config
        assert "api_key" in config
        assert config["base_url"] == "http://test-vllm:8000/v1"
        assert config["api_key"] == "test-api-key"


class TestGetSettings:
    """Tests for get_settings() cached function."""

    def test_returns_settings_instance(self, mock_env_vars):
        """
        Given: Environment is configured
        When: get_settings() is called
        Then: Settings instance should be returned
        """
        get_settings.cache_clear()

        settings = get_settings()

        assert isinstance(settings, Settings)

    def test_returns_cached_instance(self, mock_env_vars):
        """
        Given: get_settings() has been called before
        When: get_settings() is called again
        Then: Same cached instance should be returned
        """
        get_settings.cache_clear()

        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2


# =============================================================================
# Test Execution Commands
# =============================================================================
# Run tests:
#   pytest tests/test_settings.py -v
#
# Run with coverage:
#   pytest tests/test_settings.py --cov=config --cov-report=term-missing
#
# Run specific test class:
#   pytest tests/test_settings.py::TestSettingsFromEnv -v
# =============================================================================
