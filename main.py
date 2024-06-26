import asyncio
import sys
from datetime import datetime, timezone
from typing import Final

import discord
from discord import app_commands
from dotenv import load_dotenv

import handlers.commands.commandListener
import handlers.logging
import handlers.nerfuria.logging
import handlers.nerfuria.logging2
import handlers.rateLimit
import handlers.rateLimit
import workers.guildUpdater
import workers.guildUpdater2
import workers.playtimeTracker
import workers.presenceUpdater
import workers.statTracker
import workers.usernameUpdater
import wrappers.api.sessionManager
import wrappers.api.wynncraft.v3.player
import wrappers.storage.manager
import wrappers.storage.playtimeData
import wrappers.storage.playtimeData
import wrappers.storage.usernameData
from handlers import serverConfig
from handlers.commands.hybrid import guildCommand, leaderboardCommand, warcountCommand, historyCommand, applyCommand
from handlers.commands.prefixed import helpCommand, activityCommand, wandererCommand, seenCommand, spaceCommand, \
    configCommand, strikeCommand, strikesCommand, unstrikeCommand, evalCommand, playerCommand, shutdownCommand, \
    logCommand, playtimeCommand

load_dotenv()
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)
client2 = discord.Client(intents=intents)

start_time: Final = datetime.now(timezone.utc)

tree = app_commands.CommandTree(client)
tree2 = app_commands.CommandTree(client2)

initialized = False
initialized2 = False

commands = [
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
    logCommand.LogCommand(),
    shutdownCommand.ShutdownCommand()
]
hybrid_commands = [
    guildCommand.GuildCommand(),
    leaderboardCommand.LeaderboardCommand(),
    warcountCommand.WarcountCommand(),
    historyCommand.HistoryCommand(),
    applyCommand.ApplyCommand()
]


@client.event
async def on_ready():
    try:
        await handlers.logging.init_discord_handler(client)
        handlers.nerfuria.logging.set_client(client)

        handlers.logging.info(f"Logged in as {client.user}")
        handlers.logging.info("Initializing...")

        global initialized
        if not initialized:
            await serverConfig.load_server_configs()
            await wrappers.storage.manager.init_database()
            await wrappers.api.sessionManager.init_sessions()

            start_workers()

            handlers.commands.commandListener.on_ready()

            handlers.commands.commandListener.register_commands(*commands, *hybrid_commands)

            today = datetime.now(timezone.utc).date()
            if (await wrappers.storage.playtimeData.get_first_date_after(today)) is None:
                await workers.playtimeTracker.update_playtimes()

            initialized = True

            handlers.logging.info("Syncing command tree...")
            for cmd in hybrid_commands:
                tree.add_command(cmd)

            await tree.sync()

            handlers.logging.info("Ready")
            handlers.logging.info(f"Guilds: {[g.name for g in client.guilds]}")
    except Exception as e:
        await handlers.logging.error(exc_info=e)
        await stop()

@client2.event
async def on_ready():
    try:
        handlers.nerfuria.logging2.set_client(client2)
        handlers.logging.info(f"Logged in as {client2.user}")
        handlers.logging.info("Initializing...")

        global initialized2
        if not initialized2:
            handlers.commands.commandListener.on_ready()

            handlers.commands.commandListener.register_commands(*commands, *hybrid_commands)

            initialized2 = True

            handlers.logging.info("Syncing command tree...")
            for cmd in hybrid_commands:
                tree2.add_command(cmd)

            await tree2.sync()

            handlers.logging.info("Ready")
            handlers.logging.info(f"Guilds: {[g.name for g in client2.guilds]}")
    except Exception as e:
        await handlers.logging.error(exc_info=e)
        await stop()



@client.event
async def on_message(message: discord.Message):
    asyncio.create_task(handlers.commands.commandListener.on_message(message, client))

@client2.event
async def on_message(message: discord.Message):
    asyncio.create_task(handlers.commands.commandListener.on_message(message, client2))


def start_workers():
    workers.playtimeTracker.update_playtimes.start()
    workers.presenceUpdater.update_presence.start(client=client)
    workers.guildUpdater.update_guild.start()
    workers.guildUpdater2.update_guild.start()
    workers.usernameUpdater.start()
    workers.statTracker.start()


def stop_workers():
    workers.statTracker.stop()
    workers.usernameUpdater.stop()
    workers.guildUpdater2.update_guild.stop()
    workers.guildUpdater.update_guild.stop()
    workers.presenceUpdater.update_presence.stop()
    workers.playtimeTracker.update_playtimes.stop()


def main():
    print("\n  *:･ﾟ✧(=^･ω･^=)*:･ﾟ✧\n")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def runner():
        async with client:
            await client.start(os.getenv('BOT_TOKEN'))

    async def runner2():
        if os.getenv('BOT_TOKEN2') is not None:
            async with client2:
                await client2.start(os.getenv('BOT_TOKEN2'))

    async def main_runner():
        runners = [runner(), runner2()]
        await asyncio.gather(*runners, return_exceptions=True)

    try:
        handlers.logging.info("Booting up...")
        asyncio.run(main_runner())
    except (KeyboardInterrupt, SystemExit) as e:
        handlers.logging.info(e.__class__.__name__)
    except Exception as e:
        handlers.logging.error(exc_info=e)
    finally:
        asyncio.run(stop())
        handlers.logging.info("Stopped")


async def stop():
    handlers.logging.info("Shutting down...")
    stop_workers()

    await client.close()
    await client2.close()
    await wrappers.api.sessionManager.close()
    await wrappers.storage.manager.close()


if __name__ == "__main__":
    main()
