import io

import aiohttp.client_exceptions
import discord
from PIL import Image
from async_lru import alru_cache
from discord import Permissions, Embed

import handlers.logging
import utils.command
import utils.discord
import utils.misc
import wrappers.api.wynncraft.v3.guild
import wrappers.api.wynncraft.v3.player
import wrappers.api.wynncraft.v3.types
import wrappers.storage.usernameData
from handlers.commands import command, hybridCommand
from handlers.commands.commandEvent import PrefixedCommandEvent, SlashCommandEvent
from niatypes.dataTypes import WynncraftGuild
from niatypes.enums import PlayerIdentifier
from utils import tableBuilder, banner
from wrappers import botConfig

_star = "★"


def _get_curr_sr(guild_stats: wrappers.api.wynncraft.v3.types.GuildStats) -> int:
    if not guild_stats.seasonRanks:
        return 0
    curr_season = max(guild_stats.seasonRanks.keys(), key=lambda x: int(x))
    return guild_stats.seasonRanks[curr_season].rating


@alru_cache(ttl=60)
async def _create_guild_embed(guild: WynncraftGuild):
    guild_stats: wrappers.api.wynncraft.v3.types.GuildStats
    try:
        guild_stats = await wrappers.api.wynncraft.v3.guild.stats(name=guild.name)
    except (wrappers.api.wynncraft.v3.guild.UnknownGuildException, aiohttp.client_exceptions.ClientResponseError):
        return None, None

    embed = Embed(
        description=f"# [{guild_stats.prefix}] {guild_stats.name}\n"
                    f"Created: {guild_stats.created}\n"
                    f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯",
        color=botConfig.DEFAULT_COLOR
    )

    try:
        if guild_stats.banner is None:
            banner_img = None
        else:
            banner_img = banner.create_banner(guild_stats.banner["base"],
                                              [(l["colour"], l["pattern"]) for l in guild_stats.banner["layers"]])
            banner_img = banner_img.resize((200, 400), resample=Image.BOX)
    except Exception as e:
        handlers.logging.error(f"Failed to create guild banner for guild {guild.name}!", exc_info=e)
        banner_img = None

    embed.set_thumbnail(url="attachment://banner.png")

    embed.add_field(name="Guild level", value=f"{guild_stats.level} ({guild_stats.xpPercent}%)", inline=True)
    embed.add_field(name="Members", value=guild_stats.members.total, inline=True)
    embed.add_field(name="", value="", inline=True)
    embed.add_field(name="Territories", value=guild_stats.territories, inline=True)
    embed.add_field(name="Total wars", value=guild_stats.wars, inline=True)
    embed.add_field(name="Season rating", value=_get_curr_sr(guild_stats),
                    inline=True)

    embed.add_field(name="", value="⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯", inline=False)

    player_worlds = await wrappers.api.wynncraft.v3.player.player_list(identifier=PlayerIdentifier.UUID)
    online_players = {utils.misc.format_uuid(p.uuid): p for p in
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

    splits = utils.misc.split_str(table_builder.build(), 1000, "\n")
    for split in splits:
        embed.add_field(name=f"Online members ({len(online_members)})", value=f">>> ```\n{split}```")

    return embed, banner_img


class GuildCommand(hybridCommand.HybridCommand):
    def __init__(self):
        super().__init__(
            name="guild",
            aliases=("g",),
            params=[hybridCommand.CommandParam("guild", "The name or tag of the guild.", required=True,
                                               ptype=discord.AppCommandOptionType.string)],
            description="Get a wynncraft guild by its name or tag.",
            base_perms=Permissions().none(),
            permission_lvl=command.PermissionLevel.ANYONE
        )

    async def _execute(self, event: PrefixedCommandEvent):
        async with event.waiting():
            if isinstance(event, PrefixedCommandEvent):
                if len(event.args) < 2:
                    await event.reply_error("Please specify a guild!")
                    return

                guild_str = event.message.content.split(" ", 1)[1]
            elif isinstance(event, SlashCommandEvent):
                guild_str = event.args["guild"]

            try:
                guild = await utils.command.parse_guild(guild_str)
            except utils.command.AmbiguousGuildError as e:
                await event.reply_info(str(e))
                return
            except (ValueError, utils.command.UnknownGuildError) as e:
                await event.reply_error(str(e))
                return

            embed, banner_img = await _create_guild_embed(guild)
            if embed is None:
                await event.reply_error(f"Failed to retrieve stats for guild ``{guild_str}``")
                return

            if banner_img is None:
                await event.reply(embed=embed)
                return

            with io.BytesIO() as image_binary:
                banner_img.save(image_binary, 'PNG')
                image_binary.seek(0)
                file = discord.File(fp=image_binary, filename='banner.png')
                await event.reply(embed=embed, file=file)
