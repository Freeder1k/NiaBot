import asyncio
import threading
from datetime import datetime, timezone

import discord
from discord.ext import tasks
from dotenv import load_dotenv

import api.nasa
import api.rateLimit
import api.wynncraft
import api.wynncraft.network
import api.wynncraft.wynnAPI
import commands.commandListener
import commands.prefixed.helpCommand
import commands.prefixed.lastseenCommand
import commands.prefixed.playtimeCommand
import commands.prefixed.spaceCommand
import commands.prefixed.wandererCommand
import serverConfig
import storage.manager
import storage.playtimeData
import storage.playtimeData
import utils.logging

load_dotenv()
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)
start_time = datetime.now(timezone.utc)

stopped = threading.Event()


@client.event
async def on_ready():
    utils.logging.log(f"Logged in as {client.user}")
    utils.logging.log(f"Guilds: {[g.name for g in client.guilds]}")

    await serverConfig.load_server_configs()
    await storage.manager.init_database()
    await api.wynncraft.wynnAPI.init_sessions()
    await api.nasa.init_session()

    start_scheduling()

    commands.commandListener.on_ready(client)

    commands.commandListener.register_commands(
        commands.prefixed.helpCommand.HelpCommand(),
        commands.prefixed.playtimeCommand.PlaytimeCommand(),
        commands.prefixed.wandererCommand.WandererCommand(),
        commands.prefixed.lastseenCommand.LastSeenCommand(),
        commands.prefixed.spaceCommand.SpaceCommand(),
    )

    today = datetime.now(timezone.utc).date()
    if (await storage.playtimeData.get_first_date_after(today)) is None:
        await storage.playtimeData.update_playtimes()

    await client.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(
            name=f"{await api.wynncraft.network.player_sum()} players play Wynncraft",
            type=discord.ActivityType.watching,
        ),
    )


@client.event
async def on_message(message: discord.Message):
    asyncio.create_task(commands.commandListener.on_message(message))


@tasks.loop(minutes=1)
async def update_presence():
    await client.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(
            name=f"{await api.wynncraft.network.player_sum()} players play Wynncraft",
            type=discord.ActivityType.watching
        )
    )


def start_scheduling():
    api.rateLimit.update_ratelimits.start()
    storage.playtimeData.update_playtimes.start()
    update_presence.start(client)


def stop_scheduling():
    update_presence.cancel()
    storage.playtimeData.update_playtimes.cancel()
    api.rateLimit.update_ratelimits.cancel()


def main():
    print("\n  *:･ﾟ✧(=^･ω･^=)*:･ﾟ✧\n")

    client.run(os.getenv('BOT_TOKEN'))


async def stop():
    stopped.set()
    stop_scheduling()
    await client.close()
    await api.wynncraft.wynnAPI.close()
    await api.nasa.close()
    await storage.manager.close()


if __name__ == "__main__":
    try:
        main()
    finally:
        asyncio.run(stop())
