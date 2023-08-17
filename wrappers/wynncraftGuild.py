from async_lru import alru_cache

import wrappers.api.minecraft
import wrappers.api.wynncraft.guild
import wrappers.api.wynncraft.guild
import wrappers.api.wynncraft.network
import wrappers.storage.guildData
import wrappers.storage.usernameData
from niatypes.dataTypes import WynncraftGuild


@alru_cache(ttl=60)
async def get_guild(*, name: str = None, tag: str = None) -> WynncraftGuild | None:
    return await wrappers.storage.guildData.get_guild(name=name, tag=tag)


@alru_cache(ttl=60)
async def find_guilds(s: str) -> tuple[WynncraftGuild]:
    return await wrappers.storage.guildData.find_guilds(s)


async def get_guild_stats(*, name: str = None, tag: str = None) -> wrappers.api.wynncraft.guild.Stats | None:
    if name is None:
        name = (await get_guild(tag=tag)).name
    elif tag is not None:
        raise TypeError("Exactly one argument (either tag or name) must be provided.")
    return await wrappers.api.wynncraft.guild.stats(name)
