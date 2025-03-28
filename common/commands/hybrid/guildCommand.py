import io

import aiohttp.client_exceptions
import discord
from PIL import Image
from async_lru import alru_cache
from discord import Permissions, Embed

import common.api.wynncraft.v3.guild
import common.api.wynncraft.v3.player
import common.api.wynntils
import common.botInstance
import common.logging
import common.storage.usernameData
import common.types.wynncraft
import common.utils.command
import common.utils.misc
from common.commands import hybridCommand, command
from common.commands.commandEvent import PrefixedCommandEvent, SlashCommandEvent, CommandEvent
from common.types.enums import PlayerIdentifier
from common.types.wynncraft import WynncraftGuild
from common.utils import banner, tableBuilder

_star = "★"


def _get_curr_sr(guild_stats: common.types.wynncraft.GuildStats) -> int:
    if not guild_stats.seasonRanks:
        return 0
    curr_season = max(guild_stats.seasonRanks.keys(), key=lambda x: int(x))
    return guild_stats.seasonRanks[curr_season].rating


@alru_cache(ttl=60)
async def _create_guild_embed(guild: WynncraftGuild, color: int):
    guild_stats: common.types.wynncraft.GuildStats
    try:
        guild_stats = await common.api.wynncraft.v3.guild.stats(name=guild.name)
    except (common.api.wynncraft.v3.guild.UnknownGuildException, aiohttp.client_exceptions.ClientResponseError):
        return None, None

    guild_color = await common.api.wynntils.get_guild_color(guild_stats.name)
    if guild_color is not None:
        color = int(guild_color[1:], 16)

    embed = Embed(
        description=f"# [{guild_stats.prefix}] {guild_stats.name}\n"
                    f"Created: {guild_stats.created}\n"
                    f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯",
        color=color
    )

    try:
        if guild_stats.banner is None:
            banner_img = None
        else:
            banner_img = banner.create_banner(guild_stats.banner["base"],
                                              [(l["colour"], l["pattern"]) for l in guild_stats.banner["layers"]])
            banner_img = banner_img.resize((200, 400), resample=Image.Resampling.BOX)
    except Exception as e:
        common.logging.error(f"Failed to create guild banner for guild {guild.name}!", exc_info=e)
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

    player_worlds = await common.api.wynncraft.v3.player.player_list(identifier=PlayerIdentifier.UUID)
    online_players = {common.utils.misc.format_uuid(p.uuid): p for p in
                      await common.storage.usernameData.get_players(uuids=list(player_worlds.keys()))}

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

    splits = common.utils.misc.split_str(table_builder.build(), 1000, "\n")
    for split in splits:
        embed.add_field(name=f"Online members ({len(online_members)})", value=f">>> ```\n{split}```")

    return embed, banner_img


class GuildCommand(hybridCommand.HybridCommand):
    def __init__(self, bot: common.botInstance.BotInstance):
        super().__init__(
            name="guild",
            aliases=("g",),
            params=[hybridCommand.GuildParam()],
            description="Get a wynncraft guild by its name or tag.",
            base_perms=Permissions().none(),
            permission_lvl=command.PermissionLevel.ANYONE,
            bot=bot
        )

    async def _execute(self, event: CommandEvent):
        async with event.waiting():
            if isinstance(event, PrefixedCommandEvent):
                if len(event.args) < 2:
                    await event.reply_error("Please specify a guild!")
                    return

                guild_str = event.message.content.split(" ", 1)[1]
                try:
                    guild = await common.utils.command.parse_guild(guild_str)
                except ValueError as e:
                    await event.reply_error(f"{str(e)}")
                    return
            elif isinstance(event, SlashCommandEvent):
                guild = event.args["guild"]

            color = event.bot.config.DEFAULT_COLOR

            embed, banner_img = await _create_guild_embed(guild, color)

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
