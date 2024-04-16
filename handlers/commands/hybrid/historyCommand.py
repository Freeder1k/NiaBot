import time
from datetime import datetime

import discord
from async_lru import alru_cache
from discord import Permissions, Embed
from discord.utils import escape_markdown

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
from niatypes.enums import PlayerStatsIdentifier
from utils.command import stats_autocomplete
from utils.discord import create_chart
from wrappers import botConfig


async def _generate_history_graph(history: list[tuple[str, int, str]]):
    dates = []
    values = []
    prev_val = None
    for rec_t, stat, join_t in history:
        if prev_val is not None:
            dates.append(datetime.fromisoformat(join_t))
            values.append(prev_val)
        dates.append(datetime.fromisoformat(rec_t))
        values.append(stat)
        prev_val = stat

    return create_chart(dates, values, "Date", "Value")  # TODO y label units


def _is_same_timeframe(timeframe: str, t1: datetime, t2: datetime):
    if timeframe == "day":
        return t1.date() == t2.date()
    elif timeframe == "week":
        t1 = t1.isocalendar()
        t2 = t2.isocalendar()
        return t1[0] == t2[0] and t1[1] == t2[1]
    elif timeframe == "month":
        return t1.month == t2.month and t1.year == t2.year
    else:
        return False


async def _generate_relative_history_graph(history: list[tuple[str, int, str]], relative: str):
    dates = []
    values = []
    prev_val = history[0][1]
    prev_date = None
    for rec_t, stat, _ in history:
        if prev_date is None or not _is_same_timeframe(relative, prev_date, datetime.fromisoformat(rec_t)):
            prev_date = datetime.fromisoformat(rec_t)
            dates.append(prev_date)
            values.append(stat - prev_val)
        else:
            values[-1] += stat - prev_val

        prev_val = stat

    return create_chart(dates, values, "Date", "Value")


@alru_cache(ttl=60)
async def _create_history_embed(stat: PlayerStatsIdentifier, player: wrappers.minecraftPlayer.MinecraftPlayer,
                                relative: str = None):
    embed = Embed(
        description=f"# {stat} history of {escape_markdown(player.name)}",
        color=botConfig.DEFAULT_COLOR
    )

    t = time.time()
    history = await wrappers.storage.playerTrackerData.get_history(stat, player.uuid)
    t = time.time() - t
    embed.set_footer(text=f"Query took {t:.2f}s")

    if isinstance(history[0][1], int):
        if relative is not None:
            chart = await _generate_relative_history_graph(history, relative)
        else:
            chart = await _generate_history_graph(history)
        embed.set_image(
            url="attachment://chart.png"
        )
    else:
        chart = None
        embed.add_field(name="Not implemented yet for non number values!", value="")

    return embed, chart


class HistoryCommand(hybridCommand.HybridCommand):
    def __init__(self):
        super().__init__(
            name="history",
            aliases=("h",),
            params=[
                hybridCommand.CommandParam(
                    "stat", "The stat to retrieve.",
                    required=True,
                    ptype=discord.AppCommandOptionType.string,
                    autocomplete=stats_autocomplete,
                ),
                hybridCommand.CommandParam(
                    "player", "The player, specified by username or uuid",
                    required=True,
                    ptype=discord.AppCommandOptionType.string,
                    autocomplete=utils.command.player_autocomplete,
                ),
                hybridCommand.CommandParam(
                    "relative", "If specified the timeframes to bucket relative data to.",
                    required=False,
                    ptype=discord.AppCommandOptionType.string,
                    choices=[
                        discord.app_commands.Choice(name="day", value="day"),
                        discord.app_commands.Choice(name="week", value="week"),
                        discord.app_commands.Choice(name="month", value="month"),
                        # discord.Choice(name="year", value="year"),
                    ],
                    default=None,
                )
            ],
            description="Get the history of a specified stat for a player.",
            base_perms=Permissions().none(),
            permission_lvl=command.PermissionLevel.ANYONE
        )

    async def _execute(self, event: PrefixedCommandEvent):
        async with event.waiting():
            if isinstance(event, PrefixedCommandEvent):
                return  # TODO
            elif isinstance(event, SlashCommandEvent):
                stat_str = event.args["stat"]
                player_str = event.args["player"]
                relative_str = event.args["relative"]

            try:
                stat = PlayerStatsIdentifier(stat_str.lower())
            except ValueError:
                await event.reply_error("Invalid stat!")
                return
            try:
                player = await utils.command.parse_player(player_str)
            except ValueError as e:
                await event.reply_error(str(e))
                return

            if relative_str is not None and relative_str not in ["day", "week", "month"]:
                await event.reply_error("Invalid relative timeframe!")
                return

            embed, chart = await _create_history_embed(stat, player, relative_str)
            if chart is None:
                await event.reply(embed=embed)
            else:
                await event.reply(embed=embed, file=chart)
