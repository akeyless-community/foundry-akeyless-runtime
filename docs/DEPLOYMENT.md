# Deployment patterns

This guide covers the ways to use `akeyless-foundry-runtime` on Microsoft Foundry Hosted Agents.

## Pattern overview

```
┌─────────────────────────────────────────────────────────────────┐
│                  Foundry Hosted Agent sandbox                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Your agent (Agent Framework / LangGraph / custom)       │   │
│  │                                                          │   │
│  │  ┌─────────────────┐    ┌──────────────────────────┐  │   │
│  │  │ In-agent fetch  │    │ MCP tools (optional)     │  │   │
│  │  │ get_secret      │    │ list / get_akeyless_*    │  │   │
│  │  └────────┬────────┘    └────────────┬─────────────┘  │   │
│  │           │                          │                 │   │
│  │           └──────────┬───────────────┘                 │   │
│  │                      ▼                                 │   │
│  │           akeyless-foundry-runtime                     │   │
│  │           (Azure AD cloud identity → Akeyless)         │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Akeyless Gateway │
                    └──────────────────┘
```

## Pattern 1: In-agent fetch only

**Best for:** agents that need the same secrets on every invocation (API keys, fixed config).

See [`examples/hosted-agent/`](../examples/hosted-agent/).

```python
from akeyless_foundry import get_secret

app_secret = get_secret("APP_SECRET")
```

## Pattern 2: Hybrid (recommended)

**Best for:** bootstrap secrets in code + agent-driven secret retrieval via MCP tools.

- `APP_SECRET` loaded via `get_secret()` at startup
- Other secrets available via `list_akeyless_secrets` / `get_akeyless_secret`

```python
from akeyless_foundry import AkeylessRuntimeClient

client = AkeylessRuntimeClient()
client.get_secret("APP_SECRET")
client.get_dynamic_secret("azure-creds")
client.get_rotated_secret("api-key")
```

## Pattern 3: MCP server in the agent container

**Best for:** a dedicated secrets MCP endpoint consumed by the agent or other MCP clients in the same sandbox.

See [`examples/mcp-server/server.py`](../examples/mcp-server/server.py).

```bash
pip install 'akeyless-foundry-runtime[mcp]'

export AKEYLESS_ACCESS_ID=p-xxxxx
export AKEYLESS_ACCESS_TYPE=access_key
export AKEYLESS_ACCESS_KEY=your-key
export AKEYLESS_SECRET_PREFIX=/foundry-agents/my-agent/dev

akeyless-foundry-mcp
```

Agents discover:

- `list_akeyless_secrets` (names only)
- `get_akeyless_secret`

## Environment variables reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AKEYLESS_ACCESS_ID` | Yes* | — | Akeyless auth method Access ID |
| `AKEYLESS_ACCESS_TYPE` | No | `azure_ad` | Auth method type |
| `AKEYLESS_SECRET_PREFIX` | Recommended | derived | Path prefix for short secret names |
| `AKEYLESS_GATEWAY_URL` | No | `https://api.akeyless.io` | Akeyless API / gateway URL |
| `FOUNDRY_AGENT_NAME` | No | — | Used to derive secret prefix |
| `AKEYLESS_ENV` | No | `production` | Environment segment in derived prefix |
| `AKEYLESS_SECRET_CACHE_TTL_SECONDS` | No | `300` | In-memory secret cache TTL |
| `AKEYLESS_TOKEN_EXPIRY_MARGIN_SECONDS` | No | `60` | Token refresh margin |

\* Not required if `AKEYLESS_TOKEN` is set (pre-authenticated session).

## Choosing a pattern

| Requirement | Pattern |
|-------------|---------|
| Simple agent, one API key | In-agent fetch |
| Agent picks secrets dynamically | Hybrid or MCP tools |
| Secrets must not pass through LLM context | In-agent fetch only |
| Audit tool invocations per secret access | MCP tools |
