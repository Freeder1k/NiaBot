import re
import time
from datetime import datetime

import discord
import discord.utils
from async_lru import alru_cache
from discord import Permissions, Embed
from discord.app_commands.models import Choice

import utils.command
import utils.discord
import utils.misc
import wrappers.api.wynncraft.v3.guild
import wrappers.api.wynncraft.v3.player
import wrappers.api.wynncraft.v3.types
import wrappers.minecraftPlayer
import wrappers.storage.playerTrackerData
import wrappers.storage.usernameData
from handlers.commands import command, hybridCommand
from handlers.commands.commandEvent import PrefixedCommandEvent, SlashCommandEvent
from niatypes.constants import seasons
from niatypes.dataTypes import WynncraftGuild
from utils import tableBuilder
from wrappers import botConfig

_guild_re = re.compile(r'[A-Za-z ]{3,30}')


@alru_cache(ttl=60)
async def _create_warcount_embed(guild: WynncraftGuild = None):
    guild_str = f'## Guild: {guild.name}\n' if guild else ''
    embed = Embed(
        description=f"# Top 100 warrers (all time)\n{guild_str}"
                    f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯",
        color=botConfig.DEFAULT_COLOR,
        timestamp=discord.utils.utcnow()
    )

    t = time.time()
    warcounts = (await wrappers.storage.playerTrackerData.get_warcount(guild=guild))[:100]
    t = time.time() - t
    embed.set_footer(text=f"Query took {t:.2f}s")

    names = {p.uuid: p.name for p in await wrappers.minecraftPlayer.get_players(uuids=[t[1] for t in warcounts])}

    table_builder = tableBuilder.TableBuilder.from_str('l  l  r')
    table_builder.add_row("Rank", "Name", "Wars")
    table_builder.add_seperator_row()
    [table_builder.add_row(rank, names[uuid], wars) for rank, uuid, wars in warcounts]

    splits = utils.misc.split_str(table_builder.build(), 1000, "\n")
    for split in splits:
        embed.add_field(name="", value=f">>> ```\n{split}```", inline=False)

    return embed


@alru_cache(ttl=60)
async def _create_rel_warcount_embed(timeframe: utils.command.Timeframe, guild: WynncraftGuild = None):
    guild_str = f'## Guild: {guild.name}\n' if guild else ''
    embed = Embed(
        description=f"# Top 100 warrers \n## ({timeframe})\n{guild_str}"
                    f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯",
        color=botConfig.DEFAULT_COLOR,
        timestamp=discord.utils.utcnow()
    )

    t = time.time()
    warcounts = (await wrappers.storage.playerTrackerData.get_warcount_relative(
        t_from=timeframe.start,
        t_to=timeframe.end,
        guild=guild))[:100]
    t = time.time() - t
    embed.set_footer(text=f"Query took {t:.2f}s")

    names = {p.uuid: p.name for p in await wrappers.minecraftPlayer.get_players(uuids=[t[1] for t in warcounts])}

    table_builder = tableBuilder.TableBuilder.from_str('l  l  r')
    table_builder.add_row("Rank", "Name", "Wars")
    table_builder.add_seperator_row()
    [table_builder.add_row(rank, names[uuid], wars) for rank, uuid, wars in warcounts]

    splits = utils.misc.split_str(table_builder.build(), 1000, "\n")
    for split in splits:
        embed.add_field(name="", value=f">>> ```\n{split}```", inline=False)

    return embed


async def _guild_autocomplete(
        interaction: discord.Interaction,
        current: str,
) -> list[Choice[str]]:
    if len(current) > 1:
        if not utils.command.guild_re.fullmatch(current):
            return []
        guilds = await wrappers.api.wynncraft.v3.guild.list_guilds()
        return [Choice(name=guild.name, value=guild.name) for guild in guilds
                if current.lower() in guild.tag.lower()
                or current.lower() in guild.name.lower()][0:25]

    return []


async def _date_autocomplete(
        interaction: discord.Interaction,
        current: str,
) -> list[Choice[str]]:
    if current == "":
        return [Choice(name="YYYY-MM-DD", value=datetime.utcnow().date().isoformat())]
    return []


