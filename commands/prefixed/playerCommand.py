import re
from datetime import datetime

from discord import Permissions, Embed

import api.minecraft
import api.wynncraft.player
import bot_config
import utils.discord
import utils.misc
from commands import command, commandEvent

_username_re = re.compile(r'[0-9A-Za-z_]+$')
_uuid_re = re.compile(r'[0-9a-f]+$')


class PlayerCommand(command.Command):
    def __init__(self):
        super().__init__(
            name="player",
            aliases=("playerstats", "stats"),
            usage=f"player <username|uuid>",
            description="",
            req_perms=Permissions().none(),
            permission_lvl=command.PermissionLevel.STRAT
        )

    async def _execute(self, event: commandEvent.CommandEvent):
        if len(event.args) < 2:
            await utils.discord.send_error(event.channel, "Please specify a username or uuid!")
            return

        user_str = event.args[1]
        uuid = None

        if len(user_str) <= 16:
            if _username_re.match(user_str):
                uuid = await api.minecraft.username_to_uuid(user_str)
        else:
            user_str = user_str.replace("-", "")

            if len(user_str) == 32 and _uuid_re.match(user_str):
                uuid = user_str

        if uuid is None:
            await utils.discord.send_error(event.channel, f"Couldn't parse user {event.args[1]}")
            return

        uuid = utils.misc.get_dashed_uuid(uuid)

        stats = await api.wynncraft.player.stats(uuid)

        if stats is None:
            await utils.discord.send_error(event.channel, f"Couldn't find user {event.args[1]}")
            return

        embed = Embed(
            title=f"**Stats for {stats.username}:**",
            description="⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯",
            color=bot_config.DEFAULT_COLOR
        )
        embed.add_field(name="UUID", value=stats.uuid, inline=False)
        embed.add_field(name="Rank", value=stats.rank, inline=False)
        embed.add_field(name="First Joined", value=stats.meta.firstJoin, inline=False)

        if stats.meta.location.online:
            seen_value = f"online on {stats.meta.location.server}"
        else:
            last_join = datetime.fromisoformat(stats.meta.lastJoin)
            last_join_str = utils.misc.get_relative_date_str(last_join, days=True, hours=True, minutes=True,
                                                             seconds=True)
            seen_value = f"offline for {last_join_str}"
        embed.add_field(name="Seen", value=seen_value, inline=False)

        embed.add_field(name="Playtime", value=f"{stats.meta.playtime} mins", inline=False)

        if stats.guild.name is None:
            guild_value = "None"
        else:
            guild_value = f"{stats.guild.rank} in {stats.guild.name}"
        embed.add_field(name="Guild", value=guild_value, inline=False)

        embed.set_thumbnail(url=api.minecraft.uuid_to_avatar(uuid))

        await event.channel.send(embed=embed)
