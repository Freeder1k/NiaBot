from dataclasses import dataclass

from discord import Message, Member, User, Guild
from discord.abc import MessageableChannel


@dataclass(frozen=True)
class CommandEvent:
    message: Message
    text: str
    sender: User | Member
    channel: MessageableChannel
    guild: Guild | None

    @classmethod
    def from_message(cls, message: Message):
        cls(message, message.content, message.author, message.channel, message.guild)