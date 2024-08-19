import aiohttp.client_exceptions
import discord
from discord import Client
from discord.ext import tasks

import common.logging
import common.api.rateLimit
import common.api.wynncraft.v3.player


@tasks.loop(seconds=61, reconnect=True)
async def update_presence(client: Client):
    try:
        await client.change_presence(
            status=discord.Status.online,
            activity=discord.Activity(
                name=f"{await common.api.wynncraft.v3.player.player_count()} players play Wynncraft",
                type=discord.ActivityType.watching
            )
        )
    except Exception as ex:
        await common.logging.error(exc_info=ex)
        raise ex


update_presence.add_exception_type(
    aiohttp.client_exceptions.ClientError,
    common.api.rateLimit.RateLimitException,
    Exception
)
