"""Auth unit tests with a stub V2Api — no network."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from akeyless_foundry.auth import authenticate, create_v2_api, _sdk_host
from akeyless_foundry.config import AkeylessRuntimeConfig


class TestSdkHost:
    def test_saas_host_unchanged(self):
        assert _sdk_host("https://api.akeyless.io") == "https://api.akeyless.io"

    def test_gateway_appends_api_v2(self):
        assert _sdk_host("https://gw.example.com:8000") == "https://gw.example.com:8000/api/v2"

    def test_gateway_already_has_api_v2(self):
        assert _sdk_host("https://gw.example.com:8000/api/v2") == "https://gw.example.com:8000/api/v2"


class TestAuthenticate:
    def test_preauthenticated_token(self):
        api = MagicMock()
        config = AkeylessRuntimeConfig(token="sess-token")
        session = authenticate(api, config)
        assert session.token == "sess-token"
        api.auth.assert_not_called()

    def test_access_key(self):
        api = MagicMock()
        api.auth.return_value = SimpleNamespace(token="ak-session", expiration=None)
        config = AkeylessRuntimeConfig(
            access_type="access_key",
            access_id="p-test",
            access_key="key",
        )
        session = authenticate(api, config)
        assert session.token == "ak-session"
        api.auth.assert_called_once()

    def test_azure_ad_uses_cloud_id(self):
        api = MagicMock()
        api.auth.return_value = SimpleNamespace(token="azure-session", expiration=None)
        config = AkeylessRuntimeConfig(
            access_type="azure_ad",
            access_id="p-test",
            cloud_provider="azure_ad",
            cloud_id="azure-cloud-id-token",
        )
        session = authenticate(api, config)
        assert session.token == "azure-session"
        body = api.auth.call_args[0][0]
        assert body.access_type == "azure_ad"
        assert body.cloud_id == "azure-cloud-id-token"

    def test_azure_ad_empty_generated_cloud_id(self):
        api = MagicMock()
        config = AkeylessRuntimeConfig(
            access_type="azure_ad",
            access_id="p-test",
            cloud_provider="azure_ad",
        )
        with patch("akeyless_foundry.auth.CloudId") as cloud_id_cls:
            cloud_id_cls.return_value.generate.return_value = ""
            with pytest.raises(ValueError, match="empty cloud ID"):
                authenticate(api, config)

    def test_empty_auth_token(self):
        api = MagicMock()
        api.auth.return_value = SimpleNamespace(token="", expiration=None)
        config = AkeylessRuntimeConfig(
            access_type="access_key",
            access_id="p-test",
            access_key="key",
        )
        with pytest.raises(ValueError, match="did not return a token"):
            authenticate(api, config)


class TestCreateV2Api:
    def test_returns_v2_api(self):
        api = create_v2_api("https://api.akeyless.io")
        assert api is not None
