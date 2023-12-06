from datetime import timedelta, datetime, timezone

from async_lru import alru_cache
from discord import Permissions, Embed

import utils.discord
import wrappers.api.wynncraft.guild
import wrappers.api.wynncraft.v3.guild
import wrappers.storage.playtimeData
from handlers.commands import command
from niatypes.dataTypes import CommandEvent
from wrappers import botConfig
from wrappers.api.wynncraft.v3.types import GuildStats


async def _get_playtime(uuid: str, _):
    uuid = uuid.replace(" - ", "")
    today = datetime.now(timezone.utc).date()
    last_week = today - timedelta(days=7)

    d1 = await wrappers.storage.playtimeData.get_first_date_after_from_uuid(today, uuid)
    d2 = await wrappers.storage.playtimeData.get_first_date_after_from_uuid(last_week, uuid)
    if d1 is None or d2 is None:
        return '0 min'

    pt1 = await wrappers.storage.playtimeData.get_playtime(uuid, d1)
    pt2 = await wrappers.storage.playtimeData.get_playtime(uuid, d2)

    if pt1 is None or pt2 is None:
        return '0 min'
    else:
        return f'{pt1.playtime - pt2.playtime} min'


@alru_cache(ttl=600)
async def _create_activity_embed():
    guild: GuildStats = await wrappers.api.wynncraft.v3.guild.stats(name=botConfig.GUILD_NAME)

    embed = Embed(
        color=botConfig.DEFAULT_COLOR,
        title="**Weekly Playtimes in Nia**",
        description='⎯' * 32,
        timestamp=datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
    )
    embed.set_footer(text="Last update")

    await utils.discord.add_guild_member_tables(
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
            description=f"Get the playtime of all members in {botConfig.GUILD_NAME} for the past week.",
            req_perms=Permissions().none(),
            permission_lvl=command.PermissionLevel.STRAT
        )

    async def _execute(self, event: CommandEvent):
        async with event.channel.typing():
            embed = await _create_activity_embed()
            await event.channel.send(embed=embed)
