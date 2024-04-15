import io
import time
from datetime import datetime

import discord
import matplotlib.pyplot as plt
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
from wrappers import botConfig


async def _generate_history_graph(history: list[tuple[str, int]]):
    dates = [datetime.fromisoformat(t) for t, _ in history]
    values = [stat for _, stat in history]

    # Initialize IO
    data_stream = io.BytesIO()

    plt.plot(dates, values)

    plt.xlabel("Date")
    plt.ylabel("Value")  # TODO
    plt.grid(True)

    # Save content into the data stream
    plt.savefig(data_stream, format='png', bbox_inches="tight", dpi=80)
    plt.close()

    ## Create file
    # Reset point back to beginning of stream
    data_stream.seek(0)
    chart = discord.File(data_stream, filename="graph.png")

    return chart


@alru_cache(ttl=60)
async def _create_history_embed(stat: PlayerStatsIdentifier, player: wrappers.minecraftPlayer.MinecraftPlayer):
    embed = Embed(
        description=f"# {stat} history of {escape_markdown(player.name)}",
        color=botConfig.DEFAULT_COLOR
    )

    t = time.time()
    history = await wrappers.storage.playerTrackerData.get_history(stat, player.uuid)
    t = time.time() - t
    embed.set_footer(text=f"Query took {t:.2f}s")

    if isinstance(history[0][1], int):
        chart = await _generate_history_graph(history)
        embed.set_image(
            url="attachment://graph.png"
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
            params=[hybridCommand.CommandParam(
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

            embed, chart = await _create_history_embed(stat, player)
            await event.reply(embed=embed, file=chart)
