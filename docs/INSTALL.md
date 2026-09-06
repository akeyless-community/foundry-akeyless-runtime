# Installation

You do **not** need to clone this repository to use the library. Add it as a dependency in your Foundry hosted agent project and install with `pip`.

## Option 1: PyPI (recommended)

Published as [akeyless-foundry-runtime](https://pypi.org/project/akeyless-foundry-runtime/) (`0.1.0`).

```bash
pip install akeyless-foundry-runtime
```

With optional extras:

```bash
pip install 'akeyless-foundry-runtime[mcp]'
```

In your agent's `requirements.txt`:

```text
akeyless-foundry-runtime>=0.1.0
```

## Option 2: Install directly from GitHub (no clone)

```bash
pip install "akeyless-foundry-runtime @ git+https://github.com/akeyless-community/foundry-akeyless-runtime.git"
```

Pin to a release tag for reproducible builds:

```bash
pip install "akeyless-foundry-runtime @ git+https://github.com/akeyless-community/foundry-akeyless-runtime.git@v0.1.0"
```

With extras:

```bash
pip install "akeyless-foundry-runtime[mcp] @ git+https://github.com/akeyless-community/foundry-akeyless-runtime.git@v0.1.0"
```

## Option 3: Copy the example agent (minimal)

1. Copy [`examples/hosted-agent/main.py`](../examples/hosted-agent/main.py) into your Foundry agent project
2. Add the dependency from Option 1 or 2 to `requirements.txt`
3. Set bootstrap env vars (see [AKEYLESS_SETUP.md](AKEYLESS_SETUP.md))
4. Deploy as a Foundry Hosted Agent ([FOUNDRY_DEPLOY.md](FOUNDRY_DEPLOY.md))

## Option 4: MCP server CLI only

```bash
pip install 'akeyless-foundry-runtime[mcp]'

export AKEYLESS_ACCESS_ID=p-xxxxx
export AKEYLESS_SECRET_PREFIX=/foundry-agents/my-agent/production

akeyless-foundry-mcp
```

## When you *do* need to clone

Clone the repo only if you are contributing, running tests, or developing the library:

```bash
git clone https://github.com/akeyless-community/foundry-akeyless-runtime.git
cd foundry-akeyless-runtime
pip install -e ".[dev]"
pytest
```

## Verify installation

```bash
python3 -c "from akeyless_foundry import __version__; print(__version__)"
```

Expected output: `0.1.0`
