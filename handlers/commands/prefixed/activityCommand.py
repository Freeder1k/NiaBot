import asyncio
from datetime import timedelta, datetime, timezone, date
from typing import Iterable

from async_lru import alru_cache
from discord import Permissions, Embed

import wrappers.api.wynncraft.guild
import wrappers.api.wynncraft.v3.guild
import wrappers.storage.playtimeData
from handlers.commands import command
from niatypes.dataTypes import CommandEvent
from niatypes.wynncraft.v3.guild import GuildStats
from utils.tableBuilder import TableBuilder
from wrappers import botConfig, minecraftPlayer


async def _get_playtime(uuid: str, d1: date, d2: date):
    p: minecraftPlayer = await minecraftPlayer.get_player(uuid=uuid)
    if p is None:
        return uuid, 0

    d1 = await wrappers.storage.playtimeData.get_first_date_after_from_uuid(d1, uuid)
    d2 = await wrappers.storage.playtimeData.get_first_date_after_from_uuid(d2, uuid)
    if d1 is None or d2 is None:
        return p.name, 0

    pt1 = await wrappers.storage.playtimeData.get_playtime(uuid, d1)
    pt2 = await wrappers.storage.playtimeData.get_playtime(uuid, d2)

    if pt1 is None or pt2 is None:
        return p.name, 0
    else:
        return p.name, pt2.playtime - pt1.playtime


async def _get_playtimes(uuids: Iterable[str], d1: date, d2: date):
    uuids = [uuid.replace("-", "") for uuid in uuids]

    playtimes = await asyncio.gather(*(_get_playtime(uuid, d1, d2) for uuid in uuids))
    return sorted(playtimes, key=lambda t: t[1], reverse=True)


@alru_cache(ttl=600)
async def _create_activity_embed():
    guild: GuildStats = await wrappers.api.wynncraft.v3.guild.stats(guild_name=botConfig.GUILD_NAME)
    today = datetime.now(timezone.utc).date()
    last_week = today - timedelta(days=7)

    playtimes = {
        "OWNER": await _get_playtimes(guild.members.owner.keys(), last_week, today),
        "CHIEF": await _get_playtimes(guild.members.chief.keys(), last_week, today),
        "STRATEGIST": await _get_playtimes(guild.members.strategist.keys(), last_week, today),
        "CAPTAIN": await _get_playtimes(guild.members.captain.keys(), last_week, today),
        "RECRUITER": await _get_playtimes(guild.members.recruiter.keys(), last_week, today),
        "RECRUIT": await _get_playtimes(guild.members.recruit.keys(), last_week, today)
    }

    embed = Embed(
        color=botConfig.DEFAULT_COLOR,
        title="**Weekly Playtimes in Nia**",
        description='⎯' * 32,
        timestamp=datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
    )
    embed.set_footer(text="Last update")

    tb = TableBuilder.from_str('l r')
    ranks = []
    for k, v in playtimes.items():
        if len(v) == 0:
            continue
        ranks.append(k)
        tb.add_row('$', '$')
        [tb.add_row(t[0], f"{t[1]} min") for t in v]

    tables = tb.build().split(f"${' ' * (tb.get_width() - 2)}$\n")[1:]
    for i, table in enumerate(tables):
        embed.add_field(name=ranks[i], value=f">>> ```\n{table}```", inline=False)

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
