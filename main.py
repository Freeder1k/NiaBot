# This example requires the 'message_content' intent.
import asyncio
import threading
import time
from datetime import datetime

import discord
import schedule
from dotenv import load_dotenv

import util
import wynncraft.network
import wynncraft.player
import wynncraft.rateLimit
import wynncraft.wynnAPI

load_dotenv()
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)
start_time = datetime.now()

stopped = threading.Event()


def update_presence():
    asyncio.run(client.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(
            name=f"{wynncraft.network.player_sum()} players play Wynncraft",
            type=discord.ActivityType.watching
        )
    ))


def register_schedulers():
    # Register scheduler actions
    schedule.every().minute.at(":00").do(wynncraft.rateLimit.update_ratelimits)
    schedule.every().minute.at(":00").do(update_presence)

    # Set up a thread for the scheduler to run on in the background
    class ScheduleThread(threading.Thread):
        @classmethod
        def run(cls):
            while not stopped.is_set():
                schedule.run_pending()
                time.sleep(schedule.idle_seconds())

    ScheduleThread().start()


@client.event
async def on_ready():
    util.log(f'Logged in as {client.user}')
    util.log(f'Guilds: {[g.name for g in client.guilds]}')

    register_schedulers()

    await client.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(
            name=f"{wynncraft.network.player_sum()} players play Wynncraft",
            type=discord.ActivityType.watching

        ))


@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')


def main():
    client.run(os.environ.get("BOT_TOKEN"))


if __name__ == "__main__":
    try:
        main()
    finally:
        asyncio.run(client.close())
        stopped.set()
