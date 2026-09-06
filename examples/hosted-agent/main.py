"""Example Microsoft Foundry hosted agent that fetches secrets from Akeyless at runtime.

Bootstrap env vars (set on the hosted agent — not application secrets):

  AKEYLESS_ACCESS_ID=p-xxxxx
  AKEYLESS_ACCESS_TYPE=azure_ad
  AKEYLESS_SECRET_PREFIX=/foundry-agents/my-agent/production
  FOUNDRY_AGENT_NAME=my-agent

Store application secrets in Akeyless:
  /foundry-agents/my-agent/production/APP_SECRET

See docs/FOUNDRY_DEPLOY.md and docs/AKEYLESS_SETUP.md.
"""

from __future__ import annotations

import logging
import os

from akeyless_foundry import get_secret

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _load_app_secret() -> str:
    """Fetch APP_SECRET from Akeyless using the hosted agent's Entra identity."""
    prefix = os.environ.get("AKEYLESS_SECRET_PREFIX", "(not set)")
    logger.info("Fetching APP_SECRET from Akeyless (prefix=%s)", prefix)
    raw = get_secret("APP_SECRET")
    logger.info("Successfully fetched APP_SECRET from Akeyless")
    return raw.strip()


def main() -> None:
    secret = _load_app_secret()
    if not secret:
        raise SystemExit("APP_SECRET was empty")
    logger.info("Agent ready (secret length=%d)", len(secret))


if __name__ == "__main__":
    main()
