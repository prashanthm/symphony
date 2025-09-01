#!/usr/bin/env python3
"""
Symphony Environment Configuration Loader
Centralized environment variable management for all Symphony components
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class SymphonyEnvLoader:
    """Centralized environment configuration loader for Symphony"""

    def __init__(self):
        self.symphony_root = self._find_symphony_root()
        self.env_file = self.symphony_root / ".env"
        self._load_env_file()

    def _find_symphony_root(self) -> Path:
        """Find the Symphony root directory by looking for specific marker files"""
        current = Path(__file__).parent

        # Look for symphony root markers - updated for monorepo structure
        while current.parent != current:  # Stop at filesystem root
            # Look for monorepo markers
            if (current / "pyproject.toml").exists() and (current / "libs").exists():
                return current
            if (current / "apps" / "symphony-cli").exists():
                return current
            # Legacy markers for backward compatibility
            if (current / "tools" / "symphony").exists():
                return current
            current = current.parent

        # Fallback: assume we're in libs/symphony-core and go up to root
        if "libs/symphony-core" in str(Path(__file__)):
            return Path(__file__).parent.parent.parent.parent.parent

        return Path(__file__).parent.parent.parent

    def _load_env_file(self):
        """Load environment variables from .env file if it exists"""
        if self.env_file.exists():
            try:
                with open(self.env_file, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            # Only set if not already in environment
                            if key not in os.environ:
                                os.environ[key] = value

                logger.info(f"Loaded environment from {self.env_file}")
            except Exception as e:
                logger.warning(f"Failed to load .env file: {e}")
        else:
            logger.info(f"No .env file found at {self.env_file}")

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get environment variable with fallback to default"""
        return os.getenv(key, default)

    def require(self, key: str) -> str:
        """Get required environment variable, raise error if not found"""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} is not set")
        return value

    def get_linear_token(self) -> str:
        """Get Linear API token with helpful error message"""
        token = self.get("LINEAR_API_TOKEN")
        if not token:
            raise ValueError(
                f"LINEAR_API_TOKEN is required. Please:\n"
                f"1. Copy {self.symphony_root}/.env.example to {self.symphony_root}/.env\n"
                f"2. Set your Linear API token in the .env file\n"
                f"3. Or set LINEAR_API_TOKEN environment variable"
            )
        return token

    def get_github_token(self) -> str:
        """Get GitHub API token with helpful error message"""
        token = self.get("GITHUB_TOKEN")
        if not token:
            raise ValueError(
                f"GITHUB_TOKEN is required. Please:\n"
                f"1. Copy {self.symphony_root}/.env.example to {self.symphony_root}/.env\n"
                f"2. Set your GitHub API token in the .env file\n"
                f"3. Or set GITHUB_TOKEN environment variable"
            )
        return token

    def get_all_tool_tokens(self) -> Dict[str, str]:
        """Get all available tool API tokens"""
        tools = {
            "linear": self.get("LINEAR_API_TOKEN"),
            "github": self.get("GITHUB_TOKEN"),
            "hubspot": self.get("HUBSPOT_API_KEY"),
            "slack": self.get("SLACK_BOT_TOKEN"),
            "stripe": self.get("STRIPE_API_KEY"),
            "notion": self.get("NOTION_API_TOKEN"),
            "zoom_client_id": self.get("ZOOM_CLIENT_ID"),
            "zoom_client_secret": self.get("ZOOM_CLIENT_SECRET"),
            "quickbooks_client_id": self.get("QUICKBOOKS_CLIENT_ID"),
            "quickbooks_client_secret": self.get("QUICKBOOKS_CLIENT_SECRET"),
        }

        # Filter out None values
        return {k: v for k, v in tools.items() if v is not None}

    def validate_required_tools(self, required_tools: list) -> Dict[str, bool]:
        """Validate that required tools have their API tokens configured"""
        validation = {}
        all_tokens = self.get_all_tool_tokens()

        for tool in required_tools:
            validation[tool] = tool in all_tokens and bool(all_tokens[tool])

        return validation

    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary for debugging"""
        return {
            "symphony_root": str(self.symphony_root),
            "env_file_exists": self.env_file.exists(),
            "env_file_path": str(self.env_file),
            "environment": self.get("SYMPHONY_ENV", "development"),
            "log_level": self.get("LOG_LEVEL", "INFO"),
            "debug": self.get("DEBUG", "false").lower() == "true",
            "configured_tools": list(self.get_all_tool_tokens().keys()),
        }


# Global instance
_env_loader = None


def get_env_loader() -> SymphonyEnvLoader:
    """Get global environment loader instance"""
    global _env_loader
    if _env_loader is None:
        _env_loader = SymphonyEnvLoader()
    return _env_loader


def get_linear_token() -> str:
    """Convenience function to get Linear token"""
    return get_env_loader().get_linear_token()


def get_github_token() -> str:
    """Convenience function to get GitHub token"""
    return get_env_loader().get_github_token()


def get_tool_tokens() -> Dict[str, str]:
    """Convenience function to get all tool tokens"""
    return get_env_loader().get_all_tool_tokens()


def load_environment() -> SymphonyEnvLoader:
    """Load environment configuration and return loader instance"""
    return get_env_loader()


def validate_setup() -> bool:
    """Validate that the basic setup is working"""
    try:
        env_loader = get_env_loader()
        summary = env_loader.get_config_summary()

        print("🔧 Symphony Environment Configuration:")
        print(f"  📁 Root: {summary['symphony_root']}")
        print(
            f"  📄 .env file: {'✅ Found' if summary['env_file_exists'] else '❌ Not found'}"
        )
        print(f"  🌍 Environment: {summary['environment']}")
        print(f"  📊 Log level: {summary['log_level']}")
        print(f"  🔧 Debug: {summary['debug']}")
        print(f"  🔗 Configured tools: {len(summary['configured_tools'])}")

        for tool in summary["configured_tools"]:
            print(f"    • {tool}")

        return True

    except Exception as e:
        print(f"❌ Environment validation failed: {e}")
        return False


if __name__ == "__main__":
    validate_setup()
