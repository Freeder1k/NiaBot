import asyncio
import re
from re import Pattern

from discord import Message, TextChannel, Client

import config
from commands.command import Command
from commands.commandEvent import CommandEvent

_bot_mention: Pattern
_commands: list[Command] = []

command_tasks = []


def _run_command(command: Command, command_event: CommandEvent):
    asyncio.run(command.run(command_event))


def register_commands(*new_commands: Command):
    global _commands
    _commands += new_commands


def get_commands() -> tuple[Command]:
    return tuple(_commands)


def on_ready(client: Client):
    global _bot_mention
    _bot_mention = re.compile(f"\?<@!?{client.user.id}>")


def on_message(message: Message):
    if type(message.channel) is not TextChannel:
        return
    if message.webhook_id is not None:
        return
    if message.author.bot:
        return

    content = message.content
    if len(content) > 0:
        if content.startswith(config.PREFIX):
            content = content[1:]
        elif _bot_mention.match(content):
            content = content.split(" ", 1)[1]
        else:
            return

        splits = content.split(" ")
        command_event = CommandEvent(message, content, splits, message.author, message.channel,
                                     message.guild)

        for c in _commands:
            if c.is_this_command(command_event.args[0]):
                # Thread(target=asyncio.run, args=(c.run(command_event),)).start()
                command_tasks.append(asyncio.create_task(c.run(command_event)))
                # TODO implement this properly with multiprocessing
