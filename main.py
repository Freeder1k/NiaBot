import asyncio
from datetime import datetime, timezone

import aiohttp.client_exceptions
import discord
from discord.ext import tasks
from dotenv import load_dotenv

import handlers.commands.commandListener
import handlers.logging
import handlers.nerfuria.wynnGuild
import handlers.rateLimit
import handlers.rateLimit
import handlers.wynncraft.guilds
import handlers.wynncraft.onlinePlayers
import wrappers.api.sessionManager
import wrappers.api.wynncraft.network
import wrappers.storage.manager
import wrappers.storage.playtimeData
import wrappers.storage.playtimeData
import wrappers.storage.usernameData
from handlers import serverConfig
from handlers.commands.prefixed import helpCommand, activityCommand, wandererCommand, seenCommand, spaceCommand, \
    configCommand, \
    strikeCommand, strikesCommand, unstrikeCommand, evalCommand, playerCommand, guildCommand, shutdownCommand
from handlers.commands.prefixed import logCommand, playtimeCommand

load_dotenv()
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)
start_time = datetime.now(timezone.utc)

initialized = False


@client.event
async def on_ready():
    try:
        handlers.logging.init_logger(client)

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
                shutdownCommand.ShutdownCommand()
            )

            # await player.update_nia()
            today = datetime.now(timezone.utc).date()
            if (await wrappers.storage.playtimeData.get_first_date_after(today)) is None:
                await wrappers.storage.playtimeData.update_playtimes()

            initialized = True
            handlers.logging.log("Ready")
            handlers.logging.log(f"Logged in as {client.user}")
            handlers.logging.log(f"Guilds: {[g.name for g in client.guilds]}")
    except Exception as e:
        await handlers.logging.log_exception(e)
        await stop()


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
        await handlers.logging.log_exception(ex)
        raise ex


update_presence.add_exception_type(
    aiohttp.client_exceptions.ClientError,
    handlers.rateLimit.RateLimitException
)


def start_scheduling():
    wrappers.storage.playtimeData.update_playtimes.start()
    update_presence.start()
    handlers.nerfuria.wynnGuild.update_guild.start(client=client)
    handlers.wynncraft.onlinePlayers.update_players.start(client=client)
    handlers.wynncraft.guilds.update_guilds.start()


def stop_scheduling():
    handlers.wynncraft.guilds.update_guilds.stop()
    handlers.wynncraft.onlinePlayers.update_players.stop()
    handlers.nerfuria.wynnGuild.update_guild.stop()
    update_presence.stop()
    wrappers.storage.playtimeData.update_playtimes.stop()


def main():
    print("\n  *:･ﾟ✧(=^･ω･^=)*:･ﾟ✧\n")

    async def runner():
        async with client:
            await client.start(os.getenv('BOT_TOKEN'))

    try:
        handlers.logging.log("Booting up...")
        asyncio.run(runner())
    except (KeyboardInterrupt, SystemExit) as e:
        handlers.logging.log(f"{e.__class__.__name__}: {e}")
    except Exception as e:
        handlers.logging.log_exception(e, discord=False)
    finally:
        asyncio.run(stop())


async def stop():
    handlers.logging.log("Shutting down...")
    stop_scheduling()
    await client.close()
    await wrappers.api.sessionManager.close()
    await wrappers.storage.manager.close()
    handlers.logging.log("Stopped")


if __name__ == "__main__":
    main()
