import re
import traceback
from re import Pattern

from discord import Message, TextChannel, Client

import utils.discord
from handlers.commands.command import Command
from dataTypes import CommandEvent
from wrappers import serverConfig

_bot_mention: Pattern
_commands: list[Command] = []
_command_map: dict[str, Command] = {}
_client: Client = None


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
    global _bot_mention, _client
    _bot_mention = re.compile(f"\?<@!?{client.user.id}>")
    _client = client


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

    cmd_prefix = serverConfig.get_cmd_prefix(message.guild.id)
    if content.startswith(cmd_prefix):
        args = content[len(cmd_prefix):].split(" ")
    elif _bot_mention.match(content):
        _, *args = message.content.split(" ")
    else:
        return

    if len(args) < 1:
        return

    if args[0] not in _command_map:
        return

    command_event = CommandEvent(message, args, message.author, message.channel, message.guild, _client)

    try:
        await _command_map[args[0]].run(command_event)
    except Exception as e:
        await utils.discord.send_exception(command_event, e)
        print(message)
        traceback.print_exc()
