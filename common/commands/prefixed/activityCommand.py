import time
from datetime import timedelta, datetime, timezone

from async_lru import alru_cache
from discord import Permissions, Embed

import common.api.wynncraft.v3.guild
import common.storage.playerTrackerData
import common.storage.playtimeData
import common.utils.discord
from common.commands import command
from common.commands.commandEvent import PrefixedCommandEvent
from common.types.wynncraft import GuildStats
from workers.playtimeTracker import main_access_private_members


@alru_cache(ttl=600)
async def _create_activity_embed(bot_config, weeks):
    guild_name = bot_config.GUILD_NAME
    guild: GuildStats = await common.api.wynncraft.v3.guild.stats(name=guild_name)

    after_date = datetime.now(timezone.utc).date() - timedelta(days=7*weeks)

    t1 = time.time()
    playtime_data = await common.storage.playerTrackerData.get_playtimes_for_guild(guild.name, after_date)
    t2 = time.time()

    async def get_playtime(uuid, _):
        uuid = uuid.lower().replace("-", "")
        if uuid in main_access_private_members.get(guild_name, set()):
            return 'PRIVATE'
        if uuid not in playtime_data:
            return '0 min'
        return f"{int(playtime_data[uuid] * 60)} min"

    embed = Embed(
        color=bot_config.DEFAULT_COLOR,
        title=f"**Playtimes in {guild_name}** in the last {weeks} week(s)",
        description='⎯' * 32,
        timestamp=datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
    )
    embed.set_footer(text=f"Query took {t2 - t1:.2f}s.")

    await common.utils.discord.add_guild_member_tables(
        base_embed=embed,
        guild=guild,
        data_function=get_playtime,
        sort_function=lambda t: int(t[:-4]),
        sort_reverse=True
    )

    return embed


class ActivityCommand(command.Command):
    def __init__(self):
        super().__init__(
            name="activity",
            aliases=("act",),
            usage=f"activity [weeks]",
            description=f"Get the playtime of all members in the guild for the past specified amount of weeks.",
            req_perms=Permissions().none(),
            permission_lvl=command.PermissionLevel.STRAT
        )

    async def _execute(self, event: PrefixedCommandEvent):
        async with event.waiting():
            if len(event.args) >= 2:
                weeks = int(event.args[1])
            else:
                weeks = 1
            embed = await _create_activity_embed(event.bot.config, weeks)
            await event.reply(embed=embed)
