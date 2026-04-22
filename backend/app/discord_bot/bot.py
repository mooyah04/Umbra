"""Umbra Discord bot — public `/umbra` slash command.

Read-only against the backend DB via the HTTP API. Never triggers WCL
ingest from the bot path (Logan's hard constraint, 2026-04-22): a public
bot installed across many servers sends all its requests from one IP,
which defeats the per-IP cold-parse cooldown protecting the WCL budget.
"""
from __future__ import annotations

import logging
import os

import discord
import httpx
from discord import app_commands

from . import embed as embed_lib

logger = logging.getLogger(__name__)

API_BASE = os.environ.get("UMBRA_API_BASE", "https://api.wowumbra.gg").rstrip("/")
BOT_TOKEN_ENV = "DISCORD_BOT_TOKEN"
GUILD_ID_ENV = "DISCORD_GUILD_ID"

VALID_REGIONS = frozenset({"us", "eu", "kr", "tw", "cn"})


class UmbraBot(discord.Client):
    def __init__(self) -> None:
        # Slash commands don't need privileged intents; default is enough.
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)
        self.http_client = httpx.AsyncClient(timeout=10.0)

    async def setup_hook(self) -> None:
        guild_id = os.environ.get(GUILD_ID_ENV)
        if guild_id:
            # Guild-scoped sync is instant — used for dev iteration.
            guild = discord.Object(id=int(guild_id))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            logger.info("Synced commands to guild %s", guild_id)
        else:
            # Global sync — can take up to 1h to propagate on first publish.
            await self.tree.sync()
            logger.info("Synced global commands")

    async def close(self) -> None:
        await self.http_client.aclose()
        await super().close()


bot = UmbraBot()


class QueryParseError(ValueError):
    """Raised when the user's free-text /umbra query is malformed."""


def _split_name_realm(raw: str) -> tuple[str, str] | None:
    """Split a `name-realm` or `name/realm` token into (name, realm).

    Splits on the FIRST separator so realms with hyphens (e.g. tarren-mill,
    twisting-nether) keep their compound names intact.
    """
    cleaned = raw.strip()
    for sep in ("/", "-"):
        if sep in cleaned:
            name, realm = cleaned.split(sep, 1)
            name = name.strip()
            realm = realm.strip()
            if name and realm:
                return name, realm
    return None


def parse_query(raw: str) -> tuple[str, str, str]:
    """Parse a free-text `/umbra` query into (name, realm, region).

    Accepted form: `name-realm region`, e.g. `elonmunk-tarrenmill eu`.
    The last whitespace-separated token must be a known region code;
    everything before it is the character identity.
    """
    tokens = raw.strip().split()
    if len(tokens) < 2:
        raise QueryParseError(
            "Missing region. Format: `name-realm region`, "
            "e.g. `elonmunk-tarrenmill eu`."
        )
    region = tokens[-1].lower()
    if region not in VALID_REGIONS:
        raise QueryParseError(
            f"Unknown region `{tokens[-1]}`. Use one of: us, eu, kr, tw, cn."
        )
    identity = " ".join(tokens[:-1])
    parsed = _split_name_realm(identity)
    if parsed is None:
        raise QueryParseError(
            "Couldn't parse character. Format: `name-realm`, "
            "e.g. `elonmunk-tarrenmill`."
        )
    name, realm = parsed
    return name, realm, region


@bot.tree.command(
    name="umbra",
    description="Look up an Umbra M+ grade. Example: elonmunk-tarrenmill eu",
)
@app_commands.describe(
    query="Format: name-realm region  (e.g. elonmunk-tarrenmill eu)",
)
async def umbra_command(
    interaction: discord.Interaction,
    query: str,
) -> None:
    await interaction.response.defer()

    try:
        name, realm, region = parse_query(query)
    except QueryParseError as exc:
        await interaction.followup.send(str(exc), ephemeral=True)
        return

    url = f"{API_BASE}/api/player/{region}/{realm}/{name}/all"
    try:
        resp = await bot.http_client.get(url)
    except httpx.HTTPError as exc:
        logger.warning("API request failed: %s", exc)
        await interaction.followup.send(
            "Couldn't reach Umbra right now. Try again in a moment.",
            ephemeral=True,
        )
        return

    if resp.status_code == 400:
        await interaction.followup.send(
            f"Invalid character or realm: `{name}-{realm}`. "
            "Double-check the spelling.",
            ephemeral=True,
        )
        return
    if resp.status_code != 200:
        logger.warning("API returned %s for %s", resp.status_code, url)
        await interaction.followup.send(
            "Umbra returned an unexpected error. Try again shortly.",
            ephemeral=True,
        )
        return

    try:
        payload = resp.json()
    except ValueError:
        logger.warning("Non-JSON response from %s", url)
        await interaction.followup.send(
            "Umbra returned an unreadable response.", ephemeral=True
        )
        return

    if payload.get("not_indexed"):
        await interaction.followup.send(
            embed_lib.not_indexed_message(region, realm, name)
        )
        return

    if payload.get("is_indexing"):
        await interaction.followup.send(
            embed_lib.still_indexing_message(region, realm, name)
        )
        return

    scores = payload.get("scores") or []
    if not scores:
        await interaction.followup.send(
            embed_lib.ungraded_message(
                region, realm, name, int(payload.get("total_runs") or 0)
            )
        )
        return

    embed = embed_lib.build_profile_embed(region, realm, name, payload)
    await interaction.followup.send(embed=embed)


def run() -> None:
    token = os.environ.get(BOT_TOKEN_ENV)
    if not token:
        raise SystemExit(
            f"{BOT_TOKEN_ENV} is not set. Create a bot at "
            "discord.com/developers/applications and export the token."
        )
    logger.info("Starting Umbra bot, API base = %s", API_BASE)
    bot.run(token)
