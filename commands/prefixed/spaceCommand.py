from datetime import datetime

from discord import Permissions, Embed

import api.nasa
import botConfig
from commands import command, commandEvent


class SpaceCommand(command.Command):
    def __init__(self):
        super().__init__(
            name="space",
            aliases=(),
            usage=f"space",
            description="Send a random space image from NASA's APOD",
            req_perms=Permissions().none(),
            permission_lvl=command.PermissionLevel.ANYONE
        )

    async def _execute(self, event: commandEvent.CommandEvent):
        apod = await api.nasa.get_random_apod()
        while apod.media_type != "image":
            apod = await api.nasa.get_random_apod()

        embed = Embed(
            title=apod.title,
            timestamp=datetime.strptime(apod.date, "%Y-%m-%d"),
            color=botConfig.DEFAULT_COLOR,
            url=f"https://apod.nasa.gov/apod/ap{apod.date[2:].replace('-', '')}.html"
        )
        if apod.copyright != "":
            embed.set_footer(text=f"©{apod.copyright}")
        embed.set_image(url=apod.url)
        await event.channel.send(embed=embed)
