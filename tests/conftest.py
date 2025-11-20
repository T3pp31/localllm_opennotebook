"""Pytest configuration and fixtures."""

import os
import sys
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def env_file_path():
    """Get path to the test .env file."""
    return project_root / "docker" / ".env"


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables for testing."""
    env_vars = {
        "APP_PORT": "8501",
        "LOG_LEVEL": "DEBUG",
        "SURREAL_ADDRESS": "ws://test-db:8000",
        "SURREAL_PORT": "8000",
        "SURREAL_USER": "test_user",
        "SURREAL_PASS": "test_pass",
        "SURREAL_NAMESPACE": "test_namespace",
        "SURREAL_DATABASE": "test_database",
        "OPENAI_API_BASE": "http://test-vllm:8000/v1",
        "OPENAI_API_KEY": "test-api-key",
        "DEFAULT_CHAT_MODEL": "test-model",
        "DEFAULT_TRANSFORMATION_MODEL": "test-model",
        "DEFAULT_EMBEDDING_MODEL": "test-model",
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    return env_vars


@pytest.fixture
def empty_env_vars(monkeypatch):
    """Clear all relevant environment variables."""
    env_keys = [
        "APP_PORT", "LOG_LEVEL", "SURREAL_ADDRESS", "SURREAL_PORT",
        "SURREAL_USER", "SURREAL_PASS", "SURREAL_NAMESPACE", "SURREAL_DATABASE",
        "OPENAI_API_BASE", "OPENAI_API_KEY", "DEFAULT_CHAT_MODEL",
        "DEFAULT_TRANSFORMATION_MODEL", "DEFAULT_EMBEDDING_MODEL",
    ]
    for key in env_keys:
        monkeypatch.delenv(key, raising=False)
