"""One-shot script to finalize the Umbra Discord server structure.

Handles the polish on pre-existing channels (topics, read-only perms,
welcome + usage messages) and creates the 3 gameplay-role groups
(Tank / Healer / DPS) with matching role-gated channels under a ROLES
category.

Idempotent: safe to re-run. Topics are compared before editing;
messages authored by the bot are edited in place instead of duplicated;
roles and channels are created only if they don't already exist.

Prereqs to run:
  1. Set DISCORD_BOT_TOKEN in the environment (same token the deployed
     bot uses).
  2. Temporarily grant the bot the @Devs role in Discord so it has
     Manage Channels + Manage Roles + Send Messages. Server Settings ->
     Members -> find the bot -> assign role. Remove after the script
     completes. (The persistent Umbra-bot role with just Manage Roles
     is not enough for this script because it also creates channels.)
  3. Run from the backend/ directory:
        python scripts/setup_discord_server.py
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
from typing import Iterable

import discord

logger = logging.getLogger(__name__)

DEFAULT_GUILD_ID = 1494354441120383076  # Umbra server; override via env.

# Channels the script manages. Unmentioned channels (development,
# ban-reasons, voice) are left alone.
CHANNEL_TOPICS: dict[str, str] = {
    "welcome": "Welcome to Umbra. Start here.",
    "announcements": "Product updates and releases. Announcements only.",
    "general": "General conversation for Umbra users.",
    "scoring-talk": "Discussion of the scoring methodology and grade outcomes.",
    "showcase": "Share screenshots of your Umbra grade or profile.",
    "bug-reports": (
        "Report bugs. Include steps to reproduce and a profile link when possible."
    ),
    "suggestions": "Feature ideas and improvements for Umbra.",
    "umbra-lookups": "Look up M+ grades with /umbra name-realm region.",
}

# @everyone: read yes, send no. @Devs: send yes. Other roles fall through
# to the @everyone baseline.
READ_ONLY_CHANNELS: frozenset[str] = frozenset({"welcome", "announcements"})

# Gameplay-role groups: tank / healer / dps. Colors picked to match
# WoW's in-game role palette (blue = defense, green = healing,
# red = damage). Channel names pluralized since each hosts a cohort.
ROLE_GROUPS: dict[str, dict[str, object]] = {
    "Tank": {
        "color": 0x3B82F6,
        "channel": "tanks",
        "topic": "Discussion for tank players.",
    },
    "Healer": {
        "color": 0x10B981,
        "channel": "healers",
        "topic": "Discussion for healer players.",
    },
    "DPS": {
        "color": 0xEF4444,
        "channel": "dps",
        "topic": "Discussion for DPS players.",
    },
}

ROLES_CATEGORY_NAME = "ROLES"

WELCOME_MESSAGE = """\
# Welcome to the Umbra community

Umbra grades World of Warcraft Mythic+ performance from S+ to F- using Warcraft Logs data. Grades appear in-game on tooltips and in the Group Finder, with full profiles and leaderboards at https://wowumbra.gg.

## Channels

- <#announcements> — product updates and releases
- <#general> — general conversation
- <#umbra-lookups> — look up grades in Discord with `/umbra name-realm region`
- <#tanks> / <#healers> / <#dps> — role-specific discussion (visible after you pick your role)
- <#showcase> — share your grade and profile screenshots
- <#scoring-talk> — discuss the scoring methodology
- <#bug-reports> — report issues (include reproduction steps)
- <#suggestions> — propose features and improvements

## Install the addon

- **CurseForge**: https://www.curseforge.com/wow/addons/umbra
- **Wago**: https://addons.wago.io/addons/umbra
- **Website**: https://wowumbra.gg

## Community guidelines

1. Treat other members with respect. Critique scoring methodology, not individuals.
2. Do not harass or call out players based on their grade.
3. Keep bug reports and feature requests in their dedicated channels.
4. No promotion of boosting services, competing tools, or unrelated products.
5. English is preferred in shared channels for moderation purposes.

Enforcement escalates from warning to timeout to ban at moderator discretion.

For support or questions, mention the **@Devs** role.
"""

LOOKUPS_USAGE_MESSAGE = """\
## Grade lookup commands

Use `/umbra <name-realm> <region>` to look up any character's M+ grade.

**Examples**
- `/umbra elonmunk-tarrenmill eu`
- `/umbra mooyuh-silvermoon us`

**Supported regions**: `us`, `eu`, `kr`, `tw`, `cn`

