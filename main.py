import asyncio
import threading
import traceback
from datetime import datetime, timezone

import aiohttp.client_exceptions
import discord
from discord.ext import tasks
from dotenv import load_dotenv

import api.minecraft
import api.nasa
import api.rateLimit
import api.rateLimit
import api.sessionManager
import api.wynncraft
import api.wynncraft.network
import api.wynncraft.wynnAPI
import commands.commandListener
import nerfuria.guild
import player
import serverConfig
import storage.manager
import storage.playtimeData
import storage.playtimeData
import storage.usernameData
import utils.logging
from commands.prefixed import helpCommand, activityCommand, wandererCommand, seenCommand, spaceCommand, configCommand, \
    strikeCommand, strikesCommand, unstrikeCommand, evalCommand, playerCommand, playtimeCommand, guildCommand, \
    logCommand

load_dotenv()
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)
start_time = datetime.now(timezone.utc)

stopped = threading.Event()
initialized = False


@client.event
async def on_ready():
    try:
        utils.logging.log("Ready")
        utils.logging.log(f"Logged in as {client.user}")
        utils.logging.log(f"Guilds: {[g.name for g in client.guilds]}")

        global initialized
        if not initialized:
            await serverConfig.load_server_configs()
            await storage.manager.init_database()
            await api.sessionManager.init_sessions()

            start_scheduling()

            commands.commandListener.on_ready(client)

            commands.commandListener.register_commands(
                helpCommand.HelpCommand(),
                activityCommand.ActivityCommand(),
                wandererCommand.WandererCommand(),
                seenCommand.SeenCommand(),
                spaceCommand.SpaceCommand(),
                configCommand.ConfigCommand(),
                strikeCommand.StrikeCommand(),
                strikesCommand.StrikesCommand(),
                unstrikeCommand.UnstrikeCommand(),
                evalCommand.EvalCommand(),
                playerCommand.PlayerCommand(),
                playtimeCommand.PlaytimeCommand(),
                guildCommand.GuildCommand(),
                logCommand.LogCommand(),
            )

            # await player.update_nia()
            today = datetime.now(timezone.utc).date()
            if (await storage.playtimeData.get_first_date_after(today)) is None:
                await storage.playtimeData.update_playtimes()

            initialized = True
    except Exception as e:
        print(e)
        traceback.print_exc()


@client.event
async def on_message(message: discord.Message):
    asyncio.create_task(commands.commandListener.on_message(message))


@tasks.loop(minutes=1, reconnect=True)
async def update_presence():
    try:
        await client.change_presence(
            status=discord.Status.online,
            activity=discord.Activity(
                name=f"{await api.wynncraft.network.player_sum()} players play Wynncraft",
                type=discord.ActivityType.watching
            )
        )
    except Exception as ex:
        traceback.print_exc()
        raise ex


update_presence.add_exception_type(
    aiohttp.client_exceptions.ClientError,
    api.rateLimit.RateLimitException
)


def start_scheduling():
    api.rateLimit.ratelimit_updater.start()
    storage.playtimeData.update_playtimes.start()
    update_presence.start()
    nerfuria.guild.update_guild.start(client=client)
    player.update_players.start(client=client)


def stop_scheduling():
    player.update_players.cancel()
    nerfuria.guild.update_guild.stop()
    update_presence.cancel()
    storage.playtimeData.update_playtimes.cancel()
    api.rateLimit.ratelimit_updater.cancel()


def main():
    print("\n  *:･ﾟ✧(=^･ω･^=)*:･ﾟ✧\n")

    async def runner():
        async with client:
            await client.start(os.getenv('BOT_TOKEN'))

    try:
        asyncio.run(runner())
    except:
        asyncio.run(stop())
        return


async def stop():
    stopped.set()
    stop_scheduling()
    await client.close()
    await api.sessionManager.close()
    await storage.manager.close()
    utils.logging.log("Stopped")


if __name__ == "__main__":
    main()
