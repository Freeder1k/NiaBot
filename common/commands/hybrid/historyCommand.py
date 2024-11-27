from __future__ import annotations

import time
from datetime import datetime, timedelta, date

import discord
from async_lru import alru_cache
from discord import Permissions, Embed
from discord.utils import escape_markdown

import common.api.wynncraft.v3.guild
import common.api.wynncraft.v3.player
import common.botInstance
import common.storage.playerTrackerData
import common.storage.usernameData
import common.utils.command
import common.utils.minecraftPlayer
from common.commands import hybridCommand, command
from common.commands.commandEvent import PrefixedCommandEvent, SlashCommandEvent, CommandEvent
from common.types.enums import PlayerStatsIdentifier
from common.utils.discord import create_chart


async def _generate_history_graph(history: list[tuple[str, int | float, str]]):
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


class TimeframeDate(date):
    def __new__(cls, timeframe: str, d: date):
        if timeframe == "day":
            return super().__new__(cls, d.year, d.month, d.day)
        elif timeframe == "week":
            d = d - timedelta(days=d.weekday())
            return super().__new__(cls, d.year, d.month, d.day)
        elif timeframe == "month":
            return super().__new__(cls, d.year, d.month, 1)
        else:
            raise ValueError("Invalid timeframe")

    def __init__(self, timeframe: str, d: date):
        self.timeframe = timeframe
        super().__init__()

    def next(self) -> TimeframeDate:
        if self.timeframe == "day":
            return TimeframeDate(self.timeframe, date(self.year, self.month, self.day) + timedelta(days=1))
        elif self.timeframe == "week":
            return TimeframeDate(self.timeframe, date(self.year, self.month, self.day) + timedelta(weeks=1))
        elif self.timeframe == "month":
            return TimeframeDate(self.timeframe, date(self.year + self.month // 12, self.month % 12 + 1, 1))

    @classmethod
    def fromisoformat(cls, date_string: str, timeframe: str = "day") -> TimeframeDate:
        return cls(timeframe, datetime.fromisoformat(date_string).date())


def _get_all_timeframe_dates_between(timeframe: str, start: date, end: date):
    dates = []
    start = TimeframeDate(timeframe, start)
    end = TimeframeDate(timeframe, end)
    while start <= end:
        dates.append(start)
        start = start.next()
    return dates


async def _generate_relative_history_graph(history: list[tuple[str, int, str]], timeframe: str, playtime: bool):
    dates = _get_all_timeframe_dates_between(
        timeframe,
        datetime.fromisoformat(history[0][0]),
        datetime.fromisoformat(history[-1][0])
    )
    values = [0 for _ in dates]
    i = 0
    prev_val = history[0][1]
    prev_d = TimeframeDate.fromisoformat(history[0][0], timeframe)
    for rec_t, stat, _ in history:
        while i < len(dates) and not dates[i] == TimeframeDate.fromisoformat(rec_t, timeframe):
            i += 1
        if i >= len(dates):
            break

        # skip issue with playtimes around that time
        d = TimeframeDate.fromisoformat(rec_t)
        if not (playtime and d >= date(2023, 12, 5) >= prev_d):
            values[i] += stat - prev_val

        prev_val = stat
        prev_d = d

    return create_chart(dates, values, "Date", "Value")


@alru_cache(ttl=60)
async def _create_history_embed(stat: PlayerStatsIdentifier, player: common.utils.minecraftPlayer.MinecraftPlayer,
                                color: int, relative: str = None):
    embed = Embed(
        description=f"# {stat} history of {escape_markdown(player.name)}",
        color=color
    )

    t = time.time()
    history = await common.storage.playerTrackerData.get_history(stat, player.uuid)
    t = time.time() - t
    embed.set_footer(text=f"Query took {t:.2f}s")

    if isinstance(history[0][1], int) or isinstance(history[0][1], float):
        if relative is not None:
            chart = await _generate_relative_history_graph(
                history,
                relative,
                playtime=(stat == PlayerStatsIdentifier.PLAYTIME)
            )
        else:
            chart = await _generate_history_graph(history)
        embed.set_image(
            url="attachment://chart.png"
        )
    else:
        chart = None
        embed.add_field(name="Not implemented for non number values!", value="")

    return embed, chart


class HistoryCommand(hybridCommand.HybridCommand):
    def __init__(self, bot: common.botInstance.BotInstance):
        super().__init__(
            name="history",
            aliases=(),
            params=[
                hybridCommand.CommandParam(
                    "player", "The player, specified by username or uuid",
                    required=True,
                    ptype=discord.AppCommandOptionType.string,
                    autocomplete=common.utils.command.player_autocomplete,
                ),
                hybridCommand.CommandParam(
                    "stat", "The stat to retrieve.",
                    required=True,
                    ptype=discord.AppCommandOptionType.string,
                    choices=common.utils.command.stats_choices,
                ),
                hybridCommand.CommandParam(
                    "relative", "If specified, the timeframes to bucket relative data to.",
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
            permission_lvl=command.PermissionLevel.ANYONE,
            bot=bot
        )

    async def _execute(self, event: CommandEvent):
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
                player = await common.utils.command.parse_player(player_str)
            except ValueError as e:
                await event.reply_error(str(e))
                return

            if relative_str is not None and relative_str not in ["day", "week", "month"]:
                await event.reply_error("Invalid relative timeframe!")
                return

            color = event.bot.config.DEFAULT_COLOR

            embed, chart = await _create_history_embed(stat, player, color, relative_str)
            if chart is None:
                await event.reply(embed=embed)
            else:
                await event.reply(embed=embed, file=chart)
