from datetime import timedelta, datetime, timezone

from discord import Permissions, Embed

import utils.discord
import wrappers.api.wynncraft.guild
import wrappers.storage.playtimeData
from handlers.commands import command
from dataTypes import CommandEvent
from wrappers import botConfig


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
            guild = await wrappers.api.wynncraft.guild.stats("Nerfuria")
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

            names = {uuid: name for uuid, name in await player.get_players(uuids=[m.uuid for m in guild.members])}

            for m in guild.members:
                name = names.get(m.uuid.replace("-", "").lower(), m.name)

                prev_date = await wrappers.storage.playtimeData.get_first_date_after_from_uuid(last_week, m.uuid)
                if prev_date is None:
                    continue
                prev_pt = await wrappers.storage.playtimeData.get_playtime(m.uuid, prev_date)
                today_pt = await wrappers.storage.playtimeData.get_playtime(m.uuid, today)

                if prev_pt is None:
                    playtime = 0
                else:
                    playtime = today_pt.playtime - prev_pt.playtime
                playtimes[m.rank][name] = playtime

                longest_name_len = max(len(name), longest_name_len)
                longest_pt_len = max(len(str(playtime)), longest_pt_len)

            for k, v in playtimes.items():
                playtimes[k] = \
                    {name: playtime for name, playtime in sorted(v.items(), key=lambda item: item[1], reverse=True)}

            embed = Embed(
                color=botConfig.DEFAULT_COLOR,
                title="**Weekly Playtimes in Nia**",
                description='⎯' * 32,
                timestamp=datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
            )

            utils.discord.add_table_fields(
                base_embed=embed,
                max_l_len=longest_name_len,
                max_r_len=longest_pt_len + 4,
                splitter=False,
                fields=[(fname, [(name, f"{playtime} min") for name, playtime in val.items()]) for fname, val in
                        playtimes.items()]
            )

            embed.set_footer(text="Last update")

        await event.channel.send(embed=embed)
