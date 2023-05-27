import asyncio
from datetime import time, timezone, datetime

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
    nia = await api.wynncraft.guild.stats("Nerfuria")
    today = datetime.now(timezone.utc).date()

    res: list[api.wynncraft.player.Stats] = await asyncio.gather(
        *(api.wynncraft.player.stats(member.uuid) for member in nia.members))

    await asyncio.gather(*(storage.playtimeData.set_playtime(stats.uuid, today, stats.meta.playtime) for stats in res))


@tasks.loop(minutes=1)
async def update_presence(client: Client):
    await client.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(
            name=f"{await api.wynncraft.network.player_sum()} players play Wynncraft",
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
