from datetime import timedelta, datetime, timezone

from async_lru import alru_cache
from discord import Permissions, Embed

import common.api.wynncraft.v3.guild
import common.storage.playtimeData
import common.utils.discord
from common.commands import command
from common.commands.commandEvent import PrefixedCommandEvent
from common.types.wynncraft import GuildStats


async def _get_playtime(uuid: str, _):
    uuid = uuid.replace(" - ", "")
    today = datetime.now(timezone.utc).date()
    last_week = today - timedelta(days=7)

    d1 = await common.storage.playtimeData.get_first_date_after_from_uuid(today, uuid)
    d2 = await common.storage.playtimeData.get_first_date_after_from_uuid(last_week, uuid)
    if d1 is None or d2 is None:
        return '0 min'

    pt1 = await common.storage.playtimeData.get_playtime(uuid, d1)
    pt2 = await common.storage.playtimeData.get_playtime(uuid, d2)

    if pt1 is None or pt2 is None:
        return '0 min'
    else:
        return f'{(pt1.playtime - pt2.playtime)} min'


@alru_cache(ttl=600)
async def _create_activity_embed(bot_config):
    guild: GuildStats = await common.api.wynncraft.v3.guild.stats(name=bot_config.GUILD_NAME)

    embed = Embed(
        color=bot_config.DEFAULT_COLOR,
        title=f"**Weekly Playtimes in {bot_config.GUILD_NAME}**",
        description='⎯' * 32,
        timestamp=datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
    )
    embed.set_footer(text="Last update")

    await common.utils.discord.add_guild_member_tables(
        base_embed=embed,
        guild=guild,
        data_function=_get_playtime,
        sort_function=lambda t: int(t[:-4]),
        sort_reverse=True
    )

    return embed


class ActivityCommand(command.Command):
    def __init__(self):
        super().__init__(
            name="activity",
            aliases=("act",),
            usage=f"activity",
            description=f"Get the playtime of all members in the guild for the past week.",
            req_perms=Permissions().none(),
            permission_lvl=command.PermissionLevel.STRAT
        )

    async def _execute(self, event: PrefixedCommandEvent):
        async with event.waiting():
            embed = await _create_activity_embed(event.bot.config)
            await event.reply(embed=embed)
