from datetime import timedelta, datetime, timezone

import discord.utils
from discord import Permissions, Embed

import math

import api.wynncraft.guild
import config
import util
from commands import command, commandEvent


class WandererCommand(command.Command):
    def __init__(self):
        super().__init__(
            name="wandererpromote",
            aliases=("wpt",),
            usage=f"{config.PREFIX}wandererpromote",
            description="Get the list of players eligible for Starchild.",
            req_perms=Permissions().none(),
            permission_lvl=command.PermissionLevel.ANYONE,
        )

    async def _execute(self, event: commandEvent.CommandEvent):
        nia = await api.wynncraft.guild.stats("Nerfuria")

        seven_days_ago = datetime.now(timezone.utc).replace(hour=23, minute=59, second=59) - timedelta(days=7)

        new_members = {}
        old_members = {}

        longest_name_len = 0

        for m in nia.members:
            if m.rank == "RECRUIT":
                join_date = datetime.fromisoformat(m.joined)
                if join_date < seven_days_ago:
                    old_members[m.name] = join_date
                else:
                    new_members[m.name] = join_date
                longest_name_len = max(len(m.name), longest_name_len)

        embed = Embed(color=config.DEFAULT_COLOR, )


        old_members_str = "\n".join(
                tuple(
                    f"{name}"
                    f": {'᲼'* max(0, 10 + longest_name_len - len(name) - _date_str_len(date))}"
                    f"{discord.utils.format_dt(date, style='R')}"
                      for name, date in old_members.items()))
        new_members_str = "\n".join(
                tuple(
                    f"{name}"
                    f": {'᲼'* max(0, 10 + longest_name_len - len(name) - _date_str_len(date))}"
                    f"{discord.utils.format_dt(date, style='R')}"
                      for name, date in new_members.items()))
        table_head_str = f"᲼᲼**Name**{'᲼'* min(30, 3 + longest_name_len)}**JOINED**"

        first = True

        for s in util.split_str(old_members_str, 1000, "\n"):
            embed.add_field(
                name="Wanderers eligible for promotion\n" + table_head_str if first else "",
                value=">>> " + s,
                inline=False
            )
            first = False
        first = True
        for s in util.split_str(new_members_str, 1000, "\n"):
            embed.add_field(
                name="Wanderers not eligible for promotion\n" + table_head_str if first else "",
                value=">>> " + s,
                inline=False
            )
            first = False

        await event.channel.send(embed=embed)


def _date_str_len(dt: datetime):
    delta = (datetime.now(timezone.utc) - dt)
    l = 0

    if delta.days >= 2 * 365:
        l += 5 + int(math.log10(delta.days//365)) # years
    elif delta.days >= 365:
        l += 4  # year
    elif delta.days >= 2 * 30:
        l += 6 + int(math.log10(delta.days//30)) # months
    elif delta.days >= 30:
        l += 5  # month
    elif delta.days >= 2:
        l += 4 + int(math.log10(delta.days)) # days
    elif delta.days >= 1:
        l += 3  # day
    elif delta.seconds >= 2 * 60 * 60:
        l += 5 + int(math.log10(delta.seconds//(60*60))) # hours
    elif delta.seconds >= 60 * 60:
        l += 4 # hour
    elif delta.seconds >= 2 * 60:
        l += 7 + int(math.log10(delta.seconds//60)) # minutes
    elif delta.seconds >= 60:
        l += 6 # minute
    elif delta.seconds >= 2:
        l += 7 + int(math.log10(delta.seconds)) # seconds
    else:
        l += 6 # second

    return l