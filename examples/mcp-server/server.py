"""Deployable MCP server exposing Akeyless secrets as Foundry Hosted Agent tools.

Run locally:
  AKEYLESS_ACCESS_ID=p-xxxxx AKEYLESS_ACCESS_TYPE=access_key AKEYLESS_ACCESS_KEY=... \\
    python server.py
"""

from akeyless_foundry.tools.mcp import run_mcp_server

if __name__ == "__main__":
    run_mcp_server()
