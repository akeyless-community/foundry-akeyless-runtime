import pytest

from akeyless_foundry.config import config_from_env, validate_config
from akeyless_foundry.paths import (
    default_foundry_secret_prefix,
    join_secret_path,
    normalize_path,
    pick_secret_from_response,
)


class TestPaths:
    def test_normalize_path(self):
        assert normalize_path("foo/bar") == "/foo/bar"
        assert normalize_path("/foo//bar/") == "/foo/bar"
        assert normalize_path("") == "/"

    def test_join_secret_path(self):
        assert join_secret_path("/foundry-agents/my-agent/production", "APP_SECRET") == (
            "/foundry-agents/my-agent/production/APP_SECRET"
        )

    def test_pick_secret_from_response(self):
        data = {"/my/secret": "value"}
        assert pick_secret_from_response("/my/secret", data) == "value"

    def test_default_prefix_from_env(self, monkeypatch):
        monkeypatch.setenv("FOUNDRY_AGENT_NAME", "logistics-agent")
        monkeypatch.setenv("AKEYLESS_ENV", "staging")
        assert default_foundry_secret_prefix() == "/foundry-agents/logistics-agent/staging"


class TestConfig:
    def test_defaults_to_azure_ad(self, monkeypatch):
        monkeypatch.delenv("AKEYLESS_ACCESS_TYPE", raising=False)
        monkeypatch.setenv("AKEYLESS_ACCESS_ID", "p-test")
        config = config_from_env()
        assert config.access_type == "azure_ad"
        validate_config(config)

    def test_access_key_requires_credentials(self, monkeypatch):
        monkeypatch.setenv("AKEYLESS_ACCESS_TYPE", "access_key")
        monkeypatch.delenv("AKEYLESS_ACCESS_ID", raising=False)
        monkeypatch.delenv("AKEYLESS_ACCESS_KEY", raising=False)
        config = config_from_env()
        with pytest.raises(ValueError, match="access_id and access_key"):
            validate_config(config)

    def test_secret_prefix_override(self, monkeypatch):
        monkeypatch.setenv("AKEYLESS_SECRET_PREFIX", "/custom/prefix")
        config = config_from_env()
        assert config.secret_prefix == "/custom/prefix"

    def test_gateway_url(self, monkeypatch):
        monkeypatch.setenv("AKEYLESS_GATEWAY_URL", "https://gateway.example.com")
        config = config_from_env()
        assert config.gateway_url == "https://gateway.example.com"
