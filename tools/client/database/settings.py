from typing import TYPE_CHECKING, List

from discord import Guild

from tools.client.cache import cache
from config import config

if TYPE_CHECKING:
    from main import Harvest


class Settings:
    bot: "Harvest"
    guild: Guild
    prefixes: List[str]

    def __init__(self, bot: "Harvest", guild: Guild, record: dict):
        self.bot = bot
        self.guild = guild
        self.prefixes = record.get("prefixes", [config.client.prefix])

    async def update(self, **kwargs):
        await self.bot.db.execute(
            """
            UPDATE settings
            SET
                prefixes = $2
            WHERE guild_id = $1
            """,
            self.guild.id,
            kwargs.get("prefixes", self.prefixes),
        )

        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    @cache()
    async def fetch(cls, bot: "Harvest", guild: Guild) -> "Settings":
        record = await bot.db.fetchrow(
            """
            INSERT INTO settings (guild_id)
            VALUES ($1)
            ON CONFLICT (guild_id)
            DO UPDATE
            SET guild_id = excluded.guild_id
            RETURNING *
            """,
            guild.id,
        )

        return cls(bot, guild, record)
