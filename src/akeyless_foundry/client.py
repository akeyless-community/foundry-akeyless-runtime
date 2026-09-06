"""Akeyless runtime client for Microsoft Foundry Hosted Agents."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

import akeyless

from akeyless_foundry.auth import AuthSession, authenticate, create_v2_api
from akeyless_foundry.cache import TtlCache
from akeyless_foundry.config import AkeylessRuntimeConfig, config_from_env, validate_config
from akeyless_foundry.paths import (
    format_structured_response,
    join_secret_path,
    normalize_path,
    pick_secret_from_response,
)


def _is_not_found_error(error: Exception) -> bool:
    status = getattr(error, "status", None)
    if status == 404:
        return True
    message = str(error).lower()
    return "not found" in message or "404" in message


@dataclass
class GetSecretOptions:
    path: str | None = None
    version: int | None = None
    json: bool = False
    ignore_cache: bool = False
    allow_dynamic_fallback: bool = False


@dataclass
class DynamicSecretOptions:
    path: str | None = None
    timeout: int | None = None
    args: list[str] | None = None
    host: str | None = None
    dbname: str | None = None
    target: str | None = None
    json: bool = False
    ignore_cache: bool = False


@dataclass
class RotatedSecretOptions:
    path: str | None = None
    host: str | None = None
    version: int | None = None
    json: bool = False
    ignore_cache: bool = False


class AkeylessRuntimeClient:
    def __init__(self, **config_overrides: Any) -> None:
        self._config = config_from_env(**config_overrides)
        validate_config(self._config)
        self._api = create_v2_api(self._config.gateway_url)
        self._session: AuthSession | None = None
        self._secret_cache: TtlCache[str] = TtlCache()

    @classmethod
    def from_env(cls, **overrides: Any) -> AkeylessRuntimeClient:
        return cls(**overrides)

    @property
    def config(self) -> AkeylessRuntimeConfig:
        return self._config

    def resolve_path(self, name_or_path: str) -> str:
        trimmed = name_or_path.strip()
        if trimmed.startswith("/"):
            return normalize_path(trimmed)
        return join_secret_path(self._config.secret_prefix, trimmed)

    def clear_cache(self) -> None:
        self._secret_cache.clear()
        self._session = None

    def _cache_key(self, path: str, kind: str, extra: str = "") -> str:
        return f"{kind}:{path}:{extra}"

    def _read_cached(self, path: str, kind: str, ignore_cache: bool) -> str | None:
        if ignore_cache:
            return None
        return self._secret_cache.get(self._cache_key(path, kind))

    def _write_cached(self, path: str, kind: str, value: str) -> None:
        self._secret_cache.set(
            self._cache_key(path, kind),
            value,
            self._config.secret_cache_ttl_seconds,
        )

    def _get_token(self) -> str:
        now = time.monotonic()
        if self._session and now < self._session.expires_at:
            return self._session.token

        self._session = authenticate(self._api, self._config)
        return self._session.token

    def get_secret_at_path(
        self,
        path: str,
        *,
        version: int | None = None,
        json: bool = False,
        ignore_cache: bool = False,
        allow_dynamic_fallback: bool = False,
    ) -> str:
        resolved = normalize_path(path)
        cached = self._read_cached(resolved, "static", ignore_cache)
        if cached is not None:
            return cached

        token = self._get_token()
        body_kwargs: dict[str, Any] = {"names": [resolved], "token": token}
        if version is not None:
            body_kwargs["version"] = version
        if json:
            body_kwargs["json"] = True
        if ignore_cache:
            body_kwargs["ignore_cache"] = "true"

        try:
            raw = self._api.get_secret_value(akeyless.GetSecretValue(**body_kwargs))
            if isinstance(raw, dict):
                value = pick_secret_from_response(resolved, raw)
            else:
                value = format_structured_response(raw)
            self._write_cached(resolved, "static", value)
            return value
        except Exception as error:
            if allow_dynamic_fallback and _is_not_found_error(error):
                return self.get_dynamic_secret_at_path(
                    resolved,
                    ignore_cache=ignore_cache,
                )
            raise

    def get_secret(
        self,
        name: str,
        options: GetSecretOptions | None = None,
    ) -> str:
        opts = options or GetSecretOptions()
        path = opts.path or self.resolve_path(name)
        return self.get_secret_at_path(
            path,
            version=opts.version,
            json=opts.json,
            ignore_cache=opts.ignore_cache,
            allow_dynamic_fallback=opts.allow_dynamic_fallback,
        )

    def get_secret_json(
        self,
        name: str,
        options: GetSecretOptions | None = None,
    ) -> dict[str, Any]:
        raw = self.get_secret(name, options)
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError(f"Secret {name!r} is not a JSON object")
        return data

    def get_dynamic_secret_at_path(
        self,
        path: str,
        options: DynamicSecretOptions | None = None,
    ) -> str:
        opts = options or DynamicSecretOptions()
        resolved = normalize_path(path)
        should_cache = not any(
            [
                opts.args,
                opts.timeout is not None,
                opts.host,
                opts.dbname,
                opts.target,
            ]
        )

        if should_cache:
            cached = self._read_cached(resolved, "dynamic", opts.ignore_cache)
            if cached is not None:
                return cached

        token = self._get_token()
        body_kwargs: dict[str, Any] = {"name": resolved, "token": token}
        if opts.timeout is not None:
            body_kwargs["timeout"] = opts.timeout
        if opts.args:
            body_kwargs["args"] = opts.args
        if opts.host:
            body_kwargs["host"] = opts.host
        if opts.dbname:
            body_kwargs["dbname"] = opts.dbname
        if opts.target:
            body_kwargs["target"] = opts.target
        if opts.json:
            body_kwargs["json"] = True
        if opts.ignore_cache:
            body_kwargs["ignore_cache"] = "true"

        raw = self._api.get_dynamic_secret_value(akeyless.GetDynamicSecretValue(**body_kwargs))
        value = format_structured_response(raw)

        if should_cache:
            self._write_cached(resolved, "dynamic", value)
        return value

    def get_dynamic_secret(
        self,
        name: str,
        options: DynamicSecretOptions | None = None,
    ) -> str:
        opts = options or DynamicSecretOptions()
        path = opts.path or self.resolve_path(name)
        return self.get_dynamic_secret_at_path(path, opts)

    def get_rotated_secret_at_path(
        self,
        path: str,
        options: RotatedSecretOptions | None = None,
    ) -> str:
        opts = options or RotatedSecretOptions()
        resolved = normalize_path(path)
        cached = self._read_cached(resolved, "rotated", opts.ignore_cache)
        if cached is not None:
            return cached

        token = self._get_token()
        body_kwargs: dict[str, Any] = {"names": resolved, "token": token}
        if opts.host:
            body_kwargs["host"] = opts.host
        if opts.version is not None:
            body_kwargs["version"] = opts.version
        if opts.json:
            body_kwargs["json"] = True
        if opts.ignore_cache:
            body_kwargs["ignore_cache"] = "true"

        raw = self._api.get_rotated_secret_value(akeyless.GetRotatedSecretValue(**body_kwargs))
        value = format_structured_response(raw)
        self._write_cached(resolved, "rotated", value)
        return value

    def get_rotated_secret(
        self,
        name: str,
        options: RotatedSecretOptions | None = None,
    ) -> str:
        opts = options or RotatedSecretOptions()
        path = opts.path or self.resolve_path(name)
        return self.get_rotated_secret_at_path(path, opts)

    def list_secrets(self, prefix: str | None = None) -> list[str]:
        """List secret names under a prefix. Returns paths only, never values."""
        resolved = normalize_path(prefix or self._config.secret_prefix)
        token = self._get_token()
        result = self._api.list_items(
            akeyless.ListItems(
                path=resolved,
                token=token,
                minimal_view=True,
                auto_pagination="enabled",
            )
        )

        items = getattr(result, "items", None) or []
        names: list[str] = []
        for item in items:
            if isinstance(item, dict):
                name = item.get("item_name")
            else:
                name = getattr(item, "item_name", None)
            if name:
                names.append(str(name))
        return sorted(names)


_default_client: AkeylessRuntimeClient | None = None


def get_default_client(**overrides: Any) -> AkeylessRuntimeClient:
    global _default_client
    if _default_client is None:
        _default_client = AkeylessRuntimeClient(**overrides)
    return _default_client


def reset_default_client() -> None:
    global _default_client
    _default_client = None


def get_secret(name: str, options: GetSecretOptions | None = None) -> str:
    return get_default_client().get_secret(name, options)
