from __future__ import annotations

import asyncio
import random
from pathlib import Path
import json

from discord import Embed, Member
from discord.ext.commands import Cog, command
from discord.ext import commands

from main import Harvest
from tools.client.context import Context
from config import config


class Economy(Cog):
    CACHE_TTL = 3600

    def __init__(self, bot: Harvest):
        self.bot = bot
        data_path = Path(__file__).parent / "beg_outcomes.json"
        with open(data_path, "r", encoding="utf-8") as f:
            self._msgs = json.load(f)


    async def _get_wallet(self, user_id: int) -> int:
        key = f"bal:{user_id}"
        bal = await self.bot.redis.get(key)
        if bal is not None:
            await self.bot.redis.expire(key, self.CACHE_TTL)
            return int(bal)

        bal = (
            await self.bot.db.fetchval(
                "SELECT wallet FROM economy WHERE user_id = $1", user_id
            )
            or 0
        )
        await self.bot.redis.set(key, bal, ex=self.CACHE_TTL)
        return int(bal)

    def _schedule_wallet_upsert(self, user_id: int, wallet: int) -> None:
        async def _upsert():
            await self.bot.db.execute(
                """
                INSERT INTO economy(user_id, wallet)
                  VALUES($1, $2)
                ON CONFLICT (user_id) DO UPDATE
                  SET wallet = EXCLUDED.wallet
                """,
                user_id,
                wallet,
            )
        asyncio.create_task(_upsert())

    @command(name="beg")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def beg(self, ctx: Context):
        """Beg for money, a early way to get money."""
        user_id = ctx.author.id
        current = await self._get_wallet(user_id)

        category = random.choice(["nothing", "lose", "win"])
        if category == "nothing":
            msg_text = random.choice(self._msgs["nothing"])
            new_wallet = current
        else:
            amount = random.randint(1, 50)
            new_wallet = current - amount if category == "lose" else current + amount
            template = random.choice(self._msgs[category])
            msg_text = template.replace("${amount}", f"**${amount}**")

        key = f"bal:{user_id}"
        await self.bot.redis.set(key, new_wallet, ex=self.CACHE_TTL)
        self._schedule_wallet_upsert(user_id, new_wallet)

        embed = Embed(description=msg_text, color=config.colors.primary)
        embed.set_footer(text=f"Wallet balance: ${new_wallet}")
        await ctx.send(embed=embed)

    @command(name="openaccount", aliases=["openacc"])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def openaccount(self, ctx: Context):
        """Open a bank account by depositing $400 from your wallet."""
        user_id = ctx.author.id

        record = await self.bot.db.fetchrow(
            "SELECT wallet, bank FROM economy WHERE user_id = $1", user_id
        )
        wallet = record["wallet"] or 0 if record else 0
        bank   = record["bank"]   or 0 if record else 0

        if bank > 0:
            return await ctx.neutral(
                f"You already have a bank account with **${bank}** in it."
            )

        if wallet < 400:
            needed = 400 - wallet
            return await ctx.neutral(
                f"You need **${needed}** more in your wallet to open a bank account."
            )

        new_wallet = wallet - 400
        await self.bot.redis.set(f"bal:{user_id}", new_wallet, ex=self.CACHE_TTL)

        async def _open_upsert():
            await self.bot.db.execute(
                """
                INSERT INTO economy(user_id, wallet, bank)
                  VALUES ($1, $2, 400)
                ON CONFLICT (user_id) DO UPDATE
                  SET wallet = EXCLUDED.wallet,
                      bank   = EXCLUDED.bank
                """,
                user_id,
                new_wallet,
            )
        asyncio.create_task(_open_upsert())

        await ctx.neutral(
            f"🏦 Bank account opened! $400 has been moved into your bank.\n"
            f"Wallet: **${new_wallet}**, Bank: **$400**"
        )

    @command(name="balance", aliases=["bal"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def balance(self, ctx: Context, member: Member = None):
        """Show a user's wallet, bank, total balance, and rank."""
        target = member or ctx.author
        user_id = target.id

        record = await self.bot.db.fetchrow(
            "SELECT wallet, bank FROM economy WHERE user_id = $1", user_id
        )
        if not record:
            if target == ctx.author:
                return await ctx.neutral(
                    "You don't have an account yet! Use `;openaccount` to open a bank account."
                )
            else:
                return await ctx.neutral(
                    f"{target.mention} doesn't have an account yet!"
                )

        wallet = record["wallet"] or 0
        bank   = record["bank"]   or 0
        total  = wallet + bank

        higher = await self.bot.db.fetchval(
            "SELECT COUNT(*) FROM economy WHERE (wallet + bank) > $1", total
        )
        rank = higher + 1
        total_players = await self.bot.db.fetchval("SELECT COUNT(*) FROM economy")

        if 10 <= rank % 100 <= 20:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(rank % 10, "th")
        ordinal_rank = f"{rank}{suffix}"

        description = (
            f"💰 **Wallet:** ${wallet}\n"
            f"🏛️ **Bank:**   ${bank}\n"
            f"🔢 **Total:**  ${total}\n\n"
        )

        embed = Embed(
            description=description,
            color=config.colors.primary,
        )
        embed.set_author(
            name=f"{target.display_name}'s Balance",
            url="https://www.youtube.com/watch?v=HbPr8sx1xaY&ab_channel=KingVon"
        )
        embed.set_footer(text=f"#{ordinal_rank} of {total_players}")

        await ctx.send(embed=embed)

async def setup(bot: Harvest):
    await bot.add_cog(Economy(bot))
