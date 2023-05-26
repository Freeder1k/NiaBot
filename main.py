import asyncio
import threading
from datetime import datetime

import discord
from dotenv import load_dotenv

import api.wynncraft.network
import api.wynncraft.wynnAPI
import commands.commandListener
import commands.prefixed.helpCommand
import scheduling
import storage.manager
import storage.playtimeData
import util

load_dotenv()
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)
start_time = datetime.now()

stopped = threading.Event()


@client.event
async def on_ready():
    await api.wynncraft.wynnAPI.init_sessions()

    util.log(f'Logged in as {client.user}')
    util.log(f'Guilds: {[g.name for g in client.guilds]}')

    scheduling.start_scheduling(client)

    await client.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(
            name=f"{await api.wynncraft.network.player_sum()} players play Wynncraft",
            type=discord.ActivityType.watching

        ))

    commands.commandListener.on_ready(client)

    commands.commandListener.register_commands(
        commands.prefixed.helpCommand.HelpCommand()
    )



@client.event
async def on_message(message: discord.Message):
    asyncio.create_task(commands.commandListener.on_message(message))


def main():
    print("\n  *:･ﾟ✧(=^･ω･^=)*:･ﾟ✧\n")

    storage.manager.create_database()

    client.run(os.environ.get("BOT_TOKEN"))


async def stop():
    stopped.set()
    scheduling.stop_scheduling()
    await client.close()
    await api.wynncraft.wynnAPI.close()
    storage.manager.close()


if __name__ == "__main__":
    try:
        main()
    finally:
        asyncio.run(stop())
