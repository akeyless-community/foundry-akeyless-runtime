# Examples

| Example | Pattern | Description |
|---------|---------|-------------|
| [`hosted-agent/`](hosted-agent/) | In-agent fetch | Minimal Foundry hosted agent; loads a secret from Akeyless at startup |
| [`mcp-server/`](mcp-server/) | MCP server | Standalone MCP endpoint with list/get tools |

## Quick start

1. Complete [Akeyless setup](../docs/AKEYLESS_SETUP.md)
2. Copy `.env.example` to `.env` for local testing (never commit `.env`)
3. Pick an example and follow its `requirements.txt`
4. Deploy to Foundry: [FOUNDRY_DEPLOY.md](../docs/FOUNDRY_DEPLOY.md)

```bash
# Local test (access_key auth)
export AKEYLESS_ACCESS_ID=p-xxxxx
export AKEYLESS_ACCESS_TYPE=access_key
export AKEYLESS_ACCESS_KEY=your-readonly-key
export AKEYLESS_SECRET_PREFIX=/foundry-agents/my-agent/dev

cd examples/hosted-agent
pip install -r requirements.txt
python main.py
```

Do not print secret values. Logs should show the prefix and success only.
