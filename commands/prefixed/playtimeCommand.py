from datetime import timedelta, datetime, timezone

from discord import Permissions, Embed

import api.wynncraft.guild
import config
import storage.playtimeData
import util
from commands import command, commandEvent


class PlaytimeCommand(command.Command):
    def __init__(self):
        super().__init__(
            name="playtime",
            aliases=("pt",),
            usage=f"{config.PREFIX}playtime",
            description="Get the playtime of all members in the past week.",
            req_perms=Permissions().none(),
            permission_lvl=command.PermissionLevel.ANYONE
        )

    async def _execute(self, event: commandEvent.CommandEvent):
        nia = await api.wynncraft.guild.stats("Nerfuria")
        today = datetime.now(timezone.utc).date()
        last_week = today - timedelta(days=7)

        playtimes = {
            "OWNER": {},
            "CHIEF": {},
            "STRATEGIST": {},
            "CAPTAIN": {},
            "RECRUITER": {},
            "RECRUIT": {}
        }

        longest_name_len = 0
        longest_pt_len = 0

        for m in nia.members:
            prev_date = await storage.playtimeData.get_first_date_after_from_uuid(last_week, m.uuid)
            if prev_date is None:
                continue
            prev_pt = await storage.playtimeData.get_playtime(m.uuid, prev_date)
            today_pt = await storage.playtimeData.get_playtime(m.uuid, today)

            playtime = today_pt.playtime - prev_pt.playtime
            playtimes[m.rank][m.name] = playtime

            longest_name_len = max(len(m.name), longest_name_len)
            longest_pt_len = max(len(str(playtime)), longest_pt_len)

        for k, v in playtimes.items():
            playtimes[k] = \
                {name: playtime for name, playtime in sorted(v.items(), key=lambda item: item[1], reverse=True)}

        embed = Embed(
            color=config.DEFAULT_COLOR,
            title="**Nerfuria playtimes for the last week**",
            description='⎯'*41,
            timestamp=datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
        )

        for k, v in playtimes.items():
            text = util.split_str(
                s='\n'.join((f'{name:<{longest_name_len}}'
                             f' {" " * max(0, (30 - longest_name_len - longest_pt_len))}'
                             f'{pt:>{longest_pt_len}} min'
                             for name, pt in v.items())
                            ),
                length=1000,
                splitter="\n"
            )

            first = True
            for s in text:
                embed.add_field(
                    name=k if first else "",
                    value=f">>> ```\n{s}```",
                    inline=False
                )
                first = False

        embed.set_footer(text="Last update")

        await event.channel.send(embed=embed)