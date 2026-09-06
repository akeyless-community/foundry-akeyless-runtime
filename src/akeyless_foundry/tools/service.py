"""Shared secret tool logic for MCP deployments on Foundry Hosted Agents."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Literal

from akeyless_foundry.client import (
    AkeylessRuntimeClient,
    DynamicSecretOptions,
    GetSecretOptions,
    RotatedSecretOptions,
)

SecretType = Literal["static", "dynamic", "rotated"]


@dataclass
class ToolResponse:
    ok: bool
    data: dict[str, Any]
    error: str | None = None

    def to_json(self) -> str:
        payload = {"ok": self.ok, **self.data}
        if self.error:
            payload["error"] = self.error
        return json.dumps(payload)


class SecretToolService:
    """Implements secret operations exposed as Foundry agent tools."""

    def __init__(self, client: AkeylessRuntimeClient | None = None) -> None:
        self._client = client or AkeylessRuntimeClient()

    @property
    def client(self) -> AkeylessRuntimeClient:
        return self._client

    def list_secrets(self, prefix: str | None = None) -> ToolResponse:
        """List secret names under a prefix. Never returns secret values."""
        try:
            names = self._client.list_secrets(prefix=prefix)
            return ToolResponse(
                ok=True,
                data={
                    "secrets": names,
                    "count": len(names),
                    "prefix": prefix or self._client.config.secret_prefix,
                },
            )
        except Exception as exc:
            return ToolResponse(ok=False, data={}, error=str(exc))

    def get_secret(
        self,
        name: str,
        *,
        path: str | None = None,
        secret_type: SecretType = "static",
        json_key: str | None = None,
        ignore_cache: bool = False,
    ) -> ToolResponse:
        """Fetch a secret value. Use json_key to return a single field from JSON secrets."""
        try:
            raw = self._fetch_by_type(
                name=name,
                path=path,
                secret_type=secret_type,
                ignore_cache=ignore_cache,
            )
            if json_key:
                value = self._extract_json_key(raw, json_key)
                return ToolResponse(
                    ok=True,
                    data={
                        "name": name,
                        "path": path or self._client.resolve_path(name),
                        "json_key": json_key,
                        "value": value,
                        "secret_type": secret_type,
                    },
                )

            return ToolResponse(
                ok=True,
                data={
                    "name": name,
                    "path": path or self._client.resolve_path(name),
                    "value": raw,
                    "secret_type": secret_type,
                },
            )
        except Exception as exc:
            return ToolResponse(ok=False, data={"name": name}, error=str(exc))

    def _fetch_by_type(
        self,
        *,
        name: str,
        path: str | None,
        secret_type: SecretType,
        ignore_cache: bool,
    ) -> str:
        if secret_type == "dynamic":
            return self._client.get_dynamic_secret(
                name,
                DynamicSecretOptions(path=path, ignore_cache=ignore_cache),
            )
        if secret_type == "rotated":
            return self._client.get_rotated_secret(
                name,
                RotatedSecretOptions(path=path, ignore_cache=ignore_cache),
            )

        return self._client.get_secret(
            name,
            GetSecretOptions(
                path=path,
                ignore_cache=ignore_cache,
                allow_dynamic_fallback=True,
            ),
        )

    @staticmethod
    def _extract_json_key(raw: str, json_key: str) -> str:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Secret is not valid JSON; cannot extract key {json_key!r}") from exc
        if not isinstance(data, dict):
            raise ValueError("Secret JSON must be an object to extract a key")
        if json_key not in data:
            raise ValueError(f"Key {json_key!r} not found in secret JSON")
        return stringify_value(data[json_key])


def stringify_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    return json.dumps(value)
