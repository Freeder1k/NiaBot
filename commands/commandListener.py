import re
from re import Pattern

from discord import Message, TextChannel, Client

import config
import utils.discord
from commands.command import Command
from commands.commandEvent import CommandEvent

_bot_mention: Pattern
_commands: list[Command] = []
_command_map: dict[str, Command] = {}


def register_commands(*new_commands: Command):
    global _commands
    _commands += new_commands
    for cmd in new_commands:
        _command_map[cmd.name] = cmd
        _command_map.update({a: cmd for a in cmd.aliases})


def get_commands() -> tuple[Command]:
    return tuple(_commands)


def get_command_map() -> dict[str, Command]:
    return _command_map


def on_ready(client: Client):
    global _bot_mention
    _bot_mention = re.compile(f"\?<@!?{client.user.id}>")


async def on_message(message: Message):
    if type(message.channel) is not TextChannel:
        return
    if message.webhook_id is not None:
        return
    if message.author.bot:
        return

    content = message.content
    if len(content) == 0:
        return

    if content.startswith(config.PREFIX):
        args = content[1:].split(" ")
    elif _bot_mention.match(content):
        _, *args = message.content.split(" ")
    else:
        return

    if len(args) < 1:
        return

    if args[0] not in _command_map:
        return

    command_event = CommandEvent(message, args, message.author, message.channel, message.guild)

    try:
        await _command_map[args[0]].run(command_event)
    except Exception as e:
        await utils.discord.send_exception(message.channel, e)
        print(message)
        raise e
