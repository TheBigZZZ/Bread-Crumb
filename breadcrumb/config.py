"""
Configuration management for Bread Crumb.
Handles API keys, provider preferences, and global settings.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """Manages user configuration in ~/.breadcrumb/config.json"""

    def __init__(self):
        self.app_dir = Path.home() / ".breadcrumb"
        self.config_file = self.app_dir / "config.json"
        self.app_dir.mkdir(exist_ok=True)
        self._config = self._load()

    def _load(self) -> Dict[str, Any]:
        """Load config from file or return defaults."""
        if self.config_file.exists():
            try:
                return json.loads(self.config_file.read_text())
            except Exception:
                return self._defaults()
        return self._defaults()

    def _defaults(self) -> Dict[str, Any]:
        """Default configuration."""
        return {
            "provider": "anthropic",
            "anthropic_key": "",
            "openai_key": "",
            "gemini_key": "",
            "ollama_url": "http://localhost:11434",
            "model_anthropic": "claude-3-5-sonnet-20241022",
            "model_openai": "gpt-4o",
            "model_gemini": "gemini-2.0-flash",
            "model_ollama": "llama2",
            "max_tokens": 200000,
            "temperature": 0.7,
        }

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self._config[key] = value
        self.save()

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)

    def save(self) -> None:
        """Save config to file."""
        self.config_file.write_text(json.dumps(self._config, indent=2))

    def get_api_key(self, provider: str) -> str:
        """Get API key for provider."""
        key_map = {
            "anthropic": "anthropic_key",
            "openai": "openai_key",
            "gemini": "gemini_key",
        }
        return self.get(key_map.get(provider, ""), "")

    def set_api_key(self, provider: str, key: str) -> None:
        """Set API key for provider."""
        key_map = {
            "anthropic": "anthropic_key",
            "openai": "openai_key",
            "gemini": "gemini_key",
        }
        self.set(key_map.get(provider, ""), key)

    def get_model(self, provider: Optional[str] = None) -> str:
        """Get model name for provider."""
        provider = provider or self.get("provider", "anthropic")
        model_key = f"model_{provider}"
        return self.get(model_key, "")

    def to_dict(self) -> Dict[str, Any]:
        """Return config as dictionary."""
        return self._config.copy()
