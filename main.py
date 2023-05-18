# This example requires the 'message_content' intent.
from datetime import datetime

import discord
from dotenv import load_dotenv

import util

load_dotenv()
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)
start_time = datetime.now()

def main():
    client.run(os.environ.get("BOT_TOKEN"))

@client.event
async def on_ready():
    util.log(f'Logged in as {client.user}')
    util.log(f'Guilds: {[g.name for g in client.guilds]}')
    await client.change_presence(status=discord.Status.online, activity=discord.Game("with a yarn ball"))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

if __name__ == "__main__":
    main()