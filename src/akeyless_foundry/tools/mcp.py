"""FastMCP server exposing Akeyless secrets as Foundry Hosted Agent MCP tools."""

from __future__ import annotations

from typing import Any

from akeyless_foundry.tools.service import SecretToolService, SecretType

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover - optional dependency
    raise ImportError(
        "MCP support requires the 'mcp' package. Install with: pip install 'akeyless-foundry-runtime[mcp]'"
    ) from exc


def create_mcp_server(
    *,
    name: str = "akeyless-secrets",
    service: SecretToolService | None = None,
    host: str = "0.0.0.0",
    stateless_http: bool = True,
) -> FastMCP:
    """Create a FastMCP server with Akeyless secret tools."""
    tool_service = service or SecretToolService()
    mcp = FastMCP(name, host=host, stateless_http=stateless_http)

    @mcp.tool()
    def list_akeyless_secrets(prefix: str | None = None) -> str:
        """List Akeyless secret names under a path prefix. Returns names only, never values.

        Args:
            prefix: Optional Akeyless path prefix. Defaults to AKEYLESS_SECRET_PREFIX.
        """
        return tool_service.list_secrets(prefix=prefix).to_json()

    @mcp.tool()
    def get_akeyless_secret(
        name: str,
        path: str | None = None,
        secret_type: SecretType = "static",
        json_key: str | None = None,
        ignore_cache: bool = False,
    ) -> str:
        """Fetch a secret value from Akeyless. Authenticates with cloud identity (Azure AD by default).

        Use json_key when the secret is JSON and you only need one field.
        Use secret_type='dynamic' or 'rotated' for non-static secrets.

        Args:
            name: Short secret name (resolved with AKEYLESS_SECRET_PREFIX) or full path starting with /
            path: Optional full Akeyless path; overrides prefix + name resolution
            secret_type: static, dynamic, or rotated
            json_key: Return only this key from a JSON secret
            ignore_cache: Bypass the in-memory secret cache
        """
        return tool_service.get_secret(
            name,
            path=path,
            secret_type=secret_type,
            json_key=json_key,
            ignore_cache=ignore_cache,
        ).to_json()

    return mcp


def run_mcp_server(**kwargs: Any) -> None:
    """Run the Akeyless MCP server with streamable HTTP."""
    create_mcp_server(**kwargs).run(transport="streamable-http")
