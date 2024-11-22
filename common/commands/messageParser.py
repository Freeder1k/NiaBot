import re

from discord import Message, TextChannel

from common.botInstance import BotInstance
from common.commands.commandEvent import PrefixedCommandEvent

def parse_message(message: Message, bot: BotInstance) -> PrefixedCommandEvent | None:
    """
    Parses a message for commands. Returns a PrefixedCommandEvent if a command was found, otherwise None.
    """
    if type(message.channel) is not TextChannel:
        return None
    if message.webhook_id is not None:
        return None
    if message.author.bot:
        return None

    content = message.content
    if len(content) == 0:
        return None

    cmd_prefix = bot.server_configs.get(message.guild.id).cmd_prefix
    if content.startswith(cmd_prefix):
        args = content[len(cmd_prefix):].split(" ")
    elif re.match(f"<@!?{bot.user.id}> ", content):
        _, *args = message.content.split(" ")   # Assume space after mention
    else:
        return None

    if len(args) < 1:
        return None

    return PrefixedCommandEvent(message, args, bot)