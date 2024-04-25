import asyncio
from datetime import datetime, timezone, time

import aiohttp.client_exceptions
from discord.ext import tasks

import handlers.logging
import wrappers.api
import wrappers.api.wynncraft.v3.guild
import wrappers.api.wynncraft.v3.player
import wrappers.botConfig
from wrappers.storage.playtimeData import set_playtime


async def _update_playtime(uuid: str):
    try:
        stats = await wrappers.api.wynncraft.v3.player.stats(uuid)
        await set_playtime(stats.uuid, datetime.now(timezone.utc).date(), int(stats.playtime * 60))
    except wrappers.api.wynncraft.v3.player.UnknownPlayerException:
        handlers.logging.error(f'Failed to fetch stats for guild member with uuid {uuid}')


@tasks.loop(time=time(hour=0, minute=0, tzinfo=timezone.utc), reconnect=True)
async def update_playtimes():
    try:
        guild = await wrappers.api.wynncraft.v3.guild.stats(name=wrappers.botConfig.GUILD_NAME)

        await asyncio.gather(*(_update_playtime(uuid) for uuid in guild.members.all.keys()))
    except Exception as ex:
        await handlers.logging.error(exc_info=ex)
        raise ex


update_playtimes.add_exception_type(
    aiohttp.client_exceptions.ClientError,
    Exception
)
