import asyncio
from datetime import datetime, timezone

from discord import Permissions, Embed

import utils.discord
import utils.misc
import wrappers.api.wynncraft.guild
import wrappers.api.wynncraft.player
from dataTypes import CommandEvent
from handlers.commands import command
from wrappers import botConfig, minecraftPlayer


class SeenCommand(command.Command):
    def __init__(self):
        super().__init__(
            name="seen",
            aliases=("ls", "lastseen"),
            usage=f"seen",
            description=f"Get a list of the last join dates for members in {botConfig.GUILD_NAME}.",
            req_perms=Permissions().none(),
            permission_lvl=command.PermissionLevel.STRAT
        )

    async def _execute(self, event: CommandEvent):
        async with event.channel.typing():
            guild = await wrappers.api.wynncraft.guild.stats(botConfig.GUILD_NAME)
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
            names = {uuid: name for uuid, name in
                     await minecraftPlayer.get_players(uuids=[m.uuid for m in guild.members])}
            stats = await asyncio.gather(*tuple(wrappers.api.wynncraft.player.stats(m.uuid) for m in guild.members))

            for m, p in zip(guild.members, stats):
                if p is None:
                    continue
                name = names.get(m.uuid.replace("-", "").lower(), m.name)
                if p.meta.location.online:
                    lastonline[m.rank][name] = (now, f"online({p.meta.location.server})")
                else:
                    last_join = datetime.fromisoformat(p.meta.lastJoin)
                    last_join_str = utils.misc.get_relative_date_str(last_join, days=True, hours=True, minutes=True,
                                                                     seconds=True) + " ago"
                    lastonline[m.rank][name] = (last_join, last_join_str)

                    longest_name_len = max(len(name), longest_name_len)
                    longest_date_len = max(len(last_join_str), longest_date_len)

            for k, v in lastonline.items():
                lastonline[k] = \
                    {name: last_join[1] for name, last_join in
                     sorted(v.items(), key=lambda item: item[1][0])}

            embed = Embed(
                color=botConfig.DEFAULT_COLOR,
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
