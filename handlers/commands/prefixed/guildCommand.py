import re
from collections.abc import Iterable

from async_lru import alru_cache
from discord import Permissions, Embed

import utils.discord
import utils.misc
import wrappers.api.wynncraft.network
import wrappers.api.wynncraft.v3.guild
import wrappers.api.wynncraft.v3.player
import wrappers.storage.usernameData
from handlers.commands import command
from niatypes.dataTypes import CommandEvent, WynncraftGuild
from utils import tableBuilder
from wrappers import botConfig

_guild_re = re.compile(r'[A-Za-z ]{3,30}$')

_star = "★"


def _format_guilds(guilds: Iterable[WynncraftGuild]) -> str:
    return '\n'.join([f"- {g.name} [{g.tag}]" for g in guilds])


@alru_cache(ttl=60)
async def _create_guild_embed(guild: WynncraftGuild):
    guild_stats = await wrappers.api.wynncraft.v3.guild.stats(name=guild.name)
    if guild_stats is None:
        return None

    embed = Embed(
        description=f"# [{guild_stats.prefix}] {guild_stats.name}\n"
                    f"Created: {guild_stats.created}\n"
                    f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯",
        color=botConfig.DEFAULT_COLOR
    )
    # TODO create own implementation
    embed.set_thumbnail(url=f'https://wynn-guild-banner.toki317.dev/banners/{guild_stats.name.replace(" ", "%20")}')

    embed.add_field(name="Guild level", value=f"{guild_stats.level} ({guild_stats.xpPercent}%)", inline=True)
    embed.add_field(name="Members", value=guild_stats.members.total, inline=True)
    embed.add_field(name="", value="", inline=True)
    embed.add_field(name="Territories", value=guild_stats.territories, inline=True)
    embed.add_field(name="Total wars", value=guild_stats.wars, inline=True)
    embed.add_field(name="Season rating", value=guild_stats.seasonRanks[max(guild_stats.seasonRanks.keys())].rating,
                    inline=True)

    embed.add_field(name="", value="⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯", inline=False)

    player_worlds = await wrappers.api.wynncraft.v3.player.player_list(identifier='uuid')
    online_players = {utils.misc.get_dashed_uuid(p.uuid): p for p in
                      await wrappers.storage.usernameData.get_players(uuids=list(player_worlds.keys()))}

    online_members = [(f"{5 * _star}{online_players[uuid].name}", player_worlds[uuid])
                      for uuid in guild_stats.members.owner.keys() if uuid in online_players] \
                     + [(f"{4 * _star}{online_players[uuid].name}", player_worlds[uuid])
                        for uuid in guild_stats.members.chief.keys() if uuid in online_players] \
                     + [(f"{3 * _star}{online_players[uuid].name}", player_worlds[uuid])
                        for uuid in guild_stats.members.strategist.keys() if uuid in online_players] \
                     + [(f"{2 * _star}{online_players[uuid].name}", player_worlds[uuid])
                        for uuid in guild_stats.members.captain.keys() if uuid in online_players] \
                     + [(f"{1 * _star}{online_players[uuid].name}", player_worlds[uuid])
                        for uuid in guild_stats.members.recruiter.keys() if uuid in online_players] \
                     + [(f"{0 * _star}{online_players[uuid].name}", player_worlds[uuid])
                        for uuid in guild_stats.members.recruit.keys() if uuid in online_players]

    table_builder = tableBuilder.TableBuilder.from_str('l   r')
    [table_builder.add_row(*t) for t in online_members]

    # TODO split
    embed.add_field(name=f"Online members ({len(online_members)})", value=f">>> ```\n{table_builder.build()}```")

    return embed


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
        async with event.channel.typing():
            if len(event.args) < 2:
                await utils.discord.send_error(event.channel, "Please specify a guild!")
                return

            guild_str = event.message.content.split(" ", 1)[1]

            if not _guild_re.match(guild_str):
                await utils.discord.send_error(event.channel, f"Invalid guild name or tag``{guild_str}``")
                return

            possible_guilds: tuple[WynncraftGuild] = await wrappers.api.wynncraft.v3.guild.find(guild_str)
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

            embed = await _create_guild_embed(guild)
            if embed is None:
                await utils.discord.send_error(event.channel, f"Failed to retrieve stats for guild ``{guild_str}``")
                return

            await event.channel.send(embed=embed)
