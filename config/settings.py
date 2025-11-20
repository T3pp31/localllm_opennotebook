"""
Centralized settings management for Open Notebook with vLLM.
All configuration is loaded from environment variables to avoid hardcoding.
"""

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


@dataclass
class Settings:
    """Application settings loaded from environment variables."""

    # Application Settings
    app_port: int
    log_level: str

    # SurrealDB Configuration
    surreal_address: str
    surreal_port: int
    surreal_user: str
    surreal_pass: str
    surreal_namespace: str
    surreal_database: str

    # vLLM / OpenAI Compatible API Configuration
    openai_api_base: str
    openai_api_key: str

    # Model Configuration
    default_chat_model: str
    default_transformation_model: str
    default_embedding_model: str

    @classmethod
    def from_env(cls, env_file: Optional[Path] = None) -> "Settings":
        """
        Load settings from environment variables.

        Args:
            env_file: Optional path to .env file. If not provided,
                     looks for .env in docker directory.

        Returns:
            Settings instance with loaded configuration.

        Raises:
            ValueError: If required environment variables are missing.
        """
        if env_file:
            load_dotenv(env_file)
        else:
            # Try to find .env in common locations
            possible_paths = [
                Path(__file__).parent.parent / "docker" / ".env",
                Path.cwd() / "docker" / ".env",
                Path.cwd() / ".env",
            ]
            for path in possible_paths:
                if path.exists():
                    load_dotenv(path)
                    break

        return cls(
            # Application Settings
            app_port=int(os.getenv("APP_PORT", "8501")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),

            # SurrealDB Configuration
            surreal_address=os.getenv("SURREAL_ADDRESS", "ws://surreal-db:8000"),
            surreal_port=int(os.getenv("SURREAL_PORT", "8000")),
            surreal_user=os.getenv("SURREAL_USER", "root"),
            surreal_pass=os.getenv("SURREAL_PASS", "root"),
            surreal_namespace=os.getenv("SURREAL_NAMESPACE", "open_notebook"),
            surreal_database=os.getenv("SURREAL_DATABASE", "open_notebook"),

            # vLLM / OpenAI Compatible API Configuration
            openai_api_base=os.getenv("OPENAI_API_BASE", "http://localhost:8000/v1"),
            openai_api_key=os.getenv("OPENAI_API_KEY", "dummy-key"),

            # Model Configuration
            default_chat_model=os.getenv("DEFAULT_CHAT_MODEL", "gpt-oss-20b"),
            default_transformation_model=os.getenv("DEFAULT_TRANSFORMATION_MODEL", "gpt-oss-20b"),
            default_embedding_model=os.getenv("DEFAULT_EMBEDDING_MODEL", "gpt-oss-20b"),
        )

    def validate(self) -> list[str]:
        """
        Validate that all required settings are properly configured.

        Returns:
            List of validation error messages. Empty list if all valid.
        """
        errors = []

        if not self.openai_api_base:
            errors.append("OPENAI_API_BASE is required")

        if not self.default_chat_model:
            errors.append("DEFAULT_CHAT_MODEL is required")

        if not self.surreal_address:
            errors.append("SURREAL_ADDRESS is required")

        return errors

    def get_openai_client_config(self) -> dict:
        """
        Get configuration dict for OpenAI client initialization.

        Returns:
            Dictionary with base_url and api_key for OpenAI client.
        """
        return {
            "base_url": self.openai_api_base,
            "api_key": self.openai_api_key,
        }


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Cached Settings instance loaded from environment.
    """
    return Settings.from_env()
