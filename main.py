from __future__ import annotations
from typing import List, cast, Optional
from pathlib import Path

from aiohttp import ClientSession, TCPConnector
from datetime import datetime
from logging import DEBUG, getLogger
import asyncio

from colorama import Fore, Style

import discord
from discord import AllowedMentions, Intents, ClientUser, Interaction
from discord.ext import commands
from discord.message import Message
from discord.ext.commands import Bot, when_mentioned_or, MinimalHelpCommand
from discord.utils import utcnow

from tools.client import Redis, database, init_logging, Context
from tools.client.database import Database, Settings

from config import config

log = getLogger("bot")


async def get_prefix(bot: "Harvest", message: Message) -> List[str]:
    prefix = [config.client.prefix]
    if message.guild:
        prefix = (
            cast(
                Optional[List[str]],
                await bot.db.fetchval(
                    """
                    SELECT prefixes
                    FROM settings
                    WHERE guild_id = $1
                    """,
                    message.guild.id,
                ),
            )
            or prefix
        )

    return when_mentioned_or(*prefix)(bot, message)


class CleanHelp(MinimalHelpCommand):
    """
    Simplified help command that filters out Owner, Jishaku, and uncategorized commands,
    sending paginated embeds with a consistent primary color.
    """

    def __init__(self):
        super().__init__()
        self.embed_color = config.colors.primary

    async def send_pages(self):
        destination = self.get_destination()
        for page in self.paginator.pages:
            embed = discord.Embed(description=page, color=self.embed_color)
            await destination.send(embed=embed)

    async def filter_commands(self, commands_list, *, sort=True, key=None):
        # Exclude Owner, Jishaku cogs, and commands without a category
        filtered = [
            c
            for c in commands_list
            if c.cog_name not in ("Owner", "Jishaku") and c.cog_name
        ]
        return await super().filter_commands(filtered, sort=sort, key=key)


class Harvest(Bot):
    user: ClientUser
    session: ClientSession
    uptime: datetime
    database: Database
    redis: Redis

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
            intents=Intents(
                guilds=True,
                members=True,
                messages=True,
                reactions=True,
                moderation=True,
                message_content=True,
                emojis_and_stickers=True,
            ),
            allowed_mentions=AllowedMentions(
                everyone=False, roles=False, users=True, replied_user=True
            ),
            command_prefix=get_prefix,
            case_insensitive=True,
            owner_ids=config.client.owners,
            help_command=CleanHelp(),
        )
        self.buckets = {
            "guild_commands": {
                "lock": asyncio.Lock(),
                "cooldown": commands.CooldownMapping.from_cooldown(
                    12, 2.5, commands.BucketType.guild
                ),
                "blocked": set(),
            }
        }

    @staticmethod
    async def command_cooldown(ctx: Context) -> bool:
        if ctx.author.id == ctx.guild.owner_id:
            return True

        data = ctx.bot.buckets["guild_commands"]
        if ctx.guild.id in data["blocked"]:
            return False

        bucket = data["cooldown"].get_bucket(ctx.message)
        return bucket.update_rate_limit() is None

    async def on_message(self, message: Message):
        if message.author.bot:
            return

        mention_forms = {self.user.mention, f"<@!{self.user.id}>"}
        if message.content.strip() in mention_forms:
            ctx = await self.get_context(message)

            prefixes = ctx.settings.prefixes or [config.client.prefix]

            if len(prefixes) > 1:
                text = "The current prefixes are: " + ", ".join(
                    f"`{p}`" for p in prefixes
                )
            else:
                text = f"The current prefix is `{prefixes[0]}`"

            return await ctx.neutral(text)

        await self.process_commands(message)

    @property
    def db(self) -> Database:
        return self.database

    @property
    def owners(self) -> List[int]:
        return config.client.owners

    async def setup_hook(self) -> None:
        self.session = ClientSession(connector=TCPConnector(ssl=False))

        self.database = await database.connect()
        self.redis = await Redis.from_url()

    async def on_ready(self) -> None:
        if hasattr(self, "uptime"):
            return

        log.info(
            f"Connected as {Fore.LIGHTCYAN_EX}{Style.BRIGHT}{self.user}{Fore.RESET} ({Fore.LIGHTRED_EX}{self.user.id}{Fore.RESET})."
        )
        self.uptime = utcnow()

        await self.load_extensions()

    async def load_extensions(self) -> None:
        await bot.load_extension("jishaku")

        for feature in Path("cogs").iterdir():
            if not feature.is_dir():
                continue

            elif not (feature / "__init__.py").is_file():
                continue

            try:
                await self.load_extension(".".join(feature.parts))
            except Exception as exc:
                log.exception(
                    "Failed to load extension %s.", feature.name, exc_info=exc
                )

    async def get_context(
        self, origin: Message | Interaction, /, *, cls=Context
    ) -> Context:
        context = await super().get_context(origin, cls=cls)
        context.settings = await Settings.fetch(self, context.guild)

        return context

    def run(self) -> None:
        log.info("Starting the bot...")

        super().run(config.discord.token, reconnect=True, log_handler=None)

    async def on_command_error(self, ctx: Context, error: Exception):
        ignored = (
            commands.CommandNotFound,
            commands.NotOwner,
            commands.CheckFailure,
            commands.DisabledCommand,
            commands.UserInputError,
        )
        if isinstance(error, ignored):
            return

        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send_help(ctx.command)
        if isinstance(error, commands.CommandOnCooldown):
            retry = int(error.retry_after)
            minutes, seconds = divmod(retry, 60)

            if minutes > 0 and seconds > 0:
                time_str = f"{minutes}m {seconds}s"
            elif minutes > 0:
                time_str = f"{minutes}m"
            else:
                time_str = f"{seconds}s"

            return await ctx.warn(
                f"You are on cooldown for **{time_str}**", delete_after=10
            )
        if isinstance(error, commands.BadArgument):
            return await ctx.warn(str(error))


if __name__ == "__main__":
    bot = Harvest()
    init_logging(DEBUG)
    bot.run()
