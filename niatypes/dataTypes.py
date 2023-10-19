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


@dataclass(frozen=True)
class CommandEvent:
    message: discord.Message
    args: list[str]
    sender: discord.Member
    channel: discord.TextChannel
    guild: discord.Guild
    client: discord.Client


@dataclass
class NiaMember:
    rank: NiaRank
    discord_id: int
    mc_uuid: str
    notes: list[str]
