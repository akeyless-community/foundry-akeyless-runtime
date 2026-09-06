# Security Policy

## Reporting vulnerabilities

Report security issues to [security@akeyless.io](mailto:security@akeyless.io). Do not open public GitHub issues for vulnerabilities.

## Design principles

1. **No application secrets in environment variables** — only bootstrap auth config (`AKEYLESS_ACCESS_ID`, gateway URL, path prefix).
2. **Cloud identity by default** — `azure_ad` uses the Foundry hosted agent's Entra identity; no long-lived Akeyless access keys in production.
3. **Secrets never logged** — the client returns values to your code only; do not log secret contents.
4. **In-memory caching** — secrets are cached in process memory with a configurable TTL. Use `ignore_cache=True` for highly sensitive one-time values.
5. **Least privilege** — bind the Akeyless auth method to the specific hosted-agent Entra object ID (`--bound-spid`) and restrict to the agent's secret path prefix.

## Production checklist

- [ ] Use `AKEYLESS_ACCESS_TYPE=azure_ad` (not `access_key`)
- [ ] Akeyless auth method bound to the hosted agent Entra identity (`--bound-spid`) after first deploy
- [ ] Read-only RBAC on `/foundry-agents/<agent>/<env>/*`
- [ ] No application secrets in Foundry hosted-agent environment variables
- [ ] Gateway URL points to your organization's Akeyless gateway (not a shared dev gateway)
