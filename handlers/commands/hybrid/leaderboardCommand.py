import time

import discord
from async_lru import alru_cache
from discord import Permissions, Embed
from discord.app_commands.models import Choice

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
from utils import tableBuilder
from wrappers import botConfig


@alru_cache(ttl=60)
async def _create_leaderboard_embed(stat: PlayerStatsIdentifier):
    embed = Embed(
        description=f"# Top 100 players by {stat}\n"
                    f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯",
        color=botConfig.DEFAULT_COLOR
    )

    t = time.time()
    leaderboard = await wrappers.storage.playerTrackerData.get_leaderboard(stat)
    t = time.time() - t
    embed.set_footer(text=f"Query took {t:.2f}s")

    names = {p.uuid: p.name for p in await wrappers.minecraftPlayer.get_players(uuids=leaderboard.keys())}

    table_builder = tableBuilder.TableBuilder.from_str('l   r')
    [table_builder.add_row(names[k], v) for k, v in leaderboard.items()]

    splits = utils.misc.split_str(table_builder.build(), 1000, "\n")
    for split in splits:
        embed.add_field(name="", value=f">>> ```\n{split}```", inline=False)

    return embed


async def _stats_autocomplete(
        interaction: discord.Interaction,
        current: str,
) -> list[Choice[str]]:
    if len(current) == 0:
        return [Choice(name=stat, value=stat) for stat in PlayerStatsIdentifier if not stat.startswith("dungeon")] \
            + [Choice(name='dungeons_', value='dungeons_')]

    return [
               Choice(name=stat, value=stat)
               for stat in PlayerStatsIdentifier if current.lower() in stat.lower()
           ][0:25]


class LeaderboardCommand(hybridCommand.HybridCommand):
    def __init__(self):
        super().__init__(
            name="leaderboard",
            aliases=("lb",),
            params=[hybridCommand.CommandParam(
                "stat", "The stat to track.",
                required=True,
                ptype=discord.AppCommandOptionType.string,
                autocomplete=_stats_autocomplete,
            )],  # TODO time period & guild
            description="Get the leaderboard for a specified stat.",
            base_perms=Permissions().none(),
            permission_lvl=command.PermissionLevel.ANYONE
        )

    async def _execute(self, event: PrefixedCommandEvent):
        async with event.waiting():
            if isinstance(event, PrefixedCommandEvent):
                if len(event.args) < 2:
                    await event.reply_error("Please specify a stat!")
                    return

                stat_str = event.message.content.split(" ", 1)[1]
            elif isinstance(event, SlashCommandEvent):
                stat_str = event.args["stat"]

            try:
                stat = PlayerStatsIdentifier(stat_str.lower())
            except ValueError:
                await event.reply_error("Invalid stat!")
                return

            embed = await _create_leaderboard_embed(stat)
            await event.reply(embed=embed)
