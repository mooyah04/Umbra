"""Entry point for the Umbra Discord bot.

Run locally:
    python -m app.discord_bot

Requires env vars:
    DISCORD_BOT_TOKEN        - bot token from discord.com/developers
    UMBRA_API_BASE           - backend URL (e.g., https://api.wowumbra.gg,
                                or http://<service>.railway.internal:8000
                                when deployed as a sibling Railway service)
    DISCORD_GUILD_ID (opt)   - guild ID for instant command sync during dev.
                                When unset, commands register globally
                                (propagation up to 1h).
"""
from __future__ import annotations

import logging

from .bot import run


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    run()


if __name__ == "__main__":
    main()
