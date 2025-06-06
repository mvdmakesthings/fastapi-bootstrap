"""
Configuration utilities for the FastAPI Bootstrap CLI.
"""

from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class Config:
    """Configuration manager for FastAPI Bootstrap."""

    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize the configuration manager.

        Args:
            config_file: Path to the configuration file
        """
        self.config_file = (
            config_file or Path.home() / ".fastapi-bootstrap" / "config.yaml"
        )
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file.

        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        if not self.config_file.exists():
            return {}

        try:
            with open(self.config_file, "r") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return {}

    def save_config(self) -> bool:
        """
        Save configuration to file.

        Returns:
            bool: True if saved successfully, False otherwise
        """
        # Ensure directory exists
        self.config_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(self.config_file, "w") as f:
                yaml.dump(self.config, f, default_flow_style=False)
            return True
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.

        Args:
            key: Configuration key (supports dot notation for nested keys)
            default: Default value if key doesn't exist

        Returns:
            Any: Configuration value
        """
        parts = key.split(".")
        value = self.config

        for part in parts:
            if not isinstance(value, dict) or part not in value:
                return default
            value = value[part]

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value.

        Args:
            key: Configuration key (supports dot notation for nested keys)
            value: Configuration value
        """
        parts = key.split(".")
        config = self.config

        for i, part in enumerate(parts[:-1]):
            if part not in config or not isinstance(config[part], dict):
                config[part] = {}
            config = config[part]

        config[parts[-1]] = value

    def delete(self, key: str) -> bool:
        """
        Delete configuration value.

        Args:
            key: Configuration key (supports dot notation for nested keys)

        Returns:
            bool: True if deleted successfully, False otherwise
        """
        parts = key.split(".")
        config = self.config

        for i, part in enumerate(parts[:-1]):
            if not isinstance(config, dict) or part not in config:
                return False
            config = config[part]

        if parts[-1] in config:
            del config[parts[-1]]
            return True

        return False
