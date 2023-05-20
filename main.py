# This example requires the 'message_content' intent.
import threading
import time
from datetime import datetime, timezone, timedelta, date

import discord
from dotenv import load_dotenv
import schedule

import util
import wynncraft.network
import wynncraft.wynnAPI
import wynncraft.player
import wynncraft.rateLimit

load_dotenv()
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)
start_time = datetime.now()

stopped = threading.Event()


def main():
    client.run(os.environ.get("BOT_TOKEN"))

def register_schedulers():
    # Register scheduler actions
    schedule.every().minute.at(":00").do(wynncraft.rateLimit.update_ratelimits)

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
    await client.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(
            name=f"{wynncraft.network.player_sum()} players play Wynncraft",
            type=discord.ActivityType.watching
        ))

    register_schedulers()


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')


if __name__ == "__main__":
    try:
        main()
    finally:
        stopped.set()
