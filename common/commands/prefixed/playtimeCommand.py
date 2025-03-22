import re
from datetime import datetime

from discord import Permissions, Embed

import common.storage.playtimeData
import common.utils.discord
from common.commands import command
from common.commands.commandEvent import PrefixedCommandEvent
from common.utils import minecraftPlayer

_username_re = re.compile(r'[0-9A-Za-z_]+$')
_uuid_re = re.compile(r'[0-9a-f]+$')


class PlaytimeCommand(command.Command):
    def __init__(self):
        super().__init__(
            name="playtime",
            aliases=("pt",),
            usage=f"playtime <username|uuid>",
            description=f"Get a graph of the playtime for the specified guild member.",
            req_perms=Permissions().none(),
            permission_lvl=command.PermissionLevel.ANYONE
        )

    async def _execute(self, event: PrefixedCommandEvent):
        async with event.waiting():
            if len(event.args) < 2:
                await common.utils.discord.send_error(event.channel, "Please specify a username or uuid!")
                return

            user_str = event.args[1]

            p = None
            if len(user_str) <= 16:
                if _username_re.match(user_str):
                    p = await minecraftPlayer.get_player(username=user_str)
            else:
                user_str = user_str.replace("-", "").lower()

                if len(user_str) == 32 and _uuid_re.match(user_str):
                    p = await minecraftPlayer.get_player(uuid=user_str)

            if p is None:
                await common.utils.discord.send_error(event.channel, f"Couldn't parse user ``{event.args[1]}``")
                return

            playtimes = await common.storage.playtimeData.get_all_playtimes(p.uuid)

            if len(playtimes) == 0:
                await common.utils.discord.send_error(event.channel, f"No data found for ``{p.name}``")
                return

            dates = [datetime.strptime(pt.day, '%Y-%m-%d').date() for pt in playtimes]
            values = [pt.playtime / 60 for pt in playtimes]

            chart = common.utils.discord.create_chart(dates, values, "Date", "Playtime (hours)")

            embed = Embed(title=f"Playtime for {p.name}", color=event.bot.config.DEFAULT_COLOR)
            embed.set_image(
                url="attachment://chart.png"
            )

            await event.reply(embed=embed, file=chart)
