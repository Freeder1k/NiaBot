import asyncio
from datetime import datetime, timezone, time

import aiohttp.client_exceptions
from discord.ext import tasks

import common.logging
import common.api
import common.api.wynncraft.v3.guild
import common.api.wynncraft.v3.player
from common.storage import set_playtime


async def _update_playtime(uuid: str):
    try:
        stats = await common.api.wynncraft.v3.player.stats(uuid)
        await set_playtime(stats.uuid, datetime.now(timezone.utc).date(), int(stats.playtime * 60))
    except common.api.wynncraft.v3.player.UnknownPlayerException:
        common.logging.error(f'Failed to fetch stats for guild member with uuid {uuid}')


@tasks.loop(time=time(hour=0, minute=0, tzinfo=timezone.utc), reconnect=True)
async def update_playtimes():
    try:
        guild = await common.api.wynncraft.v3.guild.stats(name=common.wrappers.botConfig.GUILD_NAME)

        await asyncio.gather(*(_update_playtime(uuid) for uuid in guild.members.all.keys()))

        await asyncio.sleep(120)

        guild2 = await common.api.wynncraft.v3.guild.stats(name=common.wrappers.botConfig.GUILD_NAME2)

        await asyncio.gather(*(_update_playtime(uuid) for uuid in guild2.members.all.keys()))
    except Exception as ex:
        await common.logging.error(exc_info=ex)
        raise ex


update_playtimes.add_exception_type(
    aiohttp.client_exceptions.ClientError,
    Exception
)
