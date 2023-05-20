# This example requires the 'message_content' intent.
import time
from datetime import datetime, timezone, timedelta, date

import discord
from dotenv import load_dotenv

from repeatingScheduler import RepeatingScheduler
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


def main():
    client.run(os.environ.get("BOT_TOKEN"))

def register_schedulers():
    now = datetime.now(timezone.utc)

    next_day = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    daily_scheduler = RepeatingScheduler(next_day, timedelta(days=1))

    next_minute = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
    minute_scheduler = RepeatingScheduler(next_minute, timedelta(minutes=1))\
        .register_action(wynncraft.rateLimit.update_ratelimits())


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
    main()
