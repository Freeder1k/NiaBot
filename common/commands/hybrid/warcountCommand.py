import time
from datetime import datetime

import discord
import discord.utils
from discord import Permissions, Embed

import common.api.wynncraft.v3.guild
import common.api.wynncraft.v3.player
import common.botInstance
import common.storage.playerTrackerData
import common.storage.usernameData
import common.utils.command
import common.utils.misc
from common.commands import hybridCommand, command
from common.commands.commandEvent import PrefixedCommandEvent, SlashCommandEvent
from common.types.constants import seasons
from common.types.wynncraft import WynncraftGuild
from common.utils import tableBuilder, minecraftPlayer
from common.utils.command import Timeframe


async def _create_warcount_embed(timeframe: Timeframe = None, guild: WynncraftGuild = None, color=None):
    t = time.time()
    warcounts = (await common.storage.playerTrackerData.get_warcount_relative(
        t_from=timeframe.start,
        t_to=timeframe.end,
        guild=guild))[:100]
    t = time.time() - t

    guild_str = f'## Guild: {guild.name}\n' if guild else ''
    timeframe_str = ' (all time)' if timeframe is None else f' ({timeframe.comment})' if timeframe.comment else f'\n## {timeframe}'
    embed = Embed(
        description=f"# Top 100 warrers\n## {timeframe_str}\n{guild_str}"
                    f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯",
        color=color,
        timestamp=discord.utils.utcnow()
    )

    embed.set_footer(text=f"Query took {t:.2f}s")

    names = {p.uuid: p.name for p in await minecraftPlayer.get_players(uuids=[t[1] for t in warcounts])}

    table_builder = tableBuilder.TableBuilder.from_str('l  l  r')
    table_builder.add_row("Rank", "Name", "Wars")
    table_builder.add_seperator_row()
    [table_builder.add_row(rank, names[uuid], wars) for rank, uuid, wars in warcounts]

    splits = common.utils.misc.split_str(table_builder.build(), 1000, "\n")
    for split in splits:
        embed.add_field(name="", value=f">>> ```\n{split}```", inline=False)

    return embed


def parse_season(season: int):
    if season >= len(seasons) or season < 0:
        raise ValueError(f"Invalid season number: ``{season}``")
    return Timeframe(seasons[season][0], seasons[season][1], f"season {season}")


class WarcountCommand(hybridCommand.HybridCommand):
    def __init__(self, bot: common.botInstance.BotInstance):
        super().__init__(
            name="warcount",
            aliases=("wc",),
            params=[
                hybridCommand.GuildParam(),
                hybridCommand.DateParam(
                    "start", "[optional] start date. E.g: '01.01.2025', '2 months ago'.",
                    required=False,
                    default=None,
                ),
                hybridCommand.DateParam(
                    "end", "[optional] end date. E.g. '31.12.2025', 'today'.",
                    required=False,
                    default=None,
                ),
                hybridCommand.CommandParam(
                    "season",
                    "The season number.",
                    required=False,
                    default=None,
                    ptype=discord.AppCommandOptionType.integer,
                )
            ],
            description="Get a war count leaderboard.",
            base_perms=Permissions().none(),
            permission_lvl=command.PermissionLevel.ANYONE,
            bot=bot
        )

    async def _execute(self, event: PrefixedCommandEvent):
        async with event.waiting():
            if isinstance(event, PrefixedCommandEvent):
                return

            elif isinstance(event, SlashCommandEvent):
                guild = event.args.get("guild")
                start = event.args.get("start")
                end = event.args.get("end")
                season = event.args.get("season")

                if start is None and end is None and season is None:
                    season = len(seasons) - 1  # latest season

                if season is not None:
                    try:
                        timeframe = parse_season(season)
                    except ValueError as e:
                        await event.reply_error(str(e))
                        return
                else:
                    if start is None:
                        start = datetime.utcnow() - common.utils.command.timedelta(days=30)
                    if end is None:
                        end = datetime.utcnow()
                    comment = f"{discord.utils.format_dt(start, 'd')} - {discord.utils.format_dt(end, 'd')}"
                    timeframe = Timeframe(start, end, comment)

                embed = await _create_warcount_embed(timeframe, guild, color=event.bot.config.DEFAULT_COLOR)
                await event.reply(embed=embed)
