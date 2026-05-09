"""
Test configuration management.
"""

import tempfile
from pathlib import Path
from breadcrumb.config import Config


def test_config_defaults():
    """Test that config has sensible defaults."""
    cfg = Config()
    assert cfg.get("provider") in ["anthropic", "openai", "gemini", "ollama"]
    assert cfg.get("temperature") == 0.7


def test_config_set_get():
    """Test setting and getting config values."""
    cfg = Config()
    cfg.set("test_key", "test_value")
    assert cfg.get("test_key") == "test_value"


def test_api_key_management():
    """Test API key get/set."""
    cfg = Config()
    cfg.set_api_key("anthropic", "sk-test-key")
    assert cfg.get_api_key("anthropic") == "sk-test-key"


def test_model_selection():
    """Test model selection."""
    cfg = Config()
    cfg.set("provider", "anthropic")
    model = cfg.get_model("anthropic")
    assert isinstance(model, str)
    assert len(model) > 0
