from datetime import timedelta, datetime, timezone

import discord.utils
from discord import Permissions, Embed

import math

import api.wynncraft.guild
import api.wynncraft.player
import config
import util

from commands import command, commandEvent


class LastSeenCommand(command.Command):
    def __init__(self):
        super().__init__(
            name="lastseen",
            aliases=("ls"),
            usage=f"{config.PREFIX}lastseen",
            description="Get players last seen in Wynncraft",
            req_perms=Permissions().none(),
            permission_lvl=command.PermissionLevel.ANYONE
        )

    async def _execute(self, event: commandEvent.CommandEvent):
        nia = await api.wynncraft.guild.stats("Nerfuria")
        lastonline = {
            "OWNER": {},
            "CHIEF": {},
            "STRATEGIST": {},
            "CAPTAIN": {},
            "RECRUITER": {},
            "RECRUIT": {}
        }
        
        longest_name_len = 0
        longest_lj_len = 0
        
        for m in nia.members:
            player = await api.wynncraft.player.stats(m.uuid)
            
            try:
                last_Join = datetime.fromisoformat(player.meta.lastJoin)
                print(m.name + ": Last joined " + str(last_Join))
                
                lastonline[m.rank][m.name] = last_Join
                
                longest_name_len = max(len(m.name), longest_name_len)
                longest_lj_len = max(len(str(last_Join)), longest_lj_len)

            except AttributeError:
                print("The 'meta' attribute or 'lastJoin' attribute is not available for " + m.name)
                continue
        
        for k, v in lastonline.items():
            lastonline[k] = \
                {name: lastonline for name, lastonline in sorted(v.items(), key=lambda item: item[1], reverse=True)}
        
        embed = Embed(
            color=config.DEFAULT_COLOR,
            title="**Nerfuria last seen online**",
            description='⎯'*41,
            timestamp=datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
        )
         
        for k, v in lastonline.items():
            text = util.split_str(
                s='\n'.join((
                     f"{name}"
                     f": {discord.utils.format_dt(lo, style='R')}"
                     for name, lo in v.items())),
                length=1000,
                splitter="\n"
            )

            first = True
            for s in text:
                embed.add_field(
                    name=k if first else "",
                    value=f">>> ```\n{s}```",
                    inline=False
                )
                first = False

        embed.set_footer(text="Last update")

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