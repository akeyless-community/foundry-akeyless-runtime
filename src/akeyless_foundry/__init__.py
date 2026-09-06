"""Fetch Akeyless secrets at runtime on Microsoft Foundry Hosted Agents."""

from akeyless_foundry.client import (
    AkeylessRuntimeClient,
    DynamicSecretOptions,
    GetSecretOptions,
    RotatedSecretOptions,
    get_default_client,
    get_secret,
)

__all__ = [
    "AkeylessRuntimeClient",
    "DynamicSecretOptions",
    "GetSecretOptions",
    "RotatedSecretOptions",
    "get_default_client",
    "get_secret",
]

__version__ = "0.1.0"
