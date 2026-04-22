"""One-shot cleanup after pivoting from 13 class groups to 3 role groups.

Deletes the 13 class roles, the 13 class-named channels, and the
CLASSES category that setup_discord_server.py created in its prior
(pre-refactor) incarnation. Idempotent: each target is only touched
if present, so this can be re-run or partially completed without
causing errors.

Prereqs are the same as setup_discord_server.py:
  1. DISCORD_BOT_TOKEN in the environment.
  2. Bot holds @Devs (or equivalent admin) so it has Manage Channels
     + Manage Roles temporarily. Revoke after the cleanup completes.
  3. Stop the Railway bot service briefly so two processes aren't
     fighting over the same token.

Run from backend/ in PowerShell:
    python scripts/cleanup_discord_classes.py

Delete this file after a successful run — it has no ongoing purpose.
"""
from __future__ import annotations

import logging
import os
import sys

import discord

logger = logging.getLogger(__name__)

DEFAULT_GUILD_ID = 1494354441120383076

CLASS_ROLE_NAMES: tuple[str, ...] = (
    "Death Knight",
    "Demon Hunter",
    "Druid",
    "Evoker",
    "Hunter",
    "Mage",
    "Monk",
    "Paladin",
    "Priest",
    "Rogue",
    "Shaman",
    "Warlock",
    "Warrior",
)

CLASS_CHANNEL_NAMES: tuple[str, ...] = (
    "death-knight",
    "demon-hunter",
    "druid",
    "evoker",
    "hunter",
    "mage",
    "monk",
    "paladin",
    "priest",
    "rogue",
    "shaman",
    "warlock",
    "warrior",
)

OLD_CATEGORY_NAME = "CLASSES"


async def _run(client: discord.Client, guild_id: int) -> None:
    guild = client.get_guild(guild_id)
    if guild is None:
        logger.error(
            "Bot is not a member of guild %s. Invite it with the OAuth URL first.",
            guild_id,
        )
        return

    logger.info("Connected to guild: %s (id=%s)", guild.name, guild.id)
    summary: list[str] = []

    # 1. Channels first — category can't be cleanly deleted while it
    # still hosts text channels (Discord would orphan them otherwise).
    for name in CLASS_CHANNEL_NAMES:
        channel = discord.utils.get(guild.text_channels, name=name)
        if channel is None:
            summary.append(f"  - channel absent   #{name}")
            continue
        try:
            await channel.delete(reason="Pivot to 3 role-groups")
            summary.append(f"  x channel deleted  #{name}")
        except discord.Forbidden:
            summary.append(
                f"  ! can't delete #{name} (needs Manage Channels)"
            )

    # 2. Empty CLASSES category.
    category = discord.utils.get(guild.categories, name=OLD_CATEGORY_NAME)
    if category is None:
        summary.append(f"  - category absent  {OLD_CATEGORY_NAME}")
    else:
        try:
            await category.delete(reason="Pivot to 3 role-groups")
            summary.append(f"  x category deleted {OLD_CATEGORY_NAME}")
        except discord.Forbidden:
            summary.append(
                f"  ! can't delete category {OLD_CATEGORY_NAME} "
                "(needs Manage Channels)"
            )

    # 3. Class roles. Discord removes the role from any members who held
    # it — no one should at this point since Onboarding wasn't configured
    # yet to grant these.
    for name in CLASS_ROLE_NAMES:
        role = discord.utils.get(guild.roles, name=name)
        if role is None:
            summary.append(f"  - role absent      @{name}")
            continue
        try:
            await role.delete(reason="Pivot to 3 role-groups")
            summary.append(f"  x role deleted     @{name}")
        except discord.Forbidden:
            summary.append(
                f"  ! can't delete @{name} (needs Manage Roles or bot's "
                "role is below @{name} in hierarchy)"
            )

    logger.info("Cleanup summary:\n%s", "\n".join(summary))


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    token = os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        sys.exit(
            "DISCORD_BOT_TOKEN is not set. Export it or use "
            "`$env:DISCORD_BOT_TOKEN=...` in PowerShell before running."
        )

    guild_id_raw = os.environ.get("DISCORD_GUILD_ID") or str(DEFAULT_GUILD_ID)
    try:
        guild_id = int(guild_id_raw)
    except ValueError:
        sys.exit(f"DISCORD_GUILD_ID must be an integer, got: {guild_id_raw!r}")

    intents = discord.Intents.default()
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready() -> None:
        try:
            await _run(client, guild_id)
        finally:
            await client.close()

    client.run(token)


if __name__ == "__main__":
    main()
