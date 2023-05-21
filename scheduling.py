import asyncio
import concurrent.futures
from datetime import datetime, time, timezone

import discord
from discord import Client
from discord.ext import tasks

import api.wynncraft.guild
import api.wynncraft.network
import api.wynncraft.player
import storage.playtimeData
from api import rateLimit

time0 = time(hour=0, minute=0, tzinfo=timezone.utc)


@tasks.loop(time=time0)
async def update_playtimes():
    # TODO async api calls
    nia = api.wynncraft.guild.stats("Nerfuria")
    today = datetime.now()

    loop = asyncio.get_running_loop()

    with concurrent.futures.ThreadPoolExecutor() as pool:
        futures = []
        for member in nia.members:
            futures.append(loop.run_in_executor(pool, api.wynncraft.player.stats, (member.uuid,)))
        for future in futures:
            res = await future
            playtime = res.meta.playtime
            storage.playtimeData.set_playtime(member.uuid, today, playtime)

        loop.run_in_executor(pool, storage.playtimeData.store_data)


@tasks.loop(minutes=1)
async def update_presence(client: Client):
    await client.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(
            name=f"{api.wynncraft.network.player_sum()} players play Wynncraft",
            type=discord.ActivityType.watching
        )
    )


@tasks.loop(minutes=1)
async def update_ratelimits():
    rateLimit.update_ratelimits()


def start_scheduling(client: Client):
    update_playtimes.start()
    update_presence.start(client)
    update_ratelimits.start()


def stop_scheduling():
    update_playtimes.cancel()
    update_presence.cancel()
    update_ratelimits.cancel()
