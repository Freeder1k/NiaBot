import asyncio
from datetime import datetime, timezone

from common.botInstance import BotInstance

import common.api.sessionManager
import common.logging
import common.storage.manager
import common.storage.playtimeData
import workers.guildUpdater
import workers.playtimeTracker
import workers.presenceUpdater
import workers.statTracker
import workers.usernameUpdater
import workers.guildIndexer
from common.commands.hybrid import *
from common.commands.prefixed import *
from dotenv import load_dotenv

load_dotenv()

def add_commands(bot):
    bot.add_commands(
        HelpCommand(bot),
        GuildCommand(bot),
        PlayerCommand(bot),
        HistoryCommand(bot),
        SpaceCommand(bot),
    )
    bot.add_commands(
        ActivityCommand(),
        ConfigCommand(),
        EvalCommand(),
        PlaytimeCommand(),
        SeenCommand(),
        ShutdownCommand(),
    )

class Niabot(BotInstance):
    def __init__(self):
        super().__init__("niabot")
        add_commands(self)

class MewoBot(BotInstance):
    def __init__(self):
        super().__init__("mewobot")
        add_commands(self)


def start_workers():
    common.logging.info("Starting workers...")
    workers.playtimeTracker.update_playtimes.start()
    workers.presenceUpdater.update_presence.start()
    workers.guildUpdater.guild_updater.start()
    workers.usernameUpdater.start()
    workers.statTracker.start()
    workers.guildIndexer.update_index.start()
    common.logging.info("Guild indexer started.")


def stop_workers():
    common.logging.info("Stopping workers...")
    workers.guildIndexer.update_index.stop()
    workers.statTracker.stop()
    workers.usernameUpdater.stop()
    workers.guildUpdater.guild_updater.stop()
    workers.presenceUpdater.update_presence.stop()
    workers.playtimeTracker.update_playtimes.stop()


async def main():
    print("\n  *:･ﾟ✧(=^･ω･^=)*:･ﾟ✧\n")

    niabot = Niabot()
    mewobot = MewoBot()

    try:
        common.logging.info("Booting up...")

        await common.storage.manager.init_database()
        await common.api.sessionManager.init_sessions()

        async with asyncio.TaskGroup() as tg:
            await niabot.login(niabot.config.BOT_TOKEN)
            await mewobot.login(mewobot.config.BOT_TOKEN)
            tg.create_task(niabot.connect())
            tg.create_task(mewobot.connect())

            await niabot.wait_until_ready()
            await common.logging.init_discord_handler(niabot)

            await mewobot.wait_until_ready()

            start_workers()

            today = datetime.now(timezone.utc).date()
            if (await common.storage.playtimeData.get_first_date_after(today)) is None:
                await workers.playtimeTracker.update_playtimes()

    except (KeyboardInterrupt, SystemExit, asyncio.CancelledError) as e:
        common.logging.info("Stopped:", e.__class__.__name__)
    except Exception as e:
        common.logging.error(exc_info=e)
    finally:
        common.logging.info("Shutting down...")
        stop_workers()

        await mewobot.close()
        await niabot.close()
        await common.api.sessionManager.close()
        await common.storage.manager.close()
        common.logging.info("o/")


if __name__ == "__main__":
    asyncio.run(main())
