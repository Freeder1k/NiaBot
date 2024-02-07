import threading
from dataclasses import dataclass

import discord
from discord import Embed
from discord.context_managers import Typing

from wrappers import botConfig


@dataclass()
class CommandEvent:
    sender: discord.Member
    channel: discord.TextChannel
    guild: discord.Guild
    client: discord.Client

    async def reply(self, content: str = None, **kwargs):
        await self.channel.send(content, **kwargs)

    async def reply_normal(self, message: str):
        await self.reply(embed=Embed(color=botConfig.DEFAULT_COLOR, description=message))

    async def reply_success(self, message: str):
        await self.reply(embed=Embed(color=botConfig.SUCCESS_COLOR, description=f"{chr(0x2705)} {message}"))

    async def reply_error(self, message: str):
        await self.reply(embed=Embed(color=botConfig.ERROR_COLOR, description=f"{chr(0x274c)} {message}"))

    async def reply_info(self, message: str):
        await self.reply(embed=Embed(color=botConfig.INFO_COLOR, description=f":information_source: {message}"))

    async def reply_exception(self, exception: Exception):
        await self.reply(embed=Embed(
            color=botConfig.ERROR_COLOR,
            title=f"A wild {type(exception)} appeared!",
            description="Please scream at the bot owner to fix it."
        ))

    def waiting(self) -> Typing:
        return self.channel.typing()


@dataclass()
class PrefixedCommandEvent(CommandEvent):
    message: discord.Message
    args: list[str]

    def __init__(self, message: discord.Message, args: list[str], client: discord.Client):
        super().__init__(message.author, message.channel, message.guild, client)
        self.message = message
        self.args = args


class Defer:
    def __init__(self, interaction: discord.Interaction):
        self.interaction = interaction

    async def __aenter__(self):
        await self.interaction.response.defer()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@dataclass()
class SlashCommandEvent(CommandEvent):
    interaction: discord.Interaction
    args: dict

    def __init__(self, interaction: discord.Interaction, args: dict):
        super().__init__(interaction.user, interaction.channel, interaction.guild, interaction.client)
        self.interaction = interaction
        self.args = args
        self._not_replied = threading.Lock()

    async def reply(self, content: str = None, **kwargs):
        if self._not_replied.acquire(blocking=False):
            await self.interaction.response.send_message(content, **kwargs)
        await self.interaction.followup.send(content, **kwargs)

    def waiting(self) -> Typing | Defer:
        if self._not_replied.acquire(blocking=False):
            return Defer(self.interaction)
        return self.channel.typing()
