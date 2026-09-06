"""Path helpers for resolving Akeyless secret names on Foundry Hosted Agents."""

from __future__ import annotations

import json
import os
from typing import Any


def normalize_path(path: str) -> str:
    trimmed = path.strip()
    if not trimmed:
        return "/"
    with_leading = trimmed if trimmed.startswith("/") else f"/{trimmed}"
    collapsed = "/".join(part for part in with_leading.split("/") if part)
    return f"/{collapsed}" if collapsed else "/"


def join_secret_path(prefix: str, name: str) -> str:
    base = normalize_path(prefix)
    segment = name.strip().lstrip("/")
    if not segment:
        return base
    if base == "/":
        return f"/{segment}"
    return f"{base}/{segment}"


def stringify_secret_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).decode("utf-8")
    return json.dumps(value)


def pick_secret_from_response(requested_path: str, data: dict[str, Any] | None) -> str:
    if not data:
        raise ValueError("Akeyless returned an empty secret payload")

    trimmed = requested_path.strip()
    candidates = [
        trimmed,
        normalize_path(trimmed),
        trimmed.lstrip("/"),
    ]

    for key in candidates:
        if key in data:
            return stringify_secret_value(data[key])

    raise ValueError(f'No value for "{requested_path}" in Akeyless response')


def format_structured_response(data: Any) -> str:
    if data is None:
        raise ValueError("Akeyless returned an empty response")
    if isinstance(data, str):
        return data
    return json.dumps(data)


def foundry_environment() -> str:
    for key in ("AKEYLESS_ENV", "FOUNDRY_ENV", "ENVIRONMENT"):
        value = os.environ.get(key, "").strip().lower()
        if value:
            return value
    return "production"


def default_foundry_secret_prefix() -> str | None:
    agent_name = os.environ.get("FOUNDRY_AGENT_NAME", "").strip()
    if not agent_name:
        return None
    return f"/foundry-agents/{agent_name}/{foundry_environment()}"
