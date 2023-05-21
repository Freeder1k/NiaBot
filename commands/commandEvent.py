from dataclasses import dataclass

from discord import Message, Member, Guild, TextChannel


@dataclass(frozen=True)
class CommandEvent:
    message: Message
    text: str
    args: list[str]
    sender: Member
    channel: TextChannel
    guild: Guild
