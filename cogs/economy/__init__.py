from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import Harvest


async def setup(bot: "Harvest") -> None:
    from .economy import Economy

    await bot.add_cog(Economy(bot))
