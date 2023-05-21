import asyncio
import threading
from datetime import datetime

import discord
from dotenv import load_dotenv

import api.wynncraft.guild
import api.wynncraft.network
import api.wynncraft.player
import commands.prefixed.helpCommand
import scheduling
import storage.playtimeData
import util
from commands import commandListener

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
    commandListener.on_ready(client)

    util.log(f'Logged in as {client.user}')
    util.log(f'Guilds: {[g.name for g in client.guilds]}')

    storage.playtimeData.load_data()
    scheduling.start_scheduling(client)

    await client.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(
            name=f"{api.wynncraft.network.player_sum()} players play Wynncraft",
            type=discord.ActivityType.watching

        ))

    commandListener.register_commands(
        commands.prefixed.helpCommand.HelpCommand()
    )


@client.event
async def on_message(message: discord.Message):
    commandListener.on_message(message)


def main():
    client.run(os.environ.get("BOT_TOKEN"))


if __name__ == "__main__":
    try:
        main()
    finally:
        stopped.set()
        scheduling.stop_scheduling()
        asyncio.run(client.close())
