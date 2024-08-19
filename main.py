import asyncio
from datetime import datetime, timezone
from typing import Final

import discord
from discord import app_commands
from dotenv import load_dotenv

import common.commands.commandListener
import common.logging
import common.logging
import common.logging2
import workers.guildUpdater
import workers.guildUpdater2
import workers.playtimeTracker
import workers.presenceUpdater
import workers.statTracker
import workers.usernameUpdater
import common.storage.playtimeData
from common.storage import serverConfig
from common.commands.hybrid import applyCommand, guildCommand, leaderboardCommand, historyCommand, warcountCommand
from common.commands import helpCommand, seenCommand, strikeCommand, strikesCommand, shutdownCommand, \
    logCommand, playerCommand, evalCommand
from common.commands.prefixed import playtimeCommand, unstrikeCommand, configCommand, activityCommand, spaceCommand, \
    wandererCommand

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
        await common.logging.init_discord_handler(client)
        common.logging.set_client(client)

        common.logging.info(f"Logged in as {client.user}")
        common.logging.info("Initializing...")

        global initialized
        if not initialized:
            await serverConfig.load_server_configs()
            await common.wrappers.storage.manager.init_database()
            await common.wrappers.api.sessionManager.init_sessions()

            start_workers()

            common.commands.commandListener.on_ready()

            common.commands.commandListener.register_commands(*commands, *hybrid_commands)

            today = datetime.now(timezone.utc).date()
            if (await common.storage.playtimeData.get_first_date_after(today)) is None:
                await workers.playtimeTracker.update_playtimes()

            initialized = True

            common.logging.info("Syncing command tree...")
            for cmd in hybrid_commands:
                tree.add_command(cmd)

            await tree.sync()

            common.logging.info("Ready")
            common.logging.info(f"Guilds: {[g.name for g in client.guilds]}")
    except Exception as e:
        await common.logging.error(exc_info=e)
        await stop()

@client2.event
async def on_ready():
    try:
        common.logging2.set_client(client2)
        common.logging.info(f"Logged in as {client2.user}")
        common.logging.info("Initializing...")

        global initialized2
        if not initialized2:
            common.commands.commandListener.on_ready()

            common.commands.commandListener.register_commands(*commands, *hybrid_commands)

            initialized2 = True

            common.logging.info("Syncing command tree...")
            for cmd in hybrid_commands:
                tree2.add_command(cmd)

            await tree2.sync()

            common.logging.info("Ready")
            common.logging.info(f"Guilds: {[g.name for g in client2.guilds]}")
    except Exception as e:
        await common.logging.error(exc_info=e)
        await stop()



@client.event
async def on_message(message: discord.Message):
    asyncio.create_task(common.commands.commandListener.on_message(message, client))

@client2.event
async def on_message(message: discord.Message):
    asyncio.create_task(common.commands.commandListener.on_message(message, client2))


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
        common.logging.info("Booting up...")
        asyncio.run(main_runner())
    except (KeyboardInterrupt, SystemExit) as e:
        common.logging.info(e.__class__.__name__)
    except Exception as e:
        common.logging.error(exc_info=e)
    finally:
        asyncio.run(stop())
        common.logging.info("Stopped")


async def stop():
    common.logging.info("Shutting down...")
    stop_workers()

    await client.close()
    await client2.close()
    await common.wrappers.api.sessionManager.close()
    await common.wrappers.storage.manager.close()


if __name__ == "__main__":
    main()
