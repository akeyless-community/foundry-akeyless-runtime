"""Client tests with a stub V2Api — no live Akeyless."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from akeyless_foundry.auth import AuthSession
from akeyless_foundry.client import AkeylessRuntimeClient, reset_default_client


def _client_with_stub_api(**overrides):
    api = MagicMock()
    with patch("akeyless_foundry.client.create_v2_api", return_value=api):
        with patch(
            "akeyless_foundry.client.authenticate",
            return_value=AuthSession(token="t", expires_at=1e18),
        ):
            client = AkeylessRuntimeClient(
                access_type="access_key",
                access_id="p-test",
                access_key="key",
                secret_prefix="/foundry-agents/demo/production",
                **overrides,
            )
    client._api = api
    return client


class TestAkeylessRuntimeClient:
    def test_get_secret_calls_sdk(self):
        client = _client_with_stub_api()
        client._api.get_secret_value.return_value = {
            "/foundry-agents/demo/production/APP_SECRET": "secret-value"
        }
        assert client.get_secret("APP_SECRET") == "secret-value"
        client._api.get_secret_value.assert_called_once()

    def test_get_dynamic_secret_calls_sdk(self):
        client = _client_with_stub_api()
        client._api.get_dynamic_secret_value.return_value = {"user": "tmp"}
        raw = client.get_dynamic_secret("azure-creds")
        assert "tmp" in raw
        client._api.get_dynamic_secret_value.assert_called_once()

    def test_get_rotated_secret_calls_sdk(self):
        client = _client_with_stub_api()
        client._api.get_rotated_secret_value.return_value = {"api_key": "rotated"}
        raw = client.get_rotated_secret("api-key")
        assert "rotated" in raw
        client._api.get_rotated_secret_value.assert_called_once()

    def test_list_secrets_returns_names_only(self):
        client = _client_with_stub_api()
        client._api.list_items.return_value = SimpleNamespace(
            items=[
                SimpleNamespace(item_name="/foundry-agents/demo/production/APP_SECRET"),
                {"item_name": "/foundry-agents/demo/production/DATABASE_URL"},
            ]
        )
        names = client.list_secrets()
        assert names == [
            "/foundry-agents/demo/production/APP_SECRET",
            "/foundry-agents/demo/production/DATABASE_URL",
        ]
        for name in names:
            assert "secret-value" not in name

    def test_resolve_short_name(self):
        client = _client_with_stub_api()
        assert client.resolve_path("APP_SECRET") == "/foundry-agents/demo/production/APP_SECRET"

    def test_reset_default_client(self):
        reset_default_client()
