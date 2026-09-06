# Deploy to Microsoft Foundry Hosted Agents

Walkthrough after [Akeyless setup](AKEYLESS_SETUP.md) and a successful local `access_key` test.

## 1. Add the library to the agent

In the hosted agent project `requirements.txt` (or `pyproject.toml`):

```text
akeyless-foundry-runtime>=0.1.0
```

Or install from [PyPI](https://pypi.org/project/akeyless-foundry-runtime/):

```bash
pip install akeyless-foundry-runtime
```

## 2. Fetch secrets in code

```python
from akeyless_foundry import get_secret

# Do not log the value.
app_secret = get_secret("APP_SECRET")
```

See [examples/hosted-agent/](../examples/hosted-agent/).

## 3. Set bootstrap environment variables

On the hosted agent definition, set **only** auth + path config:

| Variable | Required | Example |
|----------|----------|---------|
| `AKEYLESS_ACCESS_ID` | Yes | `p-xxxxxxxxxxxx` |
| `AKEYLESS_ACCESS_TYPE` | No | `azure_ad` (default) |
| `AKEYLESS_SECRET_PREFIX` | Recommended | `/foundry-agents/my-agent/production` |
| `AKEYLESS_GATEWAY_URL` | No | `https://api.akeyless.io` |
| `FOUNDRY_AGENT_NAME` | No | Used to derive prefix if `AKEYLESS_SECRET_PREFIX` is unset |
| `AKEYLESS_ENV` | No | `production` (default) |

Do **not** put application secret values in Foundry env vars.

## 4. Deploy the hosted agent

Use the Foundry portal, `azd`, or the Azure AI Projects SDK to deploy from a container image or source zip. See Microsoft Learn: [Deploy a hosted agent](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/deploy-hosted-agent) and [Deploy from source code](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/deploy-hosted-agent-code).

The platform assigns a **dedicated Entra identity** at deploy time. You do not configure a VM managed identity yourself.

## 5. Bind the agent identity in Akeyless

After the first successful deploy:

1. In Azure portal, open the Foundry project → the hosted agent → copy the agent's Entra **object ID** (service principal).
2. Update the Azure AD auth method:

```bash
akeyless auth-method update azure-ad \
  --name foundry-my-agent \
  --bound-spid "<agent-entra-object-id>"
```

Until this binding exists, a tenant-wide Azure AD auth method still works but is broader than least privilege.

## 6. Confirm outbound access

The hosted-agent sandbox must reach:

- Akeyless API / gateway (`AKEYLESS_GATEWAY_URL`, HTTPS)
- Azure IMDS / Entra token endpoint (so `akeyless-cloud-id` can mint a cloud ID)

If `akeyless-cloud-id` returns an empty cloud ID, the sandbox may not expose classic IMDS. Pass `AKEYLESS_CLOUD_ID` only as a last resort for debugging — do not bake a long-lived token into the image.

## 7. Invoke and check logs

Invoke the agent through its Foundry endpoint. Look for log lines such as `Fetching APP_SECRET from Akeyless` — never for the secret value.

| Error | Fix |
|-------|-----|
| Empty cloud ID | Identity not injected; confirm hosted-agent identity in Azure |
| 403 from Akeyless | Auth method / role / `--bound-spid` |
| 404 | Prefix or secret name |
| Timeout | Egress to Akeyless or Entra |
