import asyncio

import discord
from discord import app_commands

import common.logging
import workers.guildUpdater
import workers.presenceUpdater
from common.botConfig import BotConfig
from common.commands import command, messageParser
from common.guildLogger import GuildLogger
from common.storage.serverConfigs import ServerConfigs


class BotInstance(discord.Client):
    def __init__(self, bot_config: BotConfig):
        """
        Crate a new bot instance. This is the main class that handles the bot's functionality.

        :param bot_config: The bot's configuration.
        """
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(intents=intents)

        self.bot_config = bot_config
        self.server_configs = ServerConfigs(f'data/server_configs/{bot_config.BOT_NAME}.json')

        self._tree = app_commands.CommandTree(self)
        self._initialized = False

        self._commands = []
        self._command_map: dict[str, command.Command] = {}

        self._guild_logger = GuildLogger(self, bot_config)

    def add_commands(self, *new_commands: command.Command):
        """
        Registers new commands to the command listener.
        """
        if self._initialized:
            raise Exception("Cannot add commands after initialization")

        self._commands += new_commands

        for cmd in new_commands:
            if isinstance(cmd, discord.app_commands.Command):
                self._tree.add_command(cmd)

    async def sync_commands(self):
        """
        Syncs the commands with the bot.
        """
        self._command_map = {cmd.name: cmd for cmd in self._commands}
        self._command_map.update({alias: cmd for cmd in self._commands for alias in cmd.aliases})

        await self._tree.sync()

    async def _initialize(self):
        common.logging.info("Initializing...")

        common.logging.info("Loading server configs...")
        await self.server_configs.load()

        common.logging.info("Starting workers...")
        workers.presenceUpdater.add_client(self)
        workers.guildUpdater.add_guild(self.bot_config.GUILD_NAME, self._guild_logger)

        common.logging.info("Syncing commands...")
        await self.sync_commands()

        common.logging.info("Finished initialization")
        self._initialized = True

    async def on_ready(self):
        try:
            common.logging.info(f"Logged in as {self.user}")

            if not self._initialized:
                await self._initialize()

            common.logging.info(f"Guilds: {[g.name for g in self.guilds]}")
        except Exception as e:
            await common.logging.error(exc_info=e)
            raise e

    async def on_message(self, message: discord.Message):
        event = messageParser.parse_message(message, self)

        if event is None:
            return

        cmd = self._command_map.get(event.args[0], None)

        if cmd is None:
            return

        async def run_command():
            try:
                await cmd.run(event)
            except (KeyboardInterrupt, SystemExit) as e:
                raise e
            except Exception as e:
                common.logging.error(exc_info=e, extra={"command_event": event})
                await event.reply_exception(e)

        await asyncio.create_task(run_command())
