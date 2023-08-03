from datetime import datetime, timezone

from dateutil.relativedelta import relativedelta
from discord import Permissions, Embed

import utils.discord
import wrappers.storage.strikeData
from commands import command
from dataTypes import CommandEvent
from wrappers import botConfig


class StrikesCommand(command.Command):
    def __init__(self):
        super().__init__(
            name="strikes",
            aliases=("liststrikes"),
            usage=f"strikes <user>",
            description="Get the strikes for a user.",
            req_perms=Permissions().none(),
            permission_lvl=command.PermissionLevel.CHIEF
        )

    async def _execute(self, event: CommandEvent):
        if len(event.args) < 2:
            await utils.discord.send_error(event.channel, "Please specify a user!")
            return

        user_id = utils.discord.parse_id(event.args[1])
        if user_id == 0:
            await utils.discord.send_error(event.channel, f"Couldn't parse user: ``{event.args[1]}``.\n"
                                                          f"Please specify a user ID or mention them with the command.")
            return

        strikes = await wrappers.storage.strikeData.get_strikes(user_id, event.guild.id)

        if len(strikes) == 0:
            await utils.discord.send_info(event.channel, f"<@{user_id}> has no strikes.")
            return

        name = str(user_id)
        user = event.guild.get_member(user_id)
        if user is not None:
            name = user.display_name
        else:
            user = event.client.get_user(user_id)
            if user is not None:
                name = user.name

        embed = Embed(
            title=f"Strikes for {name}",
            color=botConfig.DEFAULT_COLOR,
            timestamp=datetime.now(timezone.utc)
        )

        two_months_ago = (datetime.now(timezone.utc).date() + relativedelta(months=-2)).strftime('%Y-%m-%d')

        for strike in strikes[:19]:
            expired = two_months_ago > strike.strike_date
            embed.add_field(
                name=f"Strike ID: {strike.strike_id}",
                value=f"Date: {strike.strike_date}\n"
                      f"Reason: ``{strike.reason}``\n"
                      f"Pardoned: {'True' if strike.pardoned else 'False'}\n"
                      f"Expired: {'True' if expired else 'False'}",
                inline=True
            )

        if len(strikes) > 19:
            embed.add_field(name=f"And {len(strikes) - 19} more...", value="", inline=False)

        await event.channel.send(embed=embed)
