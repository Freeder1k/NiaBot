from datetime import timedelta, datetime, timezone

from dateutil.parser import parse

from discord import Permissions, Embed, utils

import api.wynncraft.guild
import config
from commands import command, commandEvent


class WandererCommand(command.Command):
    def __init__(self):
        super().__init__(
            name="wandererpromote",
            aliases=("wpt",),
            usage=f"{config.PREFIX}wandererpromote",
            description="Get the list of players eligible for Starchild.",
            req_perms=Permissions().none(),
            permission_lvl=command.PermissionLevel.ANYONE,
        )

    async def _execute(self, event: commandEvent.CommandEvent):
        nia = await api.wynncraft.guild.stats("Nerfuria")
        today = datetime.now(timezone.utc).date()
        seven_days_ago = today - timedelta(days=7)

        playtimes = {}

        for m in nia.members:
            if m.rank == "RECRUIT":
                if parse(m.joinedFriendly).date() <= seven_days_ago:
                    playtimes[m.name] = m.joinedFriendly

        embed = Embed(
            color=config.DEFAULT_COLOR,
            title="Wanderers eligible for Starchild",
            description="\n".join(
                (
                    f"**{name}**: {joinedFriendly}"
                    for name, joinedFriendly in playtimes.items()
                )
            ),
        )
        embed.set_footer(text="Last update")

        await event.channel.send(embed=embed)
