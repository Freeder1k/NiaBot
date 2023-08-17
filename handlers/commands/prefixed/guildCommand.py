import re
from collections.abc import Iterable

from discord import Permissions, Embed

import utils.discord
import wrappers.api.wynncraft.guild
import wrappers.api.wynncraft.network
import wrappers.wynncraftGuild
from handlers.commands import command
from niatypes.dataTypes import CommandEvent, WynncraftGuild
from wrappers import botConfig, minecraftPlayer

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


def _format_guilds(guilds: Iterable[WynncraftGuild]) -> str:
    return '\n'.join([f"- {g.name} [{g.tag}]" for g in guilds])


class GuildCommand(command.Command):
    def __init__(self):
        super().__init__(
            name="guild",
            aliases=("g",),
            usage=f"guild <name|tag>",
            description="Get a wynncraft guild by its name or tag.",
            req_perms=Permissions().none(),
            permission_lvl=command.PermissionLevel.ANYONE
        )

    async def _execute(self, event: CommandEvent):
        if len(event.args) < 2:
            await utils.discord.send_error(event.channel, "Please specify a guild!")
            return

        guild_str = event.message.content.split(" ", 1)[1]

        if not _guild_re.match(guild_str):
            await utils.discord.send_error(event.channel, f"Invalid guild name or tag``{guild_str}``")
            return

        possible_guilds: tuple[WynncraftGuild] = await wrappers.wynncraftGuild.find_guilds(guild_str)
        if not possible_guilds:
            await utils.discord.send_error(event.channel, f"Couldn't find guild ``{guild_str}``")
            return
        if len(possible_guilds) == 1:
            guild = possible_guilds[0]
        else:
            exact_matches = [g for g in possible_guilds if g.tag == guild_str or g.name == guild_str]
            if not exact_matches:
                await utils.discord.send_info(event.channel,
                                              f"Found multiple matches for ``{guild_str}``:\n{_format_guilds(possible_guilds)}")
                return
            elif len(exact_matches) == 1:
                guild = exact_matches[0]
            else:
                await utils.discord.send_info(event.channel,
                                              f"Found multiple matches for ``{guild_str}``:\n{_format_guilds(exact_matches)}")
                return

        guild_stats = await wrappers.wynncraftGuild.get_guild_stats(name=guild.name)
        if guild_stats is None:
            await utils.discord.send_error(event.channel, f"Failed to retrieve stats for guild ``{guild_str}``")
            return

        embed = Embed(
            title=f"**Stats for {guild_stats.name}:**",
            description="⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯",
            color=botConfig.DEFAULT_COLOR
        )
        embed.add_field(name="Tag", value=guild_stats.prefix, inline=False)
        embed.add_field(name="Member count", value=len(guild_stats.members), inline=False)
        embed.add_field(name="Level", value=f"{guild_stats.level} ({guild_stats.xp}%)", inline=False)
        embed.add_field(name="Created ", value=guild_stats.created, inline=False)
        embed.add_field(name="", value="⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯", inline=False)

        server_list = await wrappers.api.wynncraft.network.server_list()

        online_members = []
        max_l_len = 0

        for world, plist in server_list.items():
            online_players = {p.uuid: p.name for p in
                              (await minecraftPlayer.get_players(usernames=plist))}

            for m in guild_stats.members:
                uuid = m.uuid.replace("-", "").lower()
                if uuid in online_players:
                    name = _get_stars(m.rank) + online_players[uuid]
                    online_members.append((name, world))
                    max_l_len = max(max_l_len, len(name))

        online_members = [x for x in sorted(online_members, key=lambda item: item[0])]

        utils.discord.add_table_fields(embed, max_l_len, 4, False,
                                       (("Online members:", online_members),))

        await event.channel.send(embed=embed)
