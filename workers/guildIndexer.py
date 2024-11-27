from discord.ext import tasks

import common.api.wynncraft.v3.guild
import common.logging
from common.utils.misc import create_inverted_index

_index = {}


async def _create_inverted_guild_index():
    guilds = await common.api.wynncraft.v3.guild.list_guilds()
    guilds = [g.tag for g in guilds] + [g.name for g in guilds]

    return create_inverted_index(guilds, ignore_case=True, max_key_len=30, max_bucket_len=25)


def get_index():
    return _index


@tasks.loop(seconds=3601, reconnect=True)
async def update_index():
    try:
        global _index
        _index = await _create_inverted_guild_index()
    except Exception as ex:
        await common.logging.error(exc_info=ex)
        raise ex


update_index.add_exception_type(Exception)
