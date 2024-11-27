from datetime import datetime, timezone

from async_lru import alru_cache
from discord import Permissions, Embed

import common.utils.discord
import common.utils.misc
import common.api.wynncraft.v3.guild
import common.api.wynncraft.v3.player
from common.commands import command
from common.commands.commandEvent import PrefixedCommandEvent
from common.utils import minecraftPlayer
from common.utils.misc import format_uuid
from common import botConfig
from common.types.wynncraft import GuildStats


async def _get_last_seen(uuid: str, _):
    # TODO use player tracking system
    p = await minecraftPlayer.get_player(uuid=uuid)
    if p is None:
        return 'ERROR(P)'
    try:
        stats = await common.api.wynncraft.v3.player.stats(format_uuid(p.uuid))
    except common.api.wynncraft.v3.player.UnknownPlayerException:
        print(p, uuid)
        return 'ERROR(S)'

    if stats.online:
        return f"online({stats.server})"
    else:
        return datetime.fromisoformat(stats.lastJoin)


def _last_seen_sort_key(val):
    if isinstance(val, str):
        if val.startswith('ERROR'):
            return -1.0
        return datetime.now().timestamp()
    if isinstance(val, datetime):
        return val.timestamp()
    return -2.0


def _get_seen_display_value(val):
    if isinstance(val, datetime):
        return f"{common.utils.misc.get_relative_date_str(val, days=True, hours=True, minutes=True, seconds=True)} ago"
    else:
        return val


@alru_cache(ttl=600)
async def _create_seen_embed(guild_name, color):
    guild: GuildStats = await common.api.wynncraft.v3.guild.stats(name=guild_name)

    embed = Embed(
        color=color,
        title=f"**Last Sightings of {guild_name} Members**",
        description='⎯' * 32,
        timestamp=datetime.now(timezone.utc)
    )

    await common.utils.discord.add_guild_member_tables(
        base_embed=embed,
        guild=guild,
        data_function=_get_last_seen,
        display_function=_get_seen_display_value,
        sort_function=_last_seen_sort_key,
        sort_reverse=True
    )

    return embed


class SeenCommand(command.Command):
    def __init__(self):
        super().__init__(
            name="seen",
            aliases=("ls", "lastseen"),
            usage=f"seen",
            description=f"Get a list of the last join dates for members in the guild.",
            req_perms=Permissions().none(),
            permission_lvl=command.PermissionLevel.STRAT
        )

    async def _execute(self, event: PrefixedCommandEvent):
        async with event.waiting():
            embed = await _create_seen_embed(event.bot.config.GUILD_NAME, event.bot.config.DEFAULT_COLOR)
            await event.reply(embed=embed)
