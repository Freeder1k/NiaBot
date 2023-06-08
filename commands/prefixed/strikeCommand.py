from datetime import datetime, timezone

from dateutil.relativedelta import relativedelta
from discord import Permissions, Embed, Forbidden

import bot_config
import utils.discord
from commands import command, commandEvent
from storage import strikeData


def _get_num_ending(num: int) -> str:
    if num == 1:
        return "st"
    if num == 2:
        return "nd"
    if num == 3:
        return "rd"
    return "th"


class StrikeCommand(command.Command):
    def __init__(self):
        super().__init__(
            name="strike",
            aliases=(),
            usage=f"strike <user> [reason]",
            description="Hand out a strike to a user.\n- <user> can be either a discord mention or a user ID",
            req_perms=Permissions().none(),
            permission_lvl=command.PermissionLevel.CHIEF
        )

    async def _execute(self, event: commandEvent.CommandEvent):
        if len(event.args) < 2:
            await utils.discord.send_error(event.channel, "Please specify a user!")
            return

        member = event.guild.get_member(utils.discord.parse_id(event.args[1]))
        if member is None:
            await utils.discord.send_error(event.channel, f"Unknown user: {event.args[1]}")
            return

        reason = "None"
        if len(event.args) > 2:
            reason = event.message.content.split(" ", 2)[2]

        date_today = datetime.now(timezone.utc).date()

        await strikeData.add_strike(member.id, event.guild.id, date_today, reason)

        strike_amount = len(await strikeData.get_unpardoned_strikes_after(member.id, event.guild.id, date_today + relativedelta(months=-2)))

        embed = Embed(
            title=f"You were striked in {event.guild.name}!",
            color=bot_config.DEFAULT_COLOR,
            description=f"Reason: ``{reason}``\n"
                        f"This is your {strike_amount}{_get_num_ending(strike_amount)} strike in 2 months!\n"
                        f"{'At 3 strikes you will be banned.' if strike_amount < 3 else 'As this is your 3rd strike you will be banned!'}",
            timestamp=datetime.now(timezone.utc)
        )

        failed_str = ""
        try:
            await member.send(embed=embed)
        except Forbidden:
            failed_str = "\n Note: couldn't DM the user."

        await utils.discord.send_success(event.channel, f"Striked {member.mention} for ``{reason}``.\n"
                                                        f"This is their {strike_amount}{_get_num_ending(strike_amount)} strike in 2 months.\n"
                                                        f"{failed_str}")
