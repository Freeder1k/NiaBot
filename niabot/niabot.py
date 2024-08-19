import asyncio
from datetime import datetime, timezone
from typing import Final

import discord
from discord import app_commands

import common.api.sessionManager
import common.commands.commandListener
import common.logging
import common.logging
import common.logging2
import common.storage.manager
import common.storage.playtimeData
import workers.guildUpdater
import workers.guildUpdater2
import workers.playtimeTracker
import workers.presenceUpdater
import workers.statTracker
import workers.usernameUpdater
from common.storage import serverConfig


class NiaBot(discord.Client):
    def __init__(self, commands, hybrid_commands, config):
        self.start_time: Final = datetime.now(timezone.utc)

        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(intents=intents)

        self.tree = app_commands.CommandTree(self)

        self.initialized = False
        self.commands = commands
        self.hybrid_commands = hybrid_commands

        self.config = config

    async def on_ready(self):
        if self.initialized:
            common.logging.info(f"Logged in as {self.user}")
            return

        await common.logging.init_discord_handler(self)
        common.logging.set_client(self)

        common.logging.info(f"Logged in as {self.user}")
        common.logging.info("Initializing Nia Bot...")

        await serverConfig.load_server_configs()
        await common.storage.manager.init_database()
        await common.api.sessionManager.init_sessions()

        start_workers()  # TODO

        common.commands.commandListener.on_ready()

        common.commands.commandListener.register_commands(*self.commands, *self.hybrid_commands)

        today = datetime.now(timezone.utc).date()
        if (await common.storage.playtimeData.get_first_date_after(today)) is None:
            await workers.playtimeTracker.update_playtimes()

        self.initialized = True

        common.logging.info("Syncing command tree...")
        for cmd in self.hybrid_commands:
            self.tree.add_command(cmd)

        await self.tree.sync()

        common.logging.info("Ready")
        common.logging.info(f"Guilds: {[g.name for g in self.guilds]}")

    async def on_message(self, message: discord.Message):
        asyncio.create_task(common.commands.commandListener.on_message(message, self))
