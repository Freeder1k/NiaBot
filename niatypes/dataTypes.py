from dataclasses import dataclass
from typing import NamedTuple

import discord

from niatypes.enums import NiaRank
from niatypes.simpleJsonable import SimpleJsonable


class MinecraftPlayer(NamedTuple):
    uuid: str
    name: str


class WynncraftGuild(NamedTuple):
    name: str
    tag: str


@dataclass(frozen=True)
class Point2D(SimpleJsonable):
    x: int
    z: int


@dataclass()
class CommandEvent:
    sender: discord.Member
    channel: discord.TextChannel
    guild: discord.Guild
    client: discord.Client


@dataclass()
class PrefixedCommandEvent(CommandEvent):
    message: discord.Message
    args: list[str]

    def __init__(self, message: discord.Message, args: list[str], client: discord.Client):
        super().__init__(message.author, message.channel, message.guild, client)
        self.message = message
        self.args = args


@dataclass()
class SlashCommandEvent(CommandEvent):
    interaction: discord.Interaction
    args: dict

    def __init__(self, interaction: discord.Interaction, args: dict):
        super().__init__(interaction.user, interaction.channel, interaction.guild, interaction.client)
        self.interaction = interaction
        self.args = args


@dataclass
class NiaMember:
    rank: NiaRank
    discord_id: int
    mc_uuid: str
    notes: list[str]
