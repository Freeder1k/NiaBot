import asyncio
from datetime import datetime, timezone, time

import aiohttp.client_exceptions
from discord.ext import tasks

import common.api
import common.api.wynncraft.v3.guild
import common.api.wynncraft.v3.player
import common.logging
from common.storage.playtimeData import set_playtime
from workers.queueWorker import QueueWorker

_worker = QueueWorker(delay=0.5)


async def _update_playtime(uuid: str):
    try:
        stats = await common.api.wynncraft.v3.player.stats(uuid)
        await set_playtime(stats.uuid, datetime.now(timezone.utc).date(), int(stats.playtime * 60))
    except common.api.wynncraft.v3.player.UnknownPlayerException:
        common.logging.error(f'Failed to fetch stats for guild member with uuid {uuid}')


async def _update_guild(guild_name: str):
    guild = await common.api.wynncraft.v3.guild.stats(name=guild_name)

    for i, uuid in enumerate(guild.members.all.keys()):
        if (i - 1) % 50 == 0:
            await asyncio.sleep(60)
        _worker.put(_update_playtime, uuid)


@tasks.loop(time=time(hour=0, minute=0, tzinfo=timezone.utc), reconnect=True)
async def update_playtimes():
    try:
        if not _worker.started:
            _worker.start()
        await _update_guild('Nerfuria')
        await asyncio.sleep(60)
        await _update_guild('Cat Cafe')
    except Exception as ex:
        await common.logging.error(exc_info=ex)
        raise ex


update_playtimes.add_exception_type(
    aiohttp.client_exceptions.ClientError,
    Exception
)
