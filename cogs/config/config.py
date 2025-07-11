from __future__ import annotations

from discord import Message
from discord.ext.commands import Cog, group, has_permissions

from main import Harvest
from tools.client.context import Context

from config import config


class Config(Cog):
    def __init__(self, bot: Harvest):
        self.bot = bot

    @group(invoke_without_command=True)
    async def prefix(self, ctx: Context) -> Message:
        """View the current guild prefixes."""

        prefixes = ctx.settings.prefixes or [config.client.prefix]

        return await ctx.neutral(
            f"The current prefixes are: {', '.join(f'`{prefix}`' for prefix in prefixes)}"
            if len(prefixes) > 1
            else f"The current prefix is `{prefixes[0]}`"
        )

    @prefix.command(name="set")
    @has_permissions(manage_guild=True)
    async def prefix_set(self, ctx: Context, prefix: str) -> Message:
        """Set the guild prefix."""

        if not prefix:
            return await ctx.warn("You must provide a prefix to set!")

        # TODO: Add a prompt to context.

        await ctx.settings.update(prefixes=[prefix])
        return await ctx.approve(f"The prefix has been set to `{prefix}`")

    @prefix.command(name="add")
    @has_permissions(manage_guild=True)
    async def prefix_add(self, ctx: Context, prefix: str) -> Message:
        """Add a prefix to the guild prefixes."""

        if not prefix:
            return await ctx.approve("You must provide a prefix to add!")

        elif prefix in ctx.settings.prefixes:
            return await ctx.warn("That prefix is already in use!")

        await ctx.settings.update(prefixes=[*ctx.settings.prefixes, prefix])
        return await ctx.approve(f"The prefix `{prefix}` has been added")

    @prefix.command(name="remove")
    @has_permissions(manage_guild=True)
    async def prefix_remove(self, ctx: Context, prefix: str) -> Message:
        """Remove a prefix from the guild prefixes."""

        if not prefix:
            return await ctx.warn("You must provide a prefix to remove!")

        elif prefix not in ctx.settings.prefixes:
            return await ctx.warn("That prefix is not in use!")

        await ctx.settings.update(
            prefixes=[p for p in ctx.settings.prefixes if p != prefix]
        )
        return await ctx.approve(f"The prefix `{prefix}` has been removed")

    @prefix.command(name="reset")
    @has_permissions(manage_guild=True)
    async def prefix_reset(self, ctx: Context) -> Message:
        """Reset the guild prefixes."""

        await ctx.settings.update(prefixes=[])
        return await ctx.approve("The prefixes have been reset to the default `;`")
