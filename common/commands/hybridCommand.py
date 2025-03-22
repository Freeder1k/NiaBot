import re
from abc import abstractmethod
from typing import Collection, Any, Union, List, Optional, Callable, Coroutine

import discord.app_commands
import discord.ext.commands
from discord import Permissions, ChannelType
from discord.app_commands import Choice, locale_str
from discord.utils import MISSING

import common.logging
import common.utils.command
import common.utils.discord
from common.botInstance import BotInstance
from common.commands import command
from common.commands.commandEvent import CommandEvent, SlashCommandEvent, PrefixedCommandEvent

_name_reg = re.compile(r"^[-\w]{1,32}$")


class CommandParam(discord.app_commands.transformers.CommandParameter):
    """
    Describes a parameter for a slash command.
    """

    def __init__(self,
                 name: str,
                 description: str,
                 required: bool = False,
                 default: Any = MISSING,
                 display_name: Union[str, locale_str] = MISSING,
                 choices: List[Choice[Union[str, int, float]]] = MISSING,
                 ptype: discord.AppCommandOptionType = MISSING,
                 channel_types: List[ChannelType] = MISSING,
                 min_value: Optional[Union[int, float]] = None,
                 max_value: Optional[Union[int, float]] = None,
                 autocomplete: Optional[Callable[..., Coroutine[Any, Any, Any]]] = None,
                 parser: Optional[Union[Callable[[str], Any], Callable[[str], Coroutine[Any, Any, Any]]]] = None,
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

        self.parser = parser


class PlayerParam(CommandParam):
    def __init__(self, required=True, default: Any = MISSING):
        super().__init__(
            "player",
            "The username or uuid of a player.",
            required=required,
            default=default,
            ptype=discord.AppCommandOptionType.string,
            autocomplete=common.utils.command.player_autocomplete,
            parser=common.utils.command.parse_player
        )


class GuildParam(CommandParam):
    def __init__(self, required=True):
        super().__init__(
            "guild",
            "The name or tag of a guild.",
            required=required,
            ptype=discord.AppCommandOptionType.string,
            autocomplete=common.utils.command.guild_autocomplete,
            parser=common.utils.command.parse_guild
        )


# class DateParam(CommandParam):
#     def __init__(self, required=True):
#         super().__init__(
#             "date",
#             "The date in the format YYYY-MM-DD.",
#             required=required,
#             ptype=discord.AppCommandOptionType.string,
#             autocomplete=common.utils.command.date_autocomplete,
#         )


class HybridCommand(command.Command, discord.app_commands.Command):
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
                 permission_lvl: command.PermissionLevel,
                 bot: BotInstance
                 ):
        usage = f"{name} {' '.join([f'<{p.display_name}>' if p.required else f'[{p.display_name}]' for p in params])}"

        command.Command.__init__(self, name, aliases, usage, description, base_perms, permission_lvl)

        async def empty_callback(interaction: discord.Interaction) -> Any:
            pass

        discord.app_commands.Command.__init__(self, name=self.name, description=self.description,
                                              callback=empty_callback)

        async def app_callback(interaction: discord.Interaction, **kwargs):
            event = SlashCommandEvent(interaction, bot, kwargs)
            try:
                await self.run(event)
            except (KeyboardInterrupt, SystemExit) as e:
                raise e
            except Exception as e:
                common.logging.error(exc_info=e, extra={"slash_command_event": event})
                await event.reply_exception(e)

        self._callback = app_callback
        self._params = {p.name: p for p in params}

        self.guild_only = True

    @abstractmethod
    async def _execute(self, event: CommandEvent):
        pass

    async def run(self, event: CommandEvent):
        """
        Runs the command and checks if the user has the required permissions to run the command and parses the arguments if it's a slash command.
        """
        if not await self.check_permissions(event):
            return

        if isinstance(event, PrefixedCommandEvent):
            await self._execute(event)
            return

        if not isinstance(event, SlashCommandEvent):
            raise TypeError(f"Unknown event type. {type(event)}")

        for param in self._params.values():
            if param.parser is None:
                continue
            value = event.args[param.name]
            if not param.required and value == param.default:
                continue

            if type(value) is str:
                try:
                    value = await discord.utils.maybe_coroutine(param.parser, value)
                    event.args[param.name] = value
                except ValueError as e:
                    await event.reply_error(f"{str(e)}")
                    return
            else:
                common.logging.error(f"Invalid type for param {param.name}: {type(value)}",
                                     extra={"slash_command_event": event})
                continue

        await self._execute(event)
