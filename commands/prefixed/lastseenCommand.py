import asyncio
from datetime import datetime, timezone

from discord import Permissions, Embed

import api.wynncraft.guild
import api.wynncraft.player
import bot_config
import player
import utils.discord
import utils.misc
from commands import command, commandEvent
from api import minecraft


class LastSeenCommand(command.Command):
    def __init__(self):
        super().__init__(
            name="lastseen",
            aliases=("ls", "seen"),
            usage=f"lastseen",
            description="Get players last seen in Wynncraft",
            req_perms=Permissions().none(),
            permission_lvl=command.PermissionLevel.STRAT
        )

    async def _execute(self, event: commandEvent.CommandEvent):
        async with event.channel.typing():
            nia = await api.wynncraft.guild.stats("Nerfuria")
            now = datetime.now(timezone.utc)

            lastonline = {
                "OWNER": {},
                "CHIEF": {},
                "STRATEGIST": {},
                "CAPTAIN": {},
                "RECRUITER": {},
                "RECRUIT": {}
            }

            longest_name_len = 0
            longest_date_len = 0
            players = await player.get_players(uuids=[m.uuid for m in nia.members])
            stats = await asyncio.gather(*tuple(api.wynncraft.player.stats(p.uuid) for p in players))

            for m, p in zip(nia.members, stats):
                if p is None:
                    continue
                if p.meta.location.online:
                    lastonline[m.rank][m.name] = (now, f"online({p.meta.location.server})")
                else:
                    last_join = datetime.fromisoformat(p.meta.lastJoin)
                    last_join_str = utils.misc.get_relative_date_str(last_join, days=True, hours=True, minutes=True,
                                                                     seconds=True) + " ago"
                    lastonline[m.rank][m.name] = (last_join, last_join_str)

                    longest_name_len = max(len(m.name), longest_name_len)
                    longest_date_len = max(len(last_join_str), longest_date_len)

            for k, v in lastonline.items():
                lastonline[k] = \
                    {name: last_join[1] for name, last_join in
                     sorted(v.items(), key=lambda item: item[1][0])}

            embed = Embed(
                color=bot_config.DEFAULT_COLOR,
                title="**Last Sightings of Nia Members**",
                description='⎯' * 35,
            )

            utils.discord.add_table_fields(
                base_embed=embed,
                max_l_len=longest_name_len,
                max_r_len=longest_date_len,
                splitter=False,
                fields=[(fname, [(name, lo_date) for name, lo_date in val.items()]) for fname, val in
                        lastonline.items()]
            )

        await event.channel.send(embed=embed)
