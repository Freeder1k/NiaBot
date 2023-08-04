from dataclasses import dataclass
from typing import NamedTuple

import discord

from niatypes.enums import NiaRank


class MinecraftPlayer(NamedTuple):
    uuid: str
    name: str


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