async def _timeframe_autocomplete(
        interaction: discord.Interaction,
        current: str,
) -> list[Choice[str]]:
    if current == "":
        return [
            Choice(name="1d", value="1d"),
            Choice(name="1w", value="1w"),
            Choice(name="1M", value="1M"),
            Choice(name="1y", value="1y"),
            Choice(name=f"s{len(seasons) - 1}", value=f"s{len(seasons) - 1}"),
        ]
    return []


class WarcountCommand(hybridCommand.HybridCommand):
    def __init__(self):
        super().__init__(
            name="warcount",
            aliases=("wc",),
            params=[
                hybridCommand.CommandParam(
                    "guild", "[optional] guild.",
                    required=False,
                    default=None,
                    ptype=discord.AppCommandOptionType.string,
                    autocomplete=_guild_autocomplete,
                ),
                hybridCommand.CommandParam(
                    "start", "[optional] start date.",
                    required=False,
                    default=None,
                    ptype=discord.AppCommandOptionType.string,
                    autocomplete=_date_autocomplete,
                ),
                hybridCommand.CommandParam(
                    "end", "[optional] end date.",
                    required=False,
                    default=None,
                    ptype=discord.AppCommandOptionType.string,
                    autocomplete=_date_autocomplete,
                ),
                hybridCommand.CommandParam(
                    "timeframe", "[optional] relative time frame.",
                    required=False,
                    default=None,
                    ptype=discord.AppCommandOptionType.string,
                    autocomplete=_timeframe_autocomplete,
                ),
            ],
            description="Get warcount leaderboard.",  # TODO more descriptive
            base_perms=Permissions().none(),
            permission_lvl=command.PermissionLevel.ANYONE
        )

    async def _execute(self, event: PrefixedCommandEvent):
        async with event.waiting():
            if isinstance(event, PrefixedCommandEvent):
                await event.reply_error("This command is not yet implemented in prefixed mode.")
                return
                if len(event.args) < 2:
                    await event.reply(embed=await _create_warcount_embed())
                    return

                if len(event.args) == 2:
                    arg = event.args[1]
                    try:
                        guild_arg = await utils.command.parse_guild(arg)

                        await event.reply(embed=await _create_warcount_embed(guild_arg))
                        return
                    except utils.command.AmbiguousGuildError as e:
                        await event.reply_info(str(e))
                        return
                    except utils.command.UnknownGuildError as e:
                        await event.reply_error(str(e))
                        return
                    except ValueError:
                        pass

                    # TODO parse timeframes and stuff

            elif isinstance(event, SlashCommandEvent):
                start = event.args.get("start")
                end = event.args.get("end")
                timeframe_arg = event.args.get("timeframe")
                guild_arg = event.args.get("guild")

                if (start is None) ^ (end is None):
                    await event.reply_error("Invalid syntax! Please specify both start and end date.")
                    return
                if (start is not None) and (timeframe_arg is not None):
                    await event.reply_error(
                        "Invalid syntax! Please specify either a timeframe **or** start and end date.")
                    return

                if start is not None:
                    start = discord.utils.parse_time(start)
                    end = discord.utils.parse_time(end)
                    timeframe = utils.command.Timeframe(start=start, end=end)
                elif timeframe_arg is not None:
                    timeframe = utils.command.Timeframe.from_timeframe_str(timeframe_arg)
                else:
                    timeframe = None

                guild = None
                if guild_arg is not None:
                    try:
                        guild = await utils.command.parse_guild(guild_arg)
                    except utils.command.AmbiguousGuildError as e:
                        await event.reply_info(str(e))
                        return
                    except (ValueError, utils.command.UnknownGuildError) as e:
                        await event.reply_error(str(e))
                        return

                if timeframe is not None:
                    embed = await _create_rel_warcount_embed(timeframe=timeframe, guild=guild)
                    await event.reply(embed=embed)
                else:
                    embed = await _create_warcount_embed(guild=guild)
                    await event.reply(embed=embed)
