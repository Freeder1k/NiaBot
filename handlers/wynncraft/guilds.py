import asyncio

import aiohttp.client_exceptions
from discord.ext import tasks

import handlers.logging
import handlers.logging
import handlers.rateLimit
import wrappers.api.wynncraft.guild
import wrappers.storage.guildData


async def _get_and_store_from_api(name: str):
    g = await wrappers.api.wynncraft.guild.stats(name)
    if g is None:
        return
    await wrappers.storage.guildData.put(g.name, g.prefix)


@tasks.loop(minutes=21, reconnect=True)
async def update_guilds():
    try:
        guild_list = set(await wrappers.api.wynncraft.guild.guild_list())
        known_guilds = set(await wrappers.storage.guildData.guild_list())
        new_guilds = guild_list - known_guilds
        deleted_guilds = known_guilds - guild_list

        if new_guilds:
            handlers.logging.log_debug(f"Adding {min(600, len(new_guilds))} new guilds.")
            handlers.logging.log_debug(new_guilds)
        if deleted_guilds:
            handlers.logging.log_debug(f"Removing {len(deleted_guilds)} guilds.")
            handlers.logging.log_debug(deleted_guilds)

        await asyncio.gather(*(_get_and_store_from_api(gname) for gname in list(new_guilds)[:600]))
        await wrappers.storage.guildData.remove_many(names=list(deleted_guilds))

    except Exception as ex:
        await handlers.logging.log_exception(ex)
        raise ex


update_guilds.add_exception_type(
    aiohttp.client_exceptions.ClientError,
    handlers.rateLimit.RateLimitException
)
