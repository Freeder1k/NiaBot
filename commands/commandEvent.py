from dataclasses import dataclass

from discord import Message, Member, Guild, TextChannel, Client


@dataclass(frozen=True)
class CommandEvent:
    message: Message
    args: list[str]
    sender: Member
    channel: TextChannel
    guild: Guild
    client: Client
