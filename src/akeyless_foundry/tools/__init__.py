"""Foundry Hosted Agent tool integrations for Akeyless secrets."""

from akeyless_foundry.tools.service import SecretToolService

__all__ = [
    "SecretToolService",
    "create_mcp_server",
    "run_mcp_server",
]


def __getattr__(name: str):
    if name in ("create_mcp_server", "run_mcp_server"):
        from akeyless_foundry.tools.mcp import create_mcp_server, run_mcp_server

        return {"create_mcp_server": create_mcp_server, "run_mcp_server": run_mcp_server}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
