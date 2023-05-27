from datetime import timedelta, datetime, timezone

from discord import Permissions, Embed

import api.wynncraft.guild
import config
import storage.playtimeData
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

        playtimes = {}

        for m in nia.members:
            prev_pt = await storage.playtimeData.get_playtime(m.uuid, last_week)
            today_pt = await storage.playtimeData.get_playtime(m.uuid, today)

            playtimes[m.name] = today_pt.playtime - (prev_pt.playtime if prev_pt is not None else 0)

        embed = Embed(
            color=config.DEFAULT_COLOR,
            title="Nerfuria playtimes for the last week.",
            description="\n".join((f"**{name}**: {pt}mins" for name, pt in playtimes.items())),
            timestamp=datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
        )
        embed.set_footer(text="Last update")

        await event.channel.send(embed=embed)
