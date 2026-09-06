# Publishing to PyPI

**Live:** [pypi.org/project/akeyless-foundry-runtime](https://pypi.org/project/akeyless-foundry-runtime/) (`0.1.0`).

```bash
pip install akeyless-foundry-runtime
```

This page is for **future releases**. Use [trusted publishing](https://docs.pypi.org/trusted-publishers/) (no API tokens in GitHub Secrets).

## Do you need a public GitHub repo?

| Goal | Public repo required? |
|------|----------------------|
| **Publish to PyPI** via trusted publishing | **No** — private repos work |
| **`pip install akeyless-foundry-runtime`** from PyPI | **No** — PyPI is public |
| **`pip install` from GitHub URL** (no clone) | **Yes** — private repos require a GitHub token |
| **Community contributors / issues / docs on GitHub** | **Yes** — recommended for `akeyless-community` packages |

**Recommendation:** Make the repository **public** before the first release.

### Make the repo public (one-time)

```bash
gh repo edit akeyless-community/foundry-akeyless-runtime --visibility public
```

## Prerequisites

- Admin access to the `akeyless-community` GitHub org (or repo maintainer)
- A [PyPI](https://pypi.org) account
- The package name `akeyless-foundry-runtime` available on PyPI

## Step 1: Register the PyPI project with a trusted publisher

1. Log in to [pypi.org](https://pypi.org)
2. Go to **Account settings** → **Publishing** → **Add a new pending publisher**
3. Fill in:

| Field | Value |
|-------|-------|
| **PyPI Project Name** | `akeyless-foundry-runtime` |
| **Publisher** | GitHub |
| **Owner** | `akeyless-community` |
| **Repository name** | `foundry-akeyless-runtime` |
| **Workflow name** | `publish.yml` |
| **Environment name** | `pypi` |

4. Click **Add**

## Step 2: Verify the GitHub Actions workflow

The repo includes `.github/workflows/publish.yml`:

- Triggers on **GitHub Release published**
- Builds wheel + sdist with `python -m build`
- Uploads via `pypa/gh-action-pypi-publish` (OIDC)

## Step 3: Create a GitHub Release

1. Bump `version` in `pyproject.toml` (currently `0.1.0`)
2. Commit and push to `main`
3. Publish a GitHub Release tagged `v0.1.0`

```bash
gh release create v0.1.0 \
  --repo akeyless-community/foundry-akeyless-runtime \
  --title "v0.1.0" \
  --notes "Initial PyPI release"
```

## Step 4: Confirm the publish

On success, visit [pypi.org/project/akeyless-foundry-runtime](https://pypi.org/project/akeyless-foundry-runtime/).

```bash
pip install akeyless-foundry-runtime
python3 -c "from akeyless_foundry import __version__; print(__version__)"
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Trusted publishing exchange failure` | Verify PyPI publisher owner/repo/workflow name match exactly |
| `File already exists` on PyPI | Bump version — versions cannot be re-uploaded |
| Workflow doesn't run | Release must be **published**, not draft |
| `Non-user identities cannot create new projects` | Pending publisher **PyPI project name** must be `akeyless-foundry-runtime` (the package name), not `foundry-akeyless-runtime` (the GitHub repo). Delete the empty wrong-name project on PyPI, recreate the pending publisher, then re-run. |
