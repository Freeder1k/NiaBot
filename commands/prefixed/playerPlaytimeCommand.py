import io

import discord
from discord import Permissions, Embed

import storage.playtimeData
from commands import command, commandEvent
import utils.discord
import re
import player
from datetime import datetime
import matplotlib.pyplot as plt
import bot_config

_username_re = re.compile(r'[0-9A-Za-z_]+$')
_uuid_re = re.compile(r'[0-9a-f]+$')

class PlayerPlaytimeCommand(command.Command):
    def __init__(self):
        super().__init__(
            name="playerplaytime",
            aliases=("ppt",),
            usage=f"playerplaytime <username|uuid>",
            description="Get a graph of the playtime for the specified player. The player must have been in Nerfuria.",
            req_perms=Permissions().none(),
            permission_lvl=command.PermissionLevel.ANYONE
        )

    async def _execute(self, event: commandEvent.CommandEvent):
        if len(event.args) < 2:
            await utils.discord.send_error(event.channel, "Please specify a username or uuid!")
            return

        user_str = event.args[1]

        p = None
        if len(user_str) <= 16:
            if _username_re.match(user_str):
                p = await player.get_player(username=user_str)
        else:
            user_str = user_str.replace("-", "").lower()

            if len(user_str) == 32 and _uuid_re.match(user_str):
                p = await player.get_player(uuid=user_str)

        if p is None:
            await utils.discord.send_error(event.channel, f"Couldn't parse user ``{event.args[1]}``")
            return

        playtimes = await storage.playtimeData.get_all_playtimes(p.uuid)

        if len(playtimes) == 0:
            await utils.discord.send_error(event.channel, f"No data found for ``{p.name}``")
            return

        dates = [datetime.strptime(pt.day, '%Y-%m-%d').date() for pt in playtimes]
        values = [pt.playtime/60 for pt in playtimes]


        # Initialize IO
        data_stream = io.BytesIO()

        # fig, ax = plt.subplots()

        plt.plot(dates, values)

        plt.xlabel("Date")
        plt.ylabel("Playtime (hours)")
        plt.xticks(rotation=45)
        plt.grid(True)

        # Save content into the data stream
        plt.savefig(data_stream, format='png', bbox_inches="tight", dpi=80)
        plt.close()

        ## Create file
        # Reset point back to beginning of stream
        data_stream.seek(0)
        chart = discord.File(data_stream, filename="playtime.png")

        embed = Embed(title=f"Playtime for {p.name}", color=bot_config.DEFAULT_COLOR)
        embed.set_image(
            url="attachment://playtime.png"
        )

        await event.channel.send(embed=embed, file=chart)

