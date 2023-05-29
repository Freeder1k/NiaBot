from datetime import timedelta, datetime, timezone

from discord import Permissions, Embed

import api.wynncraft.guild
import config
import util
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

        seven_days_ago = datetime.now(timezone.utc).replace(hour=23, minute=59, second=59) - timedelta(days=7)

        new_members = {}
        old_members = {}

        longest_name_len = 0
        longest_date_len = 0

        for m in nia.members:
            if m.rank == "RECRUIT":
                join_date = datetime.fromisoformat(m.joined)
                join_date_str = util.get_relative_date_str(join_date) + " ago"
                if join_date < seven_days_ago:
                    old_members[m.name] = join_date_str
                else:
                    new_members[m.name] = join_date_str
                longest_name_len = max(len(m.name), longest_name_len)
                longest_date_len = max(len(join_date_str), longest_date_len)

        table_head_str = f"_ _ _ _ _ _ NAME {'_ ' * 44}JOINED"
        fields = (("**Wanderers eligible for promotion**\n\n" + table_head_str, old_members),
                  ("**Wanderers not eligible for promotion**\n\n" + table_head_str, new_members))

        embed = Embed(color=config.DEFAULT_COLOR, )

        util.add_table_fields(
            base_embed=embed,
            max_l_len=longest_name_len,
            max_r_len=longest_date_len,
            splitter=True,
            fields=[(fname, [(name, join_date) for name, join_date in val.items()]) for fname, val in fields]
        )
        await event.channel.send(embed=embed)
