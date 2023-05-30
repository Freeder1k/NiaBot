import asyncio
import threading
from datetime import datetime, timezone

import discord
from dotenv import load_dotenv

import api.nasa
import api.wynncraft.network
import api.wynncraft.wynnAPI
import commands.commandListener
import commands.prefixed.helpCommand
import commands.prefixed.lastseenCommand
import commands.prefixed.playtimeCommand
import commands.prefixed.spaceCommand
import commands.prefixed.wandererCommand
import scheduling
import storage.manager
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

    await storage.manager.init_database()
    await api.wynncraft.wynnAPI.init_sessions()
    await api.nasa.init_session()

    scheduling.start_scheduling(client)

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
        await scheduling.update_playtimes()

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


def main():
    print("\n  *:･ﾟ✧(=^･ω･^=)*:･ﾟ✧\n")

    client.run(os.getenv('BOT_TOKEN'))


async def stop():
    stopped.set()
    scheduling.stop_scheduling()
    await client.close()
    await api.wynncraft.wynnAPI.close()
    await api.nasa.close()
    await storage.manager.close()


if __name__ == "__main__":
    try:
        main()
    finally:
        asyncio.run(stop())
