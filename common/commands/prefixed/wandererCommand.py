from datetime import timedelta, datetime, timezone

from discord import Permissions, Embed

import common.utils.discord
import common.utils.misc
import common.api.wynncraft.v3.guild
from common.commands import command
from common.commands.commandEvent import PrefixedCommandEvent
from common import botConfig
from common.utils import minecraftPlayer


class WandererCommand(command.Command):
    def __init__(self):
        super().__init__(
            name="wandererpromote",
            aliases=("wpt",),
            usage=f"wandererpromote",
            description="Get the list of recruits eligible for promotion.",
            req_perms=Permissions().none(),
            permission_lvl=command.PermissionLevel.STRAT,
        )

    async def _execute(self, event: PrefixedCommandEvent):
        if event.guild.id == botConfig.GUILD_DISCORD2:
            guild_name = botConfig.GUILD_NAME2
        else:
            guild_name = botConfig.GUILD_NAME

        guild = await common.api.wynncraft.v3.guild.stats(name=guild_name)

        seven_days_ago = datetime.now(timezone.utc).replace(hour=23, minute=59, second=59) - timedelta(days=7)

        new_members = {}
        old_members = {}

        longest_name_len = 0
        longest_date_len = 0

        names = {uuid: name for uuid, name in
                 await minecraftPlayer.get_players(uuids=[uuid for uuid in guild.members.recruit.keys()])}

        for uuid, m in guild.members.recruit.items():
            name = names.get(uuid.replace("-", "").lower(), m.username)

            join_date = datetime.fromisoformat(m.joined)
            join_date_str = common.utils.misc.get_relative_date_str(join_date, days=True) + " ago"
            if join_date < seven_days_ago:
                old_members[name] = join_date_str
            else:
                new_members[name] = join_date_str
            longest_name_len = max(len(name), longest_name_len)
            longest_date_len = max(len(join_date_str), longest_date_len)

        content_with = max(0, 25 - longest_name_len - longest_date_len) + longest_name_len + longest_date_len
        table_head_space = int((((content_with * 7.7) + 14 - 39 - 49) // 6)) * 2
        table_head_str = f"_ _ _ _ _ _ NAME{'_ ' * table_head_space}JOINED"
        fields = (("**Wanderers eligible for promotion**\n\n" + table_head_str, old_members),
                  ("**Wanderers not eligible for promotion**\n\n" + table_head_str, new_members))

        embed = Embed(color=botConfig.DEFAULT_COLOR, )

        common.utils.discord.add_table_fields(
            base_embed=embed,
            max_l_len=longest_name_len,
            max_r_len=longest_date_len,
            splitter=True,
            fields=[(fname, [(name, join_date) for name, join_date in val.items()]) for fname, val in fields]
        )
        await event.channel.send(embed=embed)
