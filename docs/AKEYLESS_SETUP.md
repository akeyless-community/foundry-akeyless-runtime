# Akeyless setup for Foundry Hosted Agents

Step-by-step guide to configure Akeyless before deploying a Foundry hosted agent with this library.

## Prerequisites

- An [Akeyless](https://www.akeyless.io) account (SaaS or self-hosted gateway)
- An Azure subscription with [Microsoft Foundry](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/hosted-agents) Hosted Agents
- Your hosted agent deployed (or planned) so it has a dedicated Entra identity

## 1. Create an Azure AD Auth Method

In the Akeyless console (or CLI), create an **Azure AD** authentication method:

1. Go to **Auth Methods** → **New** → **Azure AD**
2. Set **Bound Tenant ID** to your Azure tenant
3. Copy the **Access ID** (format: `p-xxxxxxxxxxxx`)

### CLI example

```bash
akeyless auth-method create azure-ad \
  --name foundry-my-agent \
  --bound-tenant-id "<Azure Tenant ID>"
```

> **Tip:** Foundry creates the hosted agent's Entra identity at **first deploy**. Start with a tenant-bound auth method, deploy once, then tighten with `--bound-spid` (the agent's service principal / object ID). This is the same chicken-and-egg as binding an AgentCore IAM role after first deploy.

Optional tightening after you have the agent identity:

```bash
akeyless auth-method update azure-ad \
  --name foundry-my-agent \
  --bound-spid "<agent-entra-object-id>"
```

See [Azure AD authentication](https://docs.akeyless.io/docs/auth-with-azure) for issuer, JWKS, audience, and other bound-* flags.

## 2. Create a secret path and RBAC

Use a dedicated path per agent and environment:

```
/foundry-agents/my-agent/production/
/foundry-agents/my-agent/staging/
```

Create an Akeyless **role** with read-only access to that path:

| Permission | Scope |
|------------|-------|
| `read` | `/foundry-agents/my-agent/production/*` |
| `list` | `/foundry-agents/my-agent/production/*` |

Associate the Azure AD auth method with this role.

## 3. Store secrets in Akeyless

Create static, dynamic, or rotated secrets under your prefix:

```
/foundry-agents/my-agent/production/APP_SECRET
/foundry-agents/my-agent/production/DATABASE_URL
/foundry-agents/my-agent/production/APP_CONFIG   # JSON with multiple keys
```

**JSON secret example** (`APP_CONFIG`):

```json
{
  "DATABASE_URL": "postgresql://user:pass@host:5432/db",
  "STRIPE_KEY": "sk_live_..."
}
```

Use `get_secret_json("APP_CONFIG")` or `get_akeyless_secret(..., json_key="DATABASE_URL")` to read individual fields.

## 4. Configure Foundry environment variables

Set **bootstrap** variables on the hosted agent — **not** application secrets:

```text
AKEYLESS_ACCESS_ID=p-xxxxxxxxxxxx
AKEYLESS_ACCESS_TYPE=azure_ad
AKEYLESS_SECRET_PREFIX=/foundry-agents/my-agent/production
AKEYLESS_GATEWAY_URL=https://api.akeyless.io
FOUNDRY_AGENT_NAME=my-agent
```

Full deploy walkthrough: **[FOUNDRY_DEPLOY.md](FOUNDRY_DEPLOY.md)**.

For self-hosted gateways, set `AKEYLESS_GATEWAY_URL` to your gateway URL (e.g. `https://gateway.example.com`).

## 5. Verify locally (optional)

Before deploying to Foundry, test with a read-only access key:

```bash
cp .env.example .env
# Edit .env with your test credentials

export AKEYLESS_ACCESS_TYPE=access_key
export AKEYLESS_ACCESS_KEY=your-readonly-key

python3 -c "
from akeyless_foundry import get_secret
value = get_secret('APP_SECRET')
print('OK' if value else 'empty')
"
```

Do not print secret values.

## 6. Verify on Foundry

After deploy, check agent logs for authentication errors. Common issues:

| Error | Fix |
|-------|-----|
| `could not obtain cloud identity` / empty cloud ID | Agent Entra identity not available in the sandbox; confirm hosted-agent identity is assigned |
| `access denied` / `403` | RBAC role not associated with auth method, or `oid` / `--bound-spid` mismatch |
| `not found` / `404` | Wrong `AKEYLESS_SECRET_PREFIX` or secret path |
| Gateway timeout | Egress from the hosted-agent sandbox blocking HTTPS to Akeyless |

## Dynamic and rotated secrets

For dynamic secrets (e.g. temporary Azure credentials):

```python
from akeyless_foundry import AkeylessRuntimeClient

client = AkeylessRuntimeClient()
creds = client.get_dynamic_secret("azure-dynamic-secret")
```

Or via tool:

```python
get_akeyless_secret(name="azure-dynamic-secret", secret_type="dynamic")
```

For rotated secrets, use `secret_type="rotated"` or `client.get_rotated_secret(...)`.
