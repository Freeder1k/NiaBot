import re
from re import Pattern

from discord import Message, TextChannel

import common.logging
import common.utils.discord
from common.botInstance import BotInstance
from common.commands.command import Command
from common.commands.commandEvent import PrefixedCommandEvent
from common.storage import serverConfig


class CommandListener:
    def __init__(self, bot: BotInstance):
        self.bot = bot
        self.bot_mention: Pattern = None
        self.commands: list[Command] = []
        self.command_map: dict[str, Command] = {}

    def register_commands(self, *new_commands: Command):
        """
        Registers new commands to the command listener.
        """
        self.commands += new_commands
        for cmd in new_commands:
            self.command_map[cmd.name] = cmd
            self.command_map.update({a: cmd for a in cmd.aliases})

    def get_commands(self) -> tuple[Command]:
        """
        Returns a tuple of all registered commands.
        """
        return tuple(self.commands)

    def get_command_map(self) -> dict[str, Command]:
        """
        Returns a map of all registered commands including aliases.
        """
        return self.command_map

    async def on_message(self, message: Message):
        """
        Called when a message is received.
        """
        if self.bot_mention is None:
            self.bot_mention = re.compile(f"\?<@!?{self.bot.user.id}>")

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
        elif self.bot_mention.match(content):
            _, *args = message.content.split(" ")
        else:
            return

        if len(args) < 1:
            return

        if args[0] not in self.command_map:
            return

        command_event = PrefixedCommandEvent(message, args, self.bot)

        try:
            await self.command_map[args[0]].run(command_event)
        except (KeyboardInterrupt, SystemExit) as e:
            raise e
        except Exception as e:
            common.logging.error(exc_info=e, extra={"command_event": command_event})
            await common.utils.discord.send_exception(command_event.channel, e)
