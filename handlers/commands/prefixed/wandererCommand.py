from datetime import timedelta, datetime, timezone

from discord import Permissions, Embed

import utils.discord
import utils.misc
import wrappers.api.wynncraft.guild
from handlers.commands import command
from dataTypes import CommandEvent
from wrappers import botConfig, minecraftPlayer


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

    async def _execute(self, event: CommandEvent):
        guild = await wrappers.api.wynncraft.guild.stats(botConfig.GUILD_NAME)

        seven_days_ago = datetime.now(timezone.utc).replace(hour=23, minute=59, second=59) - timedelta(days=7)

        new_members = {}
        old_members = {}

        longest_name_len = 0
        longest_date_len = 0

        names = {uuid: name for uuid, name in await minecraftPlayer.get_players(uuids=[m.uuid for m in guild.members])}

        for m in guild.members:
            if m.rank == "RECRUIT":
                name = names.get(m.uuid.replace("-", "").lower(), m.name)

                join_date = datetime.fromisoformat(m.joined)
                join_date_str = utils.misc.get_relative_date_str(join_date, days=True) + " ago"
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

        utils.discord.add_table_fields(
            base_embed=embed,
            max_l_len=longest_name_len,
            max_r_len=longest_date_len,
            splitter=True,
            fields=[(fname, [(name, join_date) for name, join_date in val.items()]) for fname, val in fields]
        )
        await event.channel.send(embed=embed)
