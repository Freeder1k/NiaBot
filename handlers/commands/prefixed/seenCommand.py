from datetime import datetime, timezone

from async_lru import alru_cache
from discord import Permissions, Embed

import utils.discord
import utils.misc
import wrappers.api.wynncraft.v3.guild
import wrappers.api.wynncraft.v3.player
from handlers.commands import command
from handlers.commands.commandEvent import PrefixedCommandEvent
from utils.misc import format_uuid
from wrappers import botConfig, minecraftPlayer
from wrappers.api.wynncraft.v3.types import GuildStats


async def _get_last_seen(uuid: str, _):
    # TODO use player tracking system
    p = await minecraftPlayer.get_player(uuid=uuid)
    if p is None:
        return 'ERROR(P)'
    try:
        stats = await wrappers.api.wynncraft.v3.player.stats(format_uuid(p.uuid))
    except wrappers.api.wynncraft.v3.player.UnknownPlayerException:
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
        return f"{utils.misc.get_relative_date_str(val, days=True, hours=True, minutes=True, seconds=True)} ago"
    else:
        return val


@alru_cache(ttl=600)
async def _create_seen_embed(server_id):
    if server_id == botConfig.GUILD_DISCORD2:
        guild_name = botConfig.GUILD_NAME2
    else:
        guild_name = botConfig.GUILD_NAME

    guild: GuildStats = await wrappers.api.wynncraft.v3.guild.stats(name=guild_name)

    embed = Embed(
        color=botConfig.DEFAULT_COLOR,
        title="**Last Sightings of Nia Members**",
        description='⎯' * 32,
        timestamp=datetime.now(timezone.utc)
    )

    await utils.discord.add_guild_member_tables(
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
        async with event.channel.typing():
            embed = await _create_seen_embed(event.guild.id)
            await event.channel.send(embed=embed)
