from typing import TYPE_CHECKING, Optional, Any, cast

from aiohttp import ClientSession

from discord import (
    Guild,
    Member,
    Message,
    TextChannel,
    Thread,
    VoiceChannel,
    Colour,
    Embed,
    HTTPException,
)
from discord.ext.commands import Command
from discord.ext.commands import Context as OriginalContext

from tools.client.database import Database, Settings
from config import config

if TYPE_CHECKING:
    from main import Harvest


class Context(OriginalContext):
    bot: "Harvest"
    guild: Guild
    author: Member
    channel: VoiceChannel | TextChannel | Thread
    command: Command[Any, ..., Any]
    settings: Settings
    response: Optional[Message] = None

    @property
    def session(self) -> ClientSession:
        return self.bot.session

    @property
    def db(self) -> Database:
        return self.bot.database

    @property
    def color(self) -> Colour:
        return Colour.dark_embed()

    async def send(self, *args, **kwargs) -> Message:
        if kwargs.pop("no_reference", False):
            reference = None
        else:
            reference = kwargs.pop("reference", self.message)

        patch = cast(
            Optional[Message],
            kwargs.pop("patch", None),
        )

        embed = cast(
            Optional[Embed],
            kwargs.get("embed"),
        )
        if embed and not embed.color:
            embed.color = self.color

        if args:
            kwargs["content"] = args[0]
            args = ()

        if file := kwargs.pop("file", None):
            kwargs["files"] = [file]

        if kwargs.get("view") is None:
            kwargs.pop("view", None)

        if patch:
            self.response = await patch.edit(**kwargs)
        else:
            if reference:
                kwargs["reference"] = reference

            try:
                self.response = await super().send(*args, **kwargs)
            except HTTPException:
                kwargs.pop("reference", None)
                self.response = await super().send(*args, **kwargs)

        return self.response

    async def neutral(
        self,
        *args: str,
        **kwargs,
    ) -> Message:
        """
        Send a neutral embed.
        """

        embed = Embed(
            description="\n".join(
                ("" if len(args) == 1 or index == len(args) - 1 else "") + str(arg)
                for index, arg in enumerate(args)
            ),
            color=config.colors.primary,  # color=kwargs.pop("color", None),
        )
        return await self.send(embed=embed, **kwargs)

    async def approve(
        self,
        *args: str,
        **kwargs,
    ) -> Message:
        """
        Send a success embed.
        """

        embed = Embed(
            description="\n".join(
                ("" if len(args) == 1 or index == len(args) - 1 else "") + str(arg)
                for index, arg in enumerate(args)
            ),
            color=config.colors.primary,  # color=kwargs.pop("color", None),
        )
        return await self.send(embed=embed, **kwargs)

    async def warn(
        self,
        *args: str,
        **kwargs,
    ) -> Message:
        """
        Send an error embed.
        """

        embed = Embed(
            description="\n".join(
                ("" if len(args) == 1 or index == len(args) - 1 else "") + str(arg)
                for index, arg in enumerate(args)
            ),
            color=config.colors.primary,  # color=kwargs.pop("color", None),
        )
        return await self.send(embed=embed, **kwargs)
