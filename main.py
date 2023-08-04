import asyncio
import threading
import traceback
from datetime import datetime, timezone

import aiohttp.client_exceptions
import discord
from discord.ext import tasks
from dotenv import load_dotenv

import handlers.onlinePlayers
import handlers.rateLimit
import handlers.rateLimit
import wrappers.api.sessionManager
import wrappers.api.wynncraft.network
import handlers.commands.commandListener
import handlers.wynnGuild
from handlers import serverConfig
import wrappers.storage.manager
import wrappers.storage.playtimeData
import wrappers.storage.playtimeData
import wrappers.storage.usernameData
import utils.logging
from handlers.commands.prefixed import helpCommand, activityCommand, wandererCommand, seenCommand, spaceCommand, configCommand, \
    strikeCommand, strikesCommand, unstrikeCommand, evalCommand, playerCommand, guildCommand
from handlers.commands.prefixed import logCommand, playtimeCommand

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
            await wrappers.storage.manager.init_database()
            await wrappers.api.sessionManager.init_sessions()

            start_scheduling()

            handlers.commands.commandListener.on_ready(client)

            handlers.commands.commandListener.register_commands(
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
            if (await wrappers.storage.playtimeData.get_first_date_after(today)) is None:
                await wrappers.storage.playtimeData.update_playtimes()

            initialized = True
    except Exception as e:
        print(e)
        traceback.print_exc()


@client.event
async def on_message(message: discord.Message):
    asyncio.create_task(handlers.commands.commandListener.on_message(message))


@tasks.loop(minutes=1, reconnect=True)
async def update_presence():
    try:
        await client.change_presence(
            status=discord.Status.online,
            activity=discord.Activity(
                name=f"{await wrappers.api.wynncraft.network.player_count()} players play Wynncraft",
                type=discord.ActivityType.watching
            )
        )
    except Exception as ex:
        traceback.print_exc()
        raise ex


update_presence.add_exception_type(
    aiohttp.client_exceptions.ClientError,
    handlers.rateLimit.RateLimitException
)


def start_scheduling():
    handlers.rateLimit.ratelimit_updater.start()
    wrappers.storage.playtimeData.update_playtimes.start()
    update_presence.start()
    handlers.wynnGuild.update_guild.start(client=client)
    handlers.onlinePlayers.update_players.start(client=client)


def stop_scheduling():
    handlers.onlinePlayers.update_players.cancel()
    handlers.wynnGuild.update_guild.stop()
    update_presence.cancel()
    wrappers.storage.playtimeData.update_playtimes.cancel()
    handlers.rateLimit.ratelimit_updater.cancel()


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
    await wrappers.api.sessionManager.close()
    await wrappers.storage.manager.close()
    utils.logging.log("Stopped")


if __name__ == "__main__":
    main()
