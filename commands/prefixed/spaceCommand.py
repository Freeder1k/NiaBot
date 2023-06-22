from datetime import datetime

import aiohttp.client_exceptions
from discord import Permissions, Embed

import api.nasa
import botConfig
import utils.discord
from commands import command
from dataTypes import CommandEvent
from api.rateLimit import RateLimitException


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

    async def _execute(self, event: CommandEvent):
        try:
            apod = await api.nasa.get_random_apod()
            while apod.media_type != "image":
                apod = await api.nasa.get_random_apod()
        except aiohttp.client_exceptions.ClientResponseError as ex:
            await utils.discord.send_error(event.channel, f"Failed to access Nasa API. Status: {ex.status} ({ex.message})")
            return
        except RateLimitException:
            await utils.discord.send_error(event.channel, f"Rate limited. Please wait a few minutes.")
            return

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
