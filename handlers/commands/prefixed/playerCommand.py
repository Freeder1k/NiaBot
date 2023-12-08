import re
from datetime import datetime

from async_lru import alru_cache
from discord import Permissions, Embed

import utils.discord
import utils.misc
import utils.tableBuilder
import wrappers.api.minecraft
import wrappers.api.wynncraft.v3.player
from handlers.commands import command
from niatypes.dataTypes import CommandEvent, MinecraftPlayer
from wrappers import botConfig, minecraftPlayer
from wrappers.api.wynncraft.v3.types import PlayerStats

_username_re = re.compile(r'[0-9A-Za-z_]+')
_uuid_re = re.compile(r'[0-9a-f]+')


@alru_cache(ttl=60)
async def _create_player_embed(p: MinecraftPlayer) -> Embed | None:
    try:
        stats: PlayerStats = await wrappers.api.wynncraft.v3.player.stats(utils.misc.format_uuid(p.uuid), full_result=True)
    except wrappers.api.wynncraft.v3.player.UnknownPlayerException:
        return None

    rank = stats.rank if stats.rank != "Player"\
        else stats.supportRank.capitalize() if stats.supportRank is not None\
        else "Player"

    if stats.online:
        seen = f"Online on {stats.server}"
    else:
        last_join = datetime.fromisoformat(stats.lastJoin)
        seen = f"{utils.misc.get_relative_date_str(last_join, days=True, hours=True, minutes=True, seconds=True)} ago"

    if stats.guild is None:
        guild = "None"
    else:
        guild = f"{stats.guild.rank} in **[{stats.guild.name}](https://wynncraft.com/stats/guild/{stats.guild.name})**"

    description = f"## [{rank}] {p.name}\n" \
                  f"``{stats.uuid}``\n" \
                  f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n" \
                  f"**Seen:** {seen}\n" \
                  f"**Guild:** {guild}\n" \
                  f"**Joined:** {stats.firstJoin}\n" \
                  f"**Total Playtime:** {stats.playtime} Hours\n" \
                  f"**Total Level:** {stats.globalData.totalLevel}\n" \
                  f"**Total Wars:** {stats.globalData.wars}\n" \
                  f"**Total Mobs Killed:** {stats.globalData.killedMobs}\n" \
                  f"**Total Chests Opened:** {stats.globalData.chestsFound}\n" \
                  f"**Total Quests Completed:** {stats.globalData.completedQuests}\n" \
                  f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯"

    raids_tb = utils.tableBuilder.TableBuilder.from_str("l   r")
    raids_tb.add_row("Total", str(stats.globalData.raids.total))
    for raid_name, amount in stats.globalData.raids.list.items():
        raids_tb.add_row(raid_name, str(amount))

    raids = f"**Total Raid Completions**\n" \
            f">>> ```\n" \
            f"{raids_tb.build()}\n" \
            f"```"

    dungeons_tb = utils.tableBuilder.TableBuilder.from_str("l   r")
    dungeons_tb.add_row("Total", str(stats.globalData.dungeons.total))
    for dungeon_name, amount in stats.globalData.dungeons.list.items():
        dungeons_tb.add_row(dungeon_name.replace("Corrupted", "Cor."), str(amount))

    dungeons = f"**Total Dungeon Completions**\n" \
               f">>> ```\n" \
               f"{dungeons_tb.build()}\n" \
               f"```"

    embed = Embed(
        title="",
        description=description,
        color=botConfig.DEFAULT_COLOR,
    )
    embed.set_thumbnail(url=f"https://visage.surgeplay.com/bust/350/{stats.uuid}?y=-40") \
        .add_field(name="", value=raids, inline=False) \
        .add_field(name="", value=dungeons, inline=False) \
        .add_field(name="", value="⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n**Characters**", inline=False)

    char_count = 0
    for char_id, char in stats.characters.items():
        if char.nickname is None:
            char_name = char.type.capitalize()
        else:
            char_name = f"{char.nickname} ({char.type.capitalize()})"
        embed.add_field(
            name="",
            value=f"**[{char_name}](https://wynncraft.com/stats/player/{stats.uuid}?class={char_id})**\n" \
                  f"Combat: {char.level}\n" \
                  f"Total: {char.totalLevel}",
            inline=True
        )
        char_count += 1

    for i in range(char_count % 3):
        embed.add_field(name="", value="", inline=True)

    return embed


class PlayerCommand(command.Command):
    def __init__(self):
        super().__init__(
            name="player",
            aliases=("p", "stats"),
            usage=f"player <username|uuid>",
            description="See the wynncraft stats of the provided player.",
            req_perms=Permissions().none(),
            permission_lvl=command.PermissionLevel.STRAT
        )

    async def _execute(self, event: CommandEvent):
        async with event.channel.typing():
            if len(event.args) < 2:
                await utils.discord.send_error(event.channel, "Please specify a username or uuid!")
                return

            user_str = event.args[1]

            if len(user_str) <= 16 and _username_re.fullmatch(user_str):
                p = await minecraftPlayer.get_player(username=user_str)
            else:
                user_str = user_str.replace("-", "").lower()

                if len(user_str) == 32 and _uuid_re.fullmatch(user_str):
                    p = await minecraftPlayer.get_player(uuid=user_str)
                else:
                    await utils.discord.send_error(event.channel, f"Couldn't parse player ``{event.args[1]}``.")
                    return

            if p is None:
                await utils.discord.send_error(event.channel, f"Couldn't find player ``{event.args[1]}``.")
                return

            embed = await _create_player_embed(p)
            if embed is None:
                await utils.discord.send_error(event.channel, f"Couldn't get stats for ``{p.name}``.")
            else:
                await event.channel.send(embed=embed)
