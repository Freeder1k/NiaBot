import asyncio
import os
from datetime import datetime, timezone

from async_lru import alru_cache
from discord import Permissions, Embed

import common.api.wynncraft.v3.guild
import common.api.wynncraft.v3.player
import common.storage.playerTrackerData
import common.utils.discord
import common.utils.misc
from common.commands import command
from common.commands.commandEvent import PrefixedCommandEvent
from common.types.enums import PlayerStatsIdentifier, PlayerIdentifier
from common.types.wynncraft import GuildStats
from common.utils import minecraftPlayer
from common.utils.misc import format_uuid
from workers.playtimeTracker import online_status_private_members

from dotenv import load_dotenv
load_dotenv()

async def _get_last_seen(uuid: str, api_key: str = None) -> datetime | str:
    p = await minecraftPlayer.get_player(uuid=uuid)
    if p is None:
        return 'ERROR(P)'
    try:
        stats = await common.api.wynncraft.v3.player.stats(format_uuid(p.uuid), api_key=api_key)
    except common.api.wynncraft.v3.player.UnknownPlayerException:
        print(p, uuid)
        return 'ERROR(S)'

    if stats.online:
        return f"online({stats.server})"
    last_join = stats.lastJoin
    if last_join is None:
        return 'PRIVATE'
    return datetime.fromisoformat(last_join).astimezone(timezone.utc)


def _last_seen_sort_key(val):
    if isinstance(val, str):
        if val.startswith('ERROR'):
            return -1.0
        if val == 'PRIVATE':
            return -2.0
        return datetime.now().timestamp()
    if isinstance(val, datetime):
        return val.timestamp()
    return -3.0


def _get_seen_display_value(val):
    if isinstance(val, datetime):
        return f"{common.utils.misc.get_relative_date_str(val, days=True, hours=True, minutes=True, seconds=True)} ago"
    elif val is None:
        return "PRIVATE"
    else:
        return val


@alru_cache(ttl=300)
async def _create_seen_embed(guild_name, color):
    guild: GuildStats = await common.api.wynncraft.v3.guild.stats(name=guild_name)

    guild_name = guild.name
    if guild_name == "Nerfuria":
        api_key = os.getenv('WYNN_NIA_API_KEY')
        uuids = list(uuid.replace('-', '') for uuid in guild.members.all.keys())
        data = {}
        for i in range(0, len(uuids), 100):
            batch = await asyncio.gather(*(_get_last_seen(uuid, api_key) for uuid in uuids[i:i + 100]))
            data.update(dict(zip(uuids[i:i + 100], batch)))
            if i + 100 < len(uuids):
                await asyncio.sleep(61)  # Avoid rate limiting
    else:
        data = await common.storage.playerTrackerData.get_stats_for_guild(guild_name, PlayerStatsIdentifier.LAST_LEAVE)

    online = await common.api.wynncraft.v3.player.player_list(PlayerIdentifier.UUID)

    if guild_name == "Nerfuria":
        async def data_function(p_uuid, _):
            return data[p_uuid.replace('-', '')]
    else:
        async def data_function(p_uuid, _):
            if p_uuid in online:
                return f"Online({online[p_uuid]})"
            p_uuid = p_uuid.replace('-', '')
            if p_uuid not in data:
                return "ERROR"
            if p_uuid in online_status_private_members.get(guild_name, set()):
                return "PRIVATE"
            if data[p_uuid] is None:
                return "PRIVATE"
            return datetime.fromisoformat(data[p_uuid]).astimezone(timezone.utc)

    embed = Embed(
        color=color,
        title=f"**Last Sightings of {guild_name} Members**",
        description='⎯' * 32,
        timestamp=datetime.now(timezone.utc)
    )

    await common.utils.discord.add_guild_member_tables(
        base_embed=embed,
        guild=guild,
        data_function=data_function,
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
            await event.reply_info("Processing... Please wait 1 minute.")
            embed = await _create_seen_embed(event.bot.config.GUILD_NAME, event.bot.config.DEFAULT_COLOR)
            await event.reply(embed=embed)
