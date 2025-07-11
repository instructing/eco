from __future__ import annotations
from typing import TYPE_CHECKING
from contextlib import suppress
from abc import ABC

from discord import (
    Color,
    Embed,
    Emoji,
    Interaction,
    PartialEmoji,
    ButtonStyle,
    WebhookMessage,
    InteractionResponded,
)
from discord.ext.commands import Cog
from discord.ui import Button as OriginalButton
from discord.ui import View as OriginalView
from discord.ui import Modal as OriginalModal
from discord.interactions import Interaction

if TYPE_CHECKING:
    from main import Harvest
    from tools.client import Context


class CompositeMetaClass(type(Cog), ABC.__class__):
    """
    This allows the metaclass used for proper type detection to
    coexist with discord.py's metaclass
    """

    pass


class MixinMeta(Cog, ABC, metaclass=CompositeMetaClass):
    """
    This is the base class for all mixins.
    With well-defined mixins, we can avoid the need for multiple inheritance.
    """

    bot: "Harvest"


class View(OriginalView):
    ctx: Context

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def callback(self, interaction: Interaction, button: OriginalButton):
        raise NotImplementedError

    async def disable_buttons(self) -> None:
        for child in self.children:
            child.disabled = True  # type: ignore

    async def on_timeout(self) -> None:
        self.stop()

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user != self.ctx.author:
            embed = Embed(
                description=f"This is {self.ctx.author.mention}'s selection!",
                color=Color.dark_embed(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        return interaction.user == self.ctx.author


class Button(OriginalButton):
    view: View
    custom_id: str

    def __init__(
        self,
        *,
        style: ButtonStyle = ButtonStyle.gray,
        label: str | None = None,
        disabled: bool = False,
        custom_id: str | None = None,
        url: str | None = None,
        emoji: str | Emoji | PartialEmoji | None = None,
        row: int | None = None,
    ):
        super().__init__(
            style=style,
            label=label,
            disabled=disabled,
            custom_id=custom_id,
            url=url,
            emoji=emoji,
            row=row,
        )

    async def callback(self, interaction: Interaction):
        await self.view.callback(interaction, self)


class Modal(OriginalModal):
    ctx: Context

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def callback(self, interaction: Interaction, button: OriginalButton):
        raise NotImplementedError

    async def disable_buttons(self) -> None:
        for child in self.children:
            child.disabled = True  # type: ignore

    async def on_timeout(self) -> None:
        self.stop()

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user != self.ctx.author:
            embed = Embed(
                description=f"This is {self.ctx.author.mention}'s modal!",
                color=Color.dark_embed(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        return interaction.user == self.ctx.author


class Interaction(Interaction):
    """Just adding basic methods to help manage embeds"""

    async def neutral(
        self,
        *args: str,
        **kwargs,
    ) -> WebhookMessage:
        """
        Send a neutral embed.
        """

        with suppress(InteractionResponded):
            await self.response.defer()

        embed = Embed(
            description="\n".join(
                ("" if len(args) == 1 or index == len(args) - 1 else "") + str(arg)
                for index, arg in enumerate(args)
            ),
            color=kwargs.pop("color", None),
        )
        return await self.followup.send(embed=embed, **kwargs)

    async def warn(
        self,
        *args: str,
        **kwargs,
    ) -> WebhookMessage:
        """
        Send an error embed.
        """

        with suppress(InteractionResponded):
            await self.response.defer()

        embed = Embed(
            description="\n".join(
                ("" if len(args) == 1 or index == len(args) - 1 else "") + str(arg)
                for index, arg in enumerate(args)
            ),
            color=kwargs.pop("color", None),
        )
        return await self.followup.send(embed=embed, **kwargs)

    async def approve(
        self,
        *args: str,
        **kwargs,
    ) -> WebhookMessage:
        """
        Send a success embed.
        """

        with suppress(InteractionResponded):
            await self.response.defer()

        embed = Embed(
            description="\n".join(
                ("" if len(args) == 1 or index == len(args) - 1 else "") + str(arg)
                for index, arg in enumerate(args)
            ),
            color=kwargs.pop("color", None),
        )
        return await self.followup.send(embed=embed, **kwargs)


__all__ = (
    "MixinMeta",
    "CompositeMetaClass",
    "View",
    "Button",
    "Interaction",
    "Modal",
)
