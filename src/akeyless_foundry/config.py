"""Configuration from environment variables and explicit overrides."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

from akeyless_foundry.paths import default_foundry_secret_prefix

AccessType = Literal[
    "access_key",
    "api_key",
    "aws_iam",
    "azure_ad",
    "gcp",
    "universal_identity",
    "jwt",
]
CloudProvider = Literal["aws_iam", "azure_ad", "gcp"]

DEFAULT_GATEWAY = "https://api.akeyless.io"
DEFAULT_SECRET_CACHE_TTL_SECONDS = 5 * 60
DEFAULT_TOKEN_EXPIRY_MARGIN_SECONDS = 60


def _read_env(name: str) -> str | None:
    value = os.environ.get(name)
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


def _parse_positive_float(raw: str | None, fallback: float) -> float:
    if raw is None:
        return fallback
    try:
        parsed = float(raw)
    except ValueError:
        return fallback
    return parsed if parsed >= 0 else fallback


def _parse_access_type(raw: str | None) -> AccessType:
    value = (raw or "azure_ad").lower()
    allowed: tuple[AccessType, ...] = (
        "access_key",
        "api_key",
        "aws_iam",
        "azure_ad",
        "gcp",
        "universal_identity",
        "jwt",
    )
    if value not in allowed:
        raise ValueError(
            f'Unsupported AKEYLESS_ACCESS_TYPE "{raw}". '
            "Expected access_key, api_key, aws_iam, azure_ad, gcp, universal_identity, or jwt."
        )
    return value  # type: ignore[return-value]


def _cloud_provider_for_access_type(access_type: AccessType) -> CloudProvider | None:
    if access_type in ("aws_iam", "azure_ad", "gcp"):
        return access_type
    return None


@dataclass
class AkeylessRuntimeConfig:
    gateway_url: str = DEFAULT_GATEWAY
    secret_prefix: str = "/"
    access_type: AccessType = "azure_ad"
    access_id: str | None = None
    access_key: str | None = None
    uid_token: str | None = None
    jwt: str | None = None
    token: str | None = None
    cloud_id: str | None = None
    cloud_provider: CloudProvider | None = None
    secret_cache_ttl_seconds: float = DEFAULT_SECRET_CACHE_TTL_SECONDS
    token_expiry_margin_seconds: float = DEFAULT_TOKEN_EXPIRY_MARGIN_SECONDS


def config_from_env(**overrides: object) -> AkeylessRuntimeConfig:
    access_type = overrides.get("access_type") or _parse_access_type(
        _read_env("AKEYLESS_ACCESS_TYPE")
    )

    secret_prefix = overrides.get("secret_prefix")
    if secret_prefix is None:
        secret_prefix = _read_env("AKEYLESS_SECRET_PREFIX") or default_foundry_secret_prefix() or "/"

    cloud_provider = overrides.get("cloud_provider")
    if cloud_provider is None:
        cloud_provider = _cloud_provider_for_access_type(access_type)

    return AkeylessRuntimeConfig(
        gateway_url=overrides.get("gateway_url")
        or _read_env("AKEYLESS_GATEWAY_URL")
        or DEFAULT_GATEWAY,
        secret_prefix=str(secret_prefix),
        access_type=access_type,  # type: ignore[arg-type]
        access_id=overrides.get("access_id") or _read_env("AKEYLESS_ACCESS_ID"),
        access_key=overrides.get("access_key")
        or _read_env("AKEYLESS_ACCESS_KEY")
        or _read_env("AKEYLESS_API_KEY"),
        uid_token=overrides.get("uid_token")
        or _read_env("AKEYLESS_UID_TOKEN")
        or _read_env("AKEYLESS_UNIVERSAL_IDENTITY_TOKEN"),
        jwt=overrides.get("jwt") or _read_env("AKEYLESS_JWT"),
        token=overrides.get("token") or _read_env("AKEYLESS_TOKEN"),
        cloud_id=overrides.get("cloud_id") or _read_env("AKEYLESS_CLOUD_ID"),
        cloud_provider=cloud_provider,  # type: ignore[arg-type]
        secret_cache_ttl_seconds=overrides.get("secret_cache_ttl_seconds")
        or _parse_positive_float(
            _read_env("AKEYLESS_SECRET_CACHE_TTL_SECONDS"),
            DEFAULT_SECRET_CACHE_TTL_SECONDS,
        ),
        token_expiry_margin_seconds=overrides.get("token_expiry_margin_seconds")
        or _parse_positive_float(
            _read_env("AKEYLESS_TOKEN_EXPIRY_MARGIN_SECONDS"),
            DEFAULT_TOKEN_EXPIRY_MARGIN_SECONDS,
        ),
    )


def validate_config(config: AkeylessRuntimeConfig) -> None:
    if not config.gateway_url.strip():
        raise ValueError("gateway_url is required")

    if config.token and config.token.strip():
        return

    if config.access_type in ("access_key", "api_key"):
        if not config.access_id or not config.access_key:
            raise ValueError(
                "access_id and access_key are required for access_key/api_key authentication "
                "(or set token / AKEYLESS_TOKEN)"
            )
        return

    if config.access_type == "universal_identity":
        if not config.uid_token:
            raise ValueError(
                "uid_token is required for universal_identity authentication "
                "(or set token / AKEYLESS_TOKEN)"
            )
        return

    if config.access_type == "jwt":
        if not config.access_id or not config.jwt:
            raise ValueError(
                "access_id and jwt are required for jwt authentication "
                "(or set token / AKEYLESS_TOKEN)"
            )
        return

    if config.access_type in ("aws_iam", "azure_ad", "gcp"):
        if not config.access_id:
            raise ValueError(
                f"{config.access_type} authentication requires access_id "
                "(or set token / AKEYLESS_TOKEN)"
            )
        return

    raise ValueError(f"Unsupported access type: {config.access_type}")
