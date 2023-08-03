import re

from discord import Permissions, Embed

import utils.discord
import wrappers.api.wynncraft.guild
from handlers.commands import command
from dataTypes import CommandEvent
from wrappers import botConfig

_guild_re = re.compile(r'[A-Za-z ]{3,30}$')

_star = "*"


def _get_stars(rank: str) -> str:
    match rank:
        case "OWNER":
            return _star * 5
        case "CHIEF":
            return _star * 4
        case "STRATEGIST":
            return _star * 3
        case "CAPTAIN":
            return _star * 2
        case "RECRUITER":
            return _star
        case "RECRUIT":
            return ""
    raise ValueError(f"Unknown rank {rank}")


class GuildCommand(command.Command):
    def __init__(self):
        super().__init__(
            name="guild",
            aliases=("g",),
            usage=f"guild <Guild Name>",
            description="",
            req_perms=Permissions().none(),
            permission_lvl=command.PermissionLevel.ANYONE
        )

    async def _execute(self, event: CommandEvent):
        if len(event.args) < 2:
            await utils.discord.send_error(event.channel, "Please specify a guild!")
            return

        guild_str = event.message.content.split(" ", 1)[1]

        if not _guild_re.match(guild_str):
            await utils.discord.send_error(event.channel, f"Invalid guild name ``{guild_str}``")
            return

        guild = await wrappers.api.wynncraft.guild.stats(guild_str)

        if guild is None:
            await utils.discord.send_error(event.channel, f"Couldn't find guild ``{guild_str}``")
            return

        embed = Embed(
            title=f"**Stats for {guild.name}:**",
            description="⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯",
            color=botConfig.DEFAULT_COLOR
        )
        embed.add_field(name="Tag", value=guild.prefix, inline=False)
        embed.add_field(name="Member count", value=len(guild.members), inline=False)
        embed.add_field(name="Level", value=f"{guild.level} ({guild.xp}%)", inline=False)
        embed.add_field(name="Created ", value=guild.created, inline=False)
        embed.add_field(name="", value="⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯", inline=False)

        server_list = await player.get_server_list()

        online_members = []
        max_l_len = 0

        for world, plist in server_list.items():
            online_players = {p.uuid: p.name for p in
                              (await player.get_players(usernames=plist))}

            for m in guild.members:
                uuid = m.uuid.replace("-", "").lower()
                if uuid in online_players:
                    name = _get_stars(m.rank) + online_players[uuid]
                    online_members.append((name, world))
                    max_l_len = max(max_l_len, len(name))

        online_members = [x for x in sorted(online_members, key=lambda item: item[0])]

        utils.discord.add_table_fields(embed, max_l_len, 4, False,
                                       (("Online members:", online_members),))

        await event.channel.send(embed=embed)