Characters not yet indexed on wowumbra.gg will receive a link to claim with a Warcraft Logs URL.
"""

# Channels referenced inside the welcome copy. Rendered as Discord mentions
# (<#id>) at post time so the links resolve correctly.
WELCOME_CHANNEL_REFS: tuple[str, ...] = (
    "announcements",
    "general",
    "umbra-lookups",
    "tanks",
    "healers",
    "dps",
    "showcase",
    "scoring-talk",
    "bug-reports",
    "suggestions",
)


def _substitute_channel_mentions(
    content: str, channels: dict[str, discord.TextChannel], names: Iterable[str]
) -> str:
    """Replace `<#channel-name>` placeholders with `<#channel-id>`."""
    for name in names:
        if name in channels:
            content = content.replace(f"<#{name}>", f"<#{channels[name].id}>")
    return content


async def _apply_topic(
    channel: discord.TextChannel, topic: str, summary: list[str]
) -> None:
    if channel.topic == topic:
        summary.append(f"  = topic unchanged  #{channel.name}")
        return
    try:
        await channel.edit(topic=topic)
        summary.append(f"  + topic updated   #{channel.name}")
    except discord.Forbidden:
        summary.append(
            f"  ! no permission to edit #{channel.name} "
            "(needs Manage Channels)"
        )


async def _apply_read_only(
    channel: discord.TextChannel,
    everyone: discord.Role,
    devs: discord.Role | None,
    summary: list[str],
) -> None:
    try:
        await channel.set_permissions(everyone, send_messages=False)
        if devs is not None:
            await channel.set_permissions(devs, send_messages=True)
        summary.append(f"  + read-only       #{channel.name}")
    except discord.Forbidden:
        summary.append(
            f"  ! no permission to set perms on #{channel.name} "
            "(needs Manage Roles)"
        )


async def _upsert_bot_message(
    channel: discord.TextChannel,
    content: str,
    bot_user: discord.ClientUser,
    summary: list[str],
) -> None:
    """Edit the most recent bot-authored message in place, or post a new one.

    Keeps the channel clean on re-runs instead of stacking duplicates.
    """
    existing: discord.Message | None = None
    async for message in channel.history(limit=50):
        if message.author.id == bot_user.id:
            existing = message
            break
    try:
        if existing is not None:
            if existing.content.strip() == content.strip():
                summary.append(f"  = message unchanged #{channel.name}")
                return
            await existing.edit(content=content)
            summary.append(f"  + message updated #{channel.name}")
        else:
            await channel.send(content=content)
            summary.append(f"  + message posted  #{channel.name}")
    except discord.Forbidden:
        summary.append(
            f"  ! no permission to post in #{channel.name} "
            "(needs Send Messages)"
        )


async def _ensure_role_groups(
    guild: discord.Guild, summary: list[str]
) -> dict[str, discord.Role]:
    """Create Tank/Healer/DPS roles with role-palette colors if absent.

    Returns the full role_name -> Role mapping (pre-existing + newly
    created) so downstream channel-perms setup can reference them.
    """
    by_name = {r.name: r for r in guild.roles}
    roles: dict[str, discord.Role] = {}
    for role_name, spec in ROLE_GROUPS.items():
        color_value = int(spec["color"])  # type: ignore[arg-type]
        target_colour = discord.Colour(color_value)
        if role_name in by_name:
            role = by_name[role_name]
            if role.colour.value != color_value:
                try:
                    await role.edit(
                        colour=target_colour, reason="Umbra role color sync"
                    )
                    summary.append(f"  + color synced    @{role_name}")
                except discord.Forbidden:
                    summary.append(
                        f"  ! can't edit color @{role_name} (needs Manage Roles)"
                    )
            else:
                summary.append(f"  = role exists     @{role_name}")
            roles[role_name] = role
            continue
        try:
            role = await guild.create_role(
                name=role_name,
                colour=target_colour,
                mentionable=False,
                hoist=False,
                reason="Umbra gameplay-role setup",
            )
            summary.append(f"  + role created    @{role_name}")
            roles[role_name] = role
        except discord.Forbidden:
            summary.append(
                f"  ! can't create @{role_name} (needs Manage Roles)"
            )
    return roles


async def _ensure_roles_category(
    guild: discord.Guild, summary: list[str]
) -> discord.CategoryChannel | None:
    existing = discord.utils.get(guild.categories, name=ROLES_CATEGORY_NAME)
    if existing is not None:
        summary.append(f"  = category exists {ROLES_CATEGORY_NAME}")
        return existing
    try:
        category = await guild.create_category(
            ROLES_CATEGORY_NAME, reason="Umbra role channels setup"
        )
        summary.append(f"  + category created {ROLES_CATEGORY_NAME}")
        return category
    except discord.Forbidden:
        summary.append(
            f"  ! can't create category {ROLES_CATEGORY_NAME} "
            "(needs Manage Channels)"
        )
        return None


async def _ensure_role_channels(
    guild: discord.Guild,
    category: discord.CategoryChannel,
    role_group_roles: dict[str, discord.Role],
    summary: list[str],
) -> None:
    """Create #tanks / #healers / #dps with role-gated visibility.

    Permission model:
      @everyone   -> view_channel=False  (hidden by default)
      @<Role>     -> view_channel=True, send_messages=True
      @Moderator  -> view_channel=True, send_messages=True  (moderation)
      @Devs       -> view_channel=True, send_messages=True  (admin)
    """
    mod = discord.utils.get(guild.roles, name="Moderator")
    devs = discord.utils.get(guild.roles, name="Devs")
    existing = {c.name: c for c in guild.text_channels}

    for role_name, spec in ROLE_GROUPS.items():
        role = role_group_roles.get(role_name)
        if role is None:
            continue
        channel_name = str(spec["channel"])
        topic = str(spec["topic"])
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            role: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
            ),
        }
        if mod is not None:
            overwrites[mod] = discord.PermissionOverwrite(
                view_channel=True, send_messages=True
            )
        if devs is not None:
            overwrites[devs] = discord.PermissionOverwrite(
                view_channel=True, send_messages=True
            )

        if channel_name in existing:
            ch = existing[channel_name]
            try:
                # edit() with overwrites replaces the overwrite set entirely,
                # which is what we want for a script-managed channel. Topic
                # and category are reconciled at the same time.
                await ch.edit(
                    category=category, topic=topic, overwrites=overwrites
                )
                summary.append(f"  = channel synced  #{channel_name}")
            except discord.Forbidden:
                summary.append(
                    f"  ! can't edit #{channel_name} (needs Manage Channels)"
                )
            continue
        try:
            await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=topic,
                reason="Umbra role channel setup",
            )
            summary.append(f"  + channel created #{channel_name}")
        except discord.Forbidden:
            summary.append(
                f"  ! can't create #{channel_name} (needs Manage Channels)"
            )


async def _run(client: discord.Client, guild_id: int) -> None:
    guild = client.get_guild(guild_id)
    if guild is None:
        logger.error(
            "Bot is not a member of guild %s. Invite it with the OAuth URL first.",
            guild_id,
        )
        return

    logger.info("Connected to guild: %s (id=%s)", guild.name, guild.id)

    channels: dict[str, discord.TextChannel] = {
        c.name: c for c in guild.text_channels
    }
    missing = [name for name in CHANNEL_TOPICS if name not in channels]
    if missing:
        logger.warning(
            "Expected channels not found (script will skip them): %s",
            ", ".join(missing),
        )

    everyone = guild.default_role
    devs = discord.utils.get(guild.roles, name="Devs")
    if devs is None:
        logger.warning(
            "No @Devs role found; read-only channels will block @everyone "
            "from sending with no role allow-list to compensate."
        )

    summary: list[str] = []

    # 1. Role-group roles first — channel perms in step 4 reference them.
    role_group_roles = await _ensure_role_groups(guild, summary)

    # 2. Topics on all managed existing channels.
    for name, topic in CHANNEL_TOPICS.items():
        if name in channels:
            await _apply_topic(channels[name], topic, summary)

    # 3. Read-only perms on welcome + announcements.
    for name in READ_ONLY_CHANNELS:
        if name in channels:
            await _apply_read_only(channels[name], everyone, devs, summary)

    # 4. ROLES category + per-role gated channels.
    category = await _ensure_roles_category(guild, summary)
    if category is not None and role_group_roles:
        await _ensure_role_channels(guild, category, role_group_roles, summary)

    # Refresh channel cache: role channels just created aren't in the
    # `channels` map built from the original snapshot.
    channels = {c.name: c for c in guild.text_channels}

    # 5. Welcome message (resolves channel mentions at post time).
    if "welcome" in channels:
        welcome_content = _substitute_channel_mentions(
            WELCOME_MESSAGE, channels, WELCOME_CHANNEL_REFS
        )
        await _upsert_bot_message(
            channels["welcome"], welcome_content, client.user, summary
        )

    # 6. Usage helper in umbra-lookups.
    if "umbra-lookups" in channels:
        await _upsert_bot_message(
            channels["umbra-lookups"], LOOKUPS_USAGE_MESSAGE, client.user, summary
        )

    logger.info("Setup summary:\n%s", "\n".join(summary))


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    token = os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        sys.exit(
            "DISCORD_BOT_TOKEN is not set. Export it or use `$env:DISCORD_BOT_TOKEN=...` "
            "in PowerShell before running."
        )

    guild_id_raw = os.environ.get("DISCORD_GUILD_ID") or str(DEFAULT_GUILD_ID)
    try:
        guild_id = int(guild_id_raw)
    except ValueError:
        sys.exit(f"DISCORD_GUILD_ID must be an integer, got: {guild_id_raw!r}")

    intents = discord.Intents.default()
    # guilds intent comes with Intents.default(); that's all we need.
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
