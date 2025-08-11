import asyncio
from datetime import datetime, timezone, time

import aiohttp.client_exceptions
from discord.ext import tasks

import common.api
import common.api.wynncraft.v3.session
import common.api.wynncraft.v3.guild
import common.api.wynncraft.v3.player
import common.logging
from common.storage.playtimeData import set_playtime
from workers.queueWorker import QueueWorker
from workers.guildUpdater import get_active_guilds

_worker = QueueWorker(delay=0.5)

main_access_private_members = {}
online_status_private_members = {}

async def _update_member(uuid: str, guild_name: str):
    try:
        if common.api.wynncraft.v3.player.calculate_remaining_requests() < 10:
            wait_time = common.api.wynncraft.v3.player.ratelimit_reset_time()
            await asyncio.sleep(wait_time + 1)

        stats = await common.api.wynncraft.v3.player.stats(uuid)

        if stats.playtime is None:
            main_access_private_members[guild_name].add(uuid)
        else:
            await set_playtime(uuid, datetime.now(timezone.utc).date(), int(stats.playtime * 60))

        if stats.lastJoin is None:
            online_status_private_members[guild_name].add(uuid)
    except common.api.wynncraft.v3.player.UnknownPlayerException:
        common.logging.error(f'Failed to fetch stats for guild member with uuid {uuid}')


async def _update_guild(guild_name: str):
    guild = await common.api.wynncraft.v3.guild.stats(name=guild_name)

    main_access_private_members[guild_name] = set()
    online_status_private_members[guild_name] = set()

    for i, uuid in enumerate(guild.members.all.keys()):
        uuid = uuid.replace('-', '')
        if (i - 1) % 50 == 0:
            await asyncio.sleep(60)
        _worker.put(_update_member, uuid, guild_name)


@tasks.loop(time=time(hour=0, minute=0, tzinfo=timezone.utc), reconnect=True)
async def update_playtimes():
    try:
        if not _worker.started:
            _worker.start()
        for guild_name in get_active_guilds():
            await _update_guild(guild_name)
            await asyncio.sleep(60)
    except Exception as ex:
        await common.logging.error(exc_info=ex)
        raise ex


update_playtimes.add_exception_type(
    aiohttp.client_exceptions.ClientError,
    Exception
)
