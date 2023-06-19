import re
from datetime import datetime

from discord import Permissions, Embed

import api.minecraft
import api.wynncraft.player
import botConfig
import utils.discord
import utils.misc
from commands import command, commandEvent
import player

_username_re = re.compile(r'[0-9A-Za-z_]+$')
_uuid_re = re.compile(r'[0-9a-f]+$')


class PlayerCommand(command.Command):
    def __init__(self):
        super().__init__(
            name="player",
            aliases=("playerstats", "stats"),
            usage=f"player <username|uuid>",
            description="See the wynncraft stats of the provided player.",
            req_perms=Permissions().none(),
            permission_lvl=command.PermissionLevel.STRAT
        )

    async def _execute(self, event: commandEvent.CommandEvent):
        if len(event.args) < 2:
            await utils.discord.send_error(event.channel, "Please specify a username or uuid!")
            return

        user_str = event.args[1]

        # TODO make this better?
        p = None
        use_uuid = False
        if len(user_str) <= 16:
            if _username_re.match(user_str):
                p = await player.get_player(username=user_str)
        else:
            user_str = user_str.replace("-", "").lower()

            if len(user_str) == 32 and _uuid_re.match(user_str):
                p = await player.get_player(uuid=user_str)
                use_uuid = True

        if p is None:
            await utils.discord.send_error(event.channel, f"Couldn't parse user ``{event.args[1]}``")
            return

        stats = await api.wynncraft.player.stats(api.minecraft.format_uuid(p.uuid) if use_uuid else p.name)

        if stats is None:
            await utils.discord.send_error(event.channel, f"Couldn't get stats for {p.name}")
            return

        embed = Embed(
            title=f"**Stats for {p.name}:**",
            description="⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯",
            color=botConfig.DEFAULT_COLOR
        )
        embed.add_field(name="UUID", value=api.minecraft.format_uuid(p.uuid), inline=False)
        embed.add_field(name="Rank", value=stats.meta.tag.value, inline=False)
        embed.add_field(name="First Joined", value=stats.meta.firstJoin, inline=False)

        if stats.meta.location.online:
            seen_value = f"online on {stats.meta.location.server}"
        else:
            last_join = datetime.fromisoformat(stats.meta.lastJoin)
            last_join_str = utils.misc.get_relative_date_str(last_join, days=True, hours=True, minutes=True,
                                                             seconds=True)
            seen_value = f"offline for {last_join_str}"
        embed.add_field(name="Seen", value=seen_value, inline=False)

        embed.add_field(name="Playtime", value=f"{round(stats.meta.playtime/60, 2)} hours", inline=False)

        if stats.guild.name is None:
            guild_value = "None"
        else:
            guild_value = f"{stats.guild.rank} in {stats.guild.name}"
        embed.add_field(name="Guild", value=guild_value, inline=False)

        embed.set_thumbnail(url=api.minecraft.uuid_to_avatar_url(p.uuid))

        await event.channel.send(embed=embed)
