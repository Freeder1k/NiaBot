import asyncio

import discord
from discord import app_commands

import common.logging
import workers.guildUpdater
import workers.presenceUpdater
from common.botConfig import BotConfig
from common.commands.command import Command
from common.commands.commandListener import CommandListener
from common.commands.hybridCommand import HybridCommand


class BotInstance(discord.Client):
    def __init__(self, bot_config: BotConfig):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(intents=intents)
        self.bot_config = bot_config
        self._tree = app_commands.CommandTree(self)
        self._initialized = False

        self._commands = []
        self._hybrid_commands = []

        self._command_listener = CommandListener(self)

    def register_commands(self, *new_commands: Command):
        """
        Registers new commands to the command listener.
        """
        for cmd in new_commands:
            if isinstance(cmd, HybridCommand):
                self._hybrid_commands.append(cmd)
            else:
                self._commands.append(cmd)

        if self._initialized:
            self._command_listener.register_commands(*new_commands)

            for cmd in new_commands:
                if isinstance(cmd, HybridCommand):
                    self._tree.add_command(cmd)

            await self._tree.sync()

    async def on_ready(self):
        try:
            common.logging.info(f"Logged in as {self.user}")
            common.logging.info("Initializing...")

            if not self._initialized:
                workers.presenceUpdater.add_client(self)

                self._command_listener.register_commands(*self._commands, *self._hybrid_commands)

                self._initialized = True

                common.logging.info("Syncing command tree...")
                for cmd in self._hybrid_commands:
                    self._tree.add_command(cmd)

                await self._tree.sync()

                common.logging.info("Ready")
                common.logging.info(f"Guilds: {[g.name for g in self.guilds]}")
        except Exception as e:
            await common.logging.error(exc_info=e)
            raise e

    async def on_message(self, message: discord.Message):
        asyncio.create_task(self._command_listener.on_message(message))
