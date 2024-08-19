from re import Pattern

from discord import Message, TextChannel, Client

import common.logging
import common.utils.discord
from common.storage import serverConfig
from common.commands.command import Command
from common.commands.commandEvent import PrefixedCommandEvent

_bot_mention: Pattern
_commands: list[Command] = []
_command_map: dict[str, Command] = {}
_client: Client = None


def register_commands(*new_commands: Command):
    """
    Registers new commands to the command listener.
    """
    global _commands
    _commands += new_commands
    for cmd in new_commands:
        _command_map[cmd.name] = cmd
        _command_map.update({a: cmd for a in cmd.aliases})


def get_commands() -> tuple[Command]:
    """
    Returns a tuple of all registered commands.
    """
    return tuple(_commands)


def get_command_map() -> dict[str, Command]:
    """
    Returns a map of all registered commands including aliases.
    """
    return _command_map


def on_ready():
    """
    Called when the client is ready.
    """
    # global _bot_mention
    # _bot_mention = re.compile(f"\?<@!?{client.user.id}>")
    pass


async def on_message(message: Message, client: Client):
    """
    Called when a message is received.
    """
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
    # elif _bot_mention.match(content):
    #     _, *args = message.content.split(" ")
    else:
        return

    if len(args) < 1:
        return

    if args[0] not in _command_map:
        return

    command_event = PrefixedCommandEvent(message, args, client)

    try:
        await _command_map[args[0]].run(command_event)
    except (KeyboardInterrupt, SystemExit) as e:
        raise e
    except Exception as e:
        common.logging.error(exc_info=e, extra={"command_event": command_event})
        await common.utils.discord.send_exception(command_event.channel, e)
