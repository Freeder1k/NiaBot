from __future__ import annotations

import threading
from dataclasses import dataclass

import discord
from discord import Embed
from discord.context_managers import Typing

from common import botInstance


@dataclass()
class CommandEvent:
    """
    Base class describing details relevant to a command that was run by a user.
    """
    sender: discord.Member
    channel: discord.TextChannel
    guild: discord.Guild
    bot: botInstance.BotInstance

    async def reply(self, content: str = None, **kwargs):
        """
        Wrapper to reply to the command.
        """
        await self.channel.send(content, **kwargs)

    async def reply_normal(self, message: str):
        """
        Normal reply message.
        """
        await self.reply(embed=Embed(color=self.bot.config.DEFAULT_COLOR, description=message))

    async def reply_success(self, message: str):
        """
        Reply with a message that indicates success.
        """
        await self.reply(embed=Embed(color=self.bot.config.SUCCESS_COLOR, description=f"{chr(0x2705)} {message}"))

    async def reply_error(self, message: str):
        """
        Reply with an error message.
        """
        await self.reply(embed=Embed(color=self.bot.config.ERROR_COLOR, description=f"{chr(0x274c)} {message}"))

    async def reply_info(self, message: str):
        """
        Reply with an info message.
        """
        await self.reply(embed=Embed(color=self.bot.config.INFO_COLOR, description=f":information_source: {message}"))

    async def reply_exception(self, exception: Exception):
        """
        Reply, indicating that an exception occurred.
        """
        await self.reply(embed=Embed(color=self.bot.config.ERROR_COLOR, title=f"A wild {type(exception)} appeared!",
                                     description="Please scream at the bot owner to fix it."))

    def waiting(self) -> Typing:
        """
        Returns a context manager that can be used to indicate that the bot is thinking.
        """
        return self.channel.typing()


@dataclass()
class PrefixedCommandEvent(CommandEvent):
    """
    Describes a command event that was run as a chat message in prefix style.
    """
    message: discord.Message
    args: list[str]

    def __init__(self, message: discord.Message, args: list[str], client: botInstance.BotInstance):
        super().__init__(message.author, message.channel, message.guild, client)
        self.message = message
        self.args = args


class Defer:
    """
    Context manager that can be used to indicate that the bot is thinking for slash commands.
    """

    def __init__(self, interaction: discord.Interaction):
        self.interaction = interaction

    async def __aenter__(self):
        await self.interaction.response.defer()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@dataclass()
class SlashCommandEvent(CommandEvent):
    """
    Describes a command event that was run as a slash command.
    """
    interaction: discord.Interaction
    args: dict

    def __init__(self, interaction: discord.Interaction, bot: botInstance.BotInstance, args: dict):
        super().__init__(interaction.user, interaction.channel, interaction.guild, bot)
        self.interaction = interaction
        self.args = args
        self._not_replied = threading.Lock()

    async def reply(self, content: str = None, **kwargs):
        if self._not_replied.acquire(blocking=False):
            await self.interaction.response.send_message(content, **kwargs)
            return
        await self.interaction.followup.send(content, **kwargs)

    def waiting(self) -> Typing | Defer:
        if self._not_replied.acquire(blocking=False):
            return Defer(self.interaction)
        return self.channel.typing()
