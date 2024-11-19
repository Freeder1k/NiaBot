import asyncio

import discord
from discord import app_commands

import common.logging
import workers.guildUpdater
import workers.presenceUpdater
from common.botConfig import BotConfig
from common.commands import command
from common.commands.commandListener import CommandListener
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

        self._command_listener = CommandListener(self)

        self._guild_logger = GuildLogger(self, bot_config)

    def add_commands(self, *new_commands: command.Command):
        """
        Registers new commands to the command listener.
        """
        for cmd in new_commands:
            self._commands.append(cmd)

        if self._initialized:
            self._command_listener.register_commands(*new_commands)

            for cmd in new_commands:
                if isinstance(cmd, app_commands.Command):
                    self._tree.add_command(cmd)

    async def sync_commands(self):
        """
        Syncs the command tree with the discord API.
        """
        await self._tree.sync()

    async def _initialize(self):
        common.logging.info("Initializing...")

        await self.server_configs.load()

        workers.presenceUpdater.add_client(self)
        workers.guildUpdater.add_guild(self.bot_config.GUILD_NAME, self._guild_logger)

        self._command_listener.register_commands(*self._commands)

        common.logging.info("Syncing command tree...")
        for cmd in self._commands:
            if isinstance(cmd, discord.app_commands.Command):
                self._tree.add_command(cmd)

        await self._tree.sync()

        self._initialized = True

    async def on_ready(self):
        try:
            common.logging.info(f"Logged in as {self.user}")

            if not self._initialized:
                await self._initialize()

            common.logging.info("Ready")
            common.logging.info(f"Guilds: {[g.name for g in self.guilds]}")
        except Exception as e:
            await common.logging.error(exc_info=e)
            raise e

    async def on_message(self, message: discord.Message):
        await asyncio.create_task(self._command_listener.on_message(message))
