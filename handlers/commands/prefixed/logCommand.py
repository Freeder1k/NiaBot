from datetime import timedelta, datetime, timezone

import discord.utils
from discord import Permissions, Embed

import utils.discord
import utils.misc
from handlers.commands import command
from niatypes.dataTypes import CommandEvent
from wrappers import botConfig
from wrappers.storage import guildMemberLogData


class LogCommand(command.Command):
    def __init__(self):
        super().__init__(
            name="info",
            aliases=("l",),
            usage=f"info [<amount> <timeframe>]",
            description="Get a list of info entries.\n"
                        "- ``amount`` must be an integer\n"
                        "- ``timeframe`` must be either ``d`` or ``m`` (days/months)",
            req_perms=Permissions().none(),
            permission_lvl=command.PermissionLevel.STRAT,
        )

    async def _execute(self, event: CommandEvent):
        td = timedelta(days=7)

        if len(event.args) < 2:
            pass

        if len(event.args) == 2:
            timearg = event.args[1]
            if not timearg.endswith("d") or timearg.endswith("m"):
                await utils.discord.send_error(event.channel, f"Couldn't parse time ``{timearg}``!")
                return

            try:
                amount = int(timearg[:-1])
            except ValueError:
                await utils.discord.send_error(event.channel, f"Couldn't parse time ``{timearg}``!")
                return

            if timearg.endswith("d"):
                td = timedelta(days=amount)
            elif timearg.endswith("m"):
                td = timedelta(days=amount * 30)
            else:
                await utils.discord.send_error(event.channel, f"Couldn't parse timeframe ``{timearg[-1]}``!")
                return

        if len(event.args) > 2:
            try:
                amount = int(event.args[1])
            except ValueError:
                await utils.discord.send_error(event.channel, f"Couldn't parse time amount ``{event.args[1]}``!")
                return

            if event.args[2] == "d":
                td = timedelta(days=amount)
            elif event.args[2] == "m":
                td = timedelta(days=amount * 30)
            else:
                await utils.discord.send_error(event.channel, f"Couldn't parse timeframe ``{event.args[2]}``!")
                return

        time = datetime.now(timezone.utc) - td
        logs = await guildMemberLogData.get_logs(after=time)

        if len(logs) == 0:
            await utils.discord.send_info(event.channel,
                                          f"No info entries found since {discord.utils.format_dt(time, style='D')}.")
            return

        text = "```" + \
               "```$```".join(f"[{entry.timestamp}] {entry.content}" for entry in logs) + \
               "```"

        embed = Embed(
            title=f"Guild Logs since {discord.utils.format_dt(time, style='D')}",
            color=botConfig.DEFAULT_COLOR,
        )

        content = utils.misc.split_str(text, 1000, "$")
        content = [s.replace("$", " ") for s in content]
        for s in content[:25]:
            embed.add_field(name="", value=s, inline=False)

        await event.channel.send(embed=embed)
