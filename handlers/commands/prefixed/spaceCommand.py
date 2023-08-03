from datetime import datetime

import aiohttp.client_exceptions
from discord import Permissions, Embed

import utils.discord
import wrappers.api.nasa
from handlers.commands import command
from dataTypes import CommandEvent
from wrappers import botConfig
from wrappers.api.rateLimit import RateLimitException


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
        async with event.channel.typing():
            try:
                apod = await wrappers.api.nasa.get_random_apod()
                while apod.media_type != "image":
                    print("e")
                    apod = await wrappers.api.nasa.get_random_apod()
            except aiohttp.client_exceptions.ClientResponseError as ex:
                await utils.discord.send_error(event.channel,
                                               f"Failed to access Nasa API. Status: {ex.status} ({ex.message})")
                return
            except RateLimitException:
                await utils.discord.send_error(event.channel, f"Rate limited. Please wait a few minutes.")
                return
            except TimeoutError:
                await utils.discord.send_error(event.channel, f"API request timed out. Please try again.")
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
