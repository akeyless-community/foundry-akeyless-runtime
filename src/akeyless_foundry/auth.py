"""Authenticate to Akeyless using cloud identity or other configured methods."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone

import akeyless
from akeyless_cloud_id import CloudId

from akeyless_foundry.config import AkeylessRuntimeConfig

ACCESS_KEY_DEFAULT_TTL_SECONDS = 14 * 60
ENV_TOKEN_TTL_SECONDS = 50 * 60


@dataclass
class AuthSession:
    token: str
    expires_at: float


def _expiry_from_auth_output(auth_out: akeyless.AuthOutput, margin_seconds: float) -> float:
    now = time.monotonic()
    expiration = getattr(auth_out, "expiration", None)
    if not expiration:
        return now + ACCESS_KEY_DEFAULT_TTL_SECONDS - margin_seconds

    raw = str(expiration).strip()
    if not raw:
        return now + ACCESS_KEY_DEFAULT_TTL_SECONDS - margin_seconds

    try:
        as_num = float(raw)
        if as_num > 1e12:
            return (as_num / 1000.0) - time.time() + now - margin_seconds
    except ValueError:
        pass

    try:
        as_date = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if as_date.tzinfo is None:
            as_date = as_date.replace(tzinfo=timezone.utc)
        return as_date.timestamp() - time.time() + now - margin_seconds
    except ValueError:
        pass

    return now + ACCESS_KEY_DEFAULT_TTL_SECONDS - margin_seconds


def _get_cloud_id(config: AkeylessRuntimeConfig) -> str:
    if config.cloud_id and config.cloud_id.strip():
        return config.cloud_id.strip()

    provider = config.cloud_provider or config.access_type
    if provider not in ("aws_iam", "azure_ad", "gcp"):
        raise ValueError(f"Cannot generate cloud ID for access type {provider}")

    cloud_id = CloudId().generate()
    if not cloud_id or not str(cloud_id).strip():
        raise ValueError(
            f"akeyless-cloud-id returned an empty cloud ID for provider {provider!r}. "
            "On Foundry Hosted Agents, ensure the agent Entra identity is available "
            "(IMDS / DefaultAzureCredential) or pass cloud_id explicitly."
        )
    return str(cloud_id).strip()


def _sdk_host(gateway_url: str) -> str:
    host = gateway_url.rstrip("/")
    if host.endswith("/api/v2"):
        if "api.akeyless.io" in host:
            return host[: -len("/api/v2")]
        return host
    if host.endswith("/v2"):
        return host
    if "api.akeyless.io" in host:
        return host
    return f"{host}/api/v2"


def create_v2_api(gateway_url: str) -> akeyless.V2Api:
    configuration = akeyless.Configuration(host=_sdk_host(gateway_url))
    return akeyless.V2Api(akeyless.ApiClient(configuration))


def authenticate(api: akeyless.V2Api, config: AkeylessRuntimeConfig) -> AuthSession:
    now = time.monotonic()

    if config.token and config.token.strip():
        return AuthSession(
            token=config.token.strip(),
            expires_at=now + ENV_TOKEN_TTL_SECONDS,
        )

    access_type = config.access_type

    if access_type in ("access_key", "api_key"):
        body = akeyless.Auth(
            access_id=config.access_id,
            access_type=access_type,
            access_key=config.access_key,
        )
    elif access_type == "universal_identity":
        body = akeyless.Auth(
            access_type="universal_identity",
            uid_token=config.uid_token,
        )
    elif access_type == "jwt":
        body = akeyless.Auth(
            access_id=config.access_id,
            access_type="jwt",
            jwt=config.jwt,
        )
    elif access_type in ("aws_iam", "azure_ad", "gcp"):
        body = akeyless.Auth(
            access_id=config.access_id,
            access_type=access_type,
            cloud_id=_get_cloud_id(config),
        )
    else:
        raise ValueError(f"Unsupported access type: {access_type}")

    auth_out = api.auth(body)
    token = getattr(auth_out, "token", None)
    if not token or not str(token).strip():
        raise ValueError("Akeyless authentication did not return a token")

    return AuthSession(
        token=str(token).strip(),
        expires_at=_expiry_from_auth_output(auth_out, config.token_expiry_margin_seconds),
    )
