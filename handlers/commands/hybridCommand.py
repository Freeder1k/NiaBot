import re
import typing
from abc import abstractmethod
from typing import Collection

import discord.app_commands
import discord.ext.commands
from discord import Permissions, ChannelType
from discord.app_commands import Choice, locale_str
from discord.utils import MISSING

import handlers.commands.command
import handlers.logging
from handlers.commands.commandEvent import CommandEvent, SlashCommandEvent

_name_reg = re.compile(r"^[-\w]{1,32}$")


class CommandParam(discord.app_commands.transformers.CommandParameter):
    """
    Describes a parameter for a slash command.
    """

    def __init__(
            self, name: str,
            description: str,
            required: bool = False,
            default: typing.Any = MISSING,
            display_name: typing.Union[str, locale_str] = MISSING,
            choices: typing.List[Choice[typing.Union[str, int, float]]] = MISSING,
            ptype: discord.AppCommandOptionType = MISSING,
            channel_types: typing.List[ChannelType] = MISSING,
            min_value: typing.Optional[typing.Union[int, float]] = None,
            max_value: typing.Optional[typing.Union[int, float]] = None,
            autocomplete: typing.Optional[
                typing.Callable[..., typing.Coroutine[typing.Any, typing.Any, typing.Any]]] = None,
    ):
        if not re.match(_name_reg, name) or len(name) > 32:
            raise TypeError(f"Name {name!r} is not a valid name.")

        if len(description) > 100:
            raise TypeError(f"Description {description!r} is too long.")

        if not required and default is MISSING:
            raise TypeError("Optional parameters must have a default value.")

        if choices is not MISSING and len(choices) > 25:
            raise TypeError("Choices must be less than 25.")

        super().__init__(
            default=default,
            required=required,
            name=name,
            description=description,
            type=ptype,
            choices=choices,
            channel_types=channel_types,
            min_value=min_value,
            max_value=max_value,
            autocomplete=autocomplete,
            _rename=display_name,
        )


class HybridCommand(handlers.commands.command.Command, discord.app_commands.Command):
    """
    Base class for a hybrid command that can be run either through a chat message with a prefix or as a slash command.
    This class should be inherited and the _execute method should be overridden to
    create a new command.
    """

    def __init__(self,
                 name: str,
                 aliases: Collection[str],
                 params: list[CommandParam],
                 description: str,
                 base_perms: Permissions,
                 permission_lvl: handlers.commands.command.PermissionLevel
                 ):
        usage = f"{name} {' '.join([f'<{p.display_name}>' if p.required else f'[{p.display_name}]' for p in params])}"

        handlers.commands.command.Command.__init__(self, name, aliases, usage, description, base_perms, permission_lvl)

        async def empty_callback(interaction: discord.Interaction) -> typing.Any:
            pass

        discord.app_commands.Command.__init__(
            self,
            name=self.name,
            description=self.description,
            callback=empty_callback
        )

        async def app_callback(interaction: discord.Interaction, **kwargs):
            event = SlashCommandEvent(interaction, kwargs)
            try:
                await self.run(event)
            except (KeyboardInterrupt, SystemExit) as e:
                raise e
            except Exception as e:
                handlers.logging.error(exc_info=e, extra={"slash_command_event": event})
                await event.reply_exception(e)

        self._callback = app_callback
        self._params = {p.name: p for p in params}

        self.guild_only = True

    @abstractmethod
    async def _execute(self, command_event: CommandEvent):
        pass
