from datetime import datetime

import aiohttp.client_exceptions
from discord import Permissions, Embed

import common.api.nasa
import common.utils.discord
from common.api.rateLimit import RateLimitException
from common.commands import command
from common.commands import hybridCommand
from common.commands.commandEvent import PrefixedCommandEvent
import common.botInstance


class SpaceCommand(hybridCommand.HybridCommand):
    def __init__(self, bot: common.botInstance.BotInstance):
        super().__init__(
            name="space",
            aliases=(),
            params=[],
            description="Send a random space image from NASA's APOD",
            base_perms=Permissions().none(),
            permission_lvl=command.PermissionLevel.ANYONE,
            bot=bot
        )

    async def _execute(self, event: PrefixedCommandEvent):
        async with event.waiting():
            try:
                apod = await common.api.nasa.get_random_apod()
                while apod.media_type != "image":
                    print("e")
                    apod = await common.api.nasa.get_random_apod()
            except aiohttp.client_exceptions.ClientResponseError as ex:
                await event.reply_error(f"Failed to access Nasa API. Status: {ex.status} ({ex.message})")
                return
            except RateLimitException:
                await event.reply_error(f"Rate limited. Please wait a few minutes.")
                return
            except TimeoutError:
                await event.reply_error(f"API request timed out. Please try again.")
                return

            embed = Embed(
                title=apod.title,
                timestamp=datetime.strptime(apod.date, "%Y-%m-%d"),
                color=event.bot.config.DEFAULT_COLOR,
                url=f"https://apod.nasa.gov/apod/ap{apod.date[2:].replace('-', '')}.html"
            )
            if apod.copyright != "":
                embed.set_footer(text=f"©{apod.copyright}")
            embed.set_image(url=apod.url)

            await event.reply(embed=embed)
