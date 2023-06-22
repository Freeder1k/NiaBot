from dataclasses import dataclass
from typing import NamedTuple

from discord import Message, Member, TextChannel, Guild, Client


class MinecraftPlayer(NamedTuple):
    uuid: str
    name: str


@dataclass(frozen=True)
class CommandEvent:
    message: Message
    args: list[str]
    sender: Member
    channel: TextChannel
    guild: Guild
    client: Client
