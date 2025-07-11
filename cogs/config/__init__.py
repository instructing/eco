from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import Harvest


async def setup(bot: "Harvest") -> None:
    from .config import Config

    await bot.add_cog(Config(bot))
