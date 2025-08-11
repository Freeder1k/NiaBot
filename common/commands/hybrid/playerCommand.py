from datetime import datetime

from async_lru import alru_cache
from discord import Permissions, Embed
from discord.utils import escape_markdown

import common.api.wynncraft.v3.player
import common.botInstance
import common.utils.command
import common.utils.discord
import common.utils.misc
import common.utils.tableBuilder
from common.commands import command, hybridCommand
from common.commands.commandEvent import PrefixedCommandEvent, SlashCommandEvent, CommandEvent
from common.types.dataTypes import MinecraftPlayer
from common.types.wynncraft import PlayerStats
from common.utils.command import parse_player


@alru_cache(ttl=30)
async def _create_player_embed(p: MinecraftPlayer, color: int) -> Embed | None:
    stats: PlayerStats = await common.api.wynncraft.v3.player.stats(common.utils.misc.format_uuid(p.uuid),
                                                                    full_result=True)

    rank = stats.rank if stats.rank != "Player" \
        else stats.supportRank.capitalize() if stats.supportRank is not None \
        else "Player"

    if stats.online:
        seen = f"Online on {stats.server}"
    elif stats.lastJoin is not None:
        last_join = datetime.fromisoformat(stats.lastJoin)
        seen = f"{common.utils.misc.get_relative_date_str(last_join, days=True, hours=True, minutes=True, seconds=True)} ago"
    else:
        seen = "Hidden"

    if stats.guild is None:
        guild = "None"
    else:
        guild = f"{stats.guild.rank.capitalize()} of **[{stats.guild.name}](https://wynncraft.com/stats/guild/{stats.guild.name.replace(' ', '%20')})**"

    first_join = stats.firstJoin if stats.firstJoin is not None else "Hidden"
    playtime = f"{stats.playtime} Hours" if stats.playtime is not None else "Hidden"
    if stats.globalData is None:
        total_level = "Hidden"
        wars = "Hidden"
        killed_mobs = "Hidden"
        chests_found = "Hidden"
        completed_quests = "Hidden"
        total_dungeons = "Hidden"
        pvp_kd = "Hidden"
    else:
        total_level = stats.globalData.totalLevel
        wars = stats.globalData.wars
        killed_mobs = stats.globalData.killedMobs
        chests_found = stats.globalData.chestsFound
        completed_quests = stats.globalData.completedQuests
        total_dungeons = stats.globalData.dungeons.total
        pvp_kd = f"{stats.globalData.pvp.kills}/{stats.globalData.pvp.deaths}"


    if stats.characters is not None:
        deaths = 0
        for c in stats.characters.values():
            if c.deaths is not None:
                deaths += c.deaths
            else:
                deaths = "Hidden"
                break
    else:
        deaths = "Hidden"

    description = f"## [{rank}] {escape_markdown(p.name)}\n" \
                  f"``{stats.uuid}``\n" \
                  f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n" \
                  f"**Seen:** {seen}\n" \
                  f"**Guild:** {guild}\n" \
                  f"**Joined:** {first_join}\n" \
                  f"**Total Playtime:** {playtime}\n" \
                  f"**Total Level:** {total_level}\n" \
                  f"**Total Wars:** {wars}\n" \
                  f"**Total Mobs Killed:** {killed_mobs}\n" \
                  f"**Total Deaths:** {deaths}\n" \
                  f"**Total Chests Opened:** {chests_found}\n" \
                  f"**Total Quests Completed:** {completed_quests}\n" \
                  f"**Total Dungeons Completed:** {total_dungeons}\n" \
                  f"**PVP K/D:** {pvp_kd}\n" \
                  f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯"

    if stats.globalData is not None:
        raids_tb = common.utils.tableBuilder.TableBuilder.from_str("l   r")
        raids_tb.add_row("Total", str(stats.globalData.raids.total))
        for raid_name, amount in stats.globalData.raids.list.items():
            raids_tb.add_row(raid_name, str(amount))

        raids = f"**Total Raid Completions**\n" \
                f">>> ```\n" \
                f"{raids_tb.build()}\n" \
                f"```"

    embed = Embed(
        title="",
        description=description,
        color=color,
    )
    embed.set_thumbnail(url=f"https://visage.surgeplay.com/bust/350/{stats.uuid}?y=-40")
    if stats.globalData is not None:
        embed.add_field(name="", value=raids, inline=False)

    if stats.characters is not None:
        embed.add_field(name="", value="⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n**Characters**", inline=False)
        for char_id, char in stats.characters.items():
            if char.nickname is None:
                char_name = char.type.capitalize()
            else:
                char_name = f"{escape_markdown(char.nickname)} ({char.type.capitalize()})"
            embed.add_field(
                name="",
                value=f"**[{char_name}](https://wynncraft.com/stats/player/{stats.uuid}?class={char_id})**\n" \
                      f"Combat: {char.level}\n" \
                      f"Total: {char.totalLevel}",
                inline=True
            )

        for i in range(len(stats.characters) % 3):
            embed.add_field(name="", value="", inline=True)

    return embed


class PlayerCommand(hybridCommand.HybridCommand):
    def __init__(self, bot: common.botInstance.BotInstance):
        super().__init__(
            name="player",
            aliases=("p", "stats"),
            params=[hybridCommand.PlayerParam()],
            description="See the wynncraft stats of the provided player.",
            base_perms=Permissions().none(),
            permission_lvl=command.PermissionLevel.ANYONE,
            bot=bot
        )

    async def _execute(self, event: CommandEvent):
        async with event.waiting():

            if isinstance(event, PrefixedCommandEvent):
                if len(event.args) < 2:
                    await event.reply_error("Please specify a player!")
                    return

                player_str = event.args[1]
                try:
                    p = await parse_player(player_str)
                except ValueError as e:
                    await event.reply_error(f"{str(e)}")
                    return
            elif isinstance(event, SlashCommandEvent):
                p = event.args["player"]

            color = event.bot.config.DEFAULT_COLOR

            try:
                embed = await _create_player_embed(p, color)
                await event.reply(embed=embed)
            except common.api.wynncraft.v3.player.UnknownPlayerException:
                await event.reply_error(f"{escape_markdown(p.name)} is not a wynncraft player!")
