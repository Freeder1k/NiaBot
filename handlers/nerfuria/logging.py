from discord import Embed, Client, TextChannel

import handlers.logging
import utils.misc
from handlers import serverConfig
from niatypes.enums import LogEntryType
from wrappers import botConfig
from wrappers.storage import guildMemberLogData


async def _upload_to_discord(client, embed):
    channel = client.get_channel(serverConfig.get_log_channel_id(botConfig.GUILD_DISCORD))
    if not isinstance(channel, TextChannel):
        print(channel)
        handlers.logging.error("Log channel for guild server is not text channel!")
        return

    perms = channel.permissions_for(channel.guild.me)
    if not perms.send_messages and perms.embed_links:
        print(channel)
        handlers.logging.error("Missing perms for info channel for guild server!")
        return

    await channel.send(embed=embed)


async def log_member_join():
    pass  # TODO


async def log_member_leave():
    pass  # TODO


async def log_member_name_change(client: Client, uuid: str, prev_name: str, new_name: str):
    em = Embed(
        title=f"Name changed: **{prev_name} -> {new_name}**",
        color=botConfig.DEFAULT_COLOR,
    )
    em.set_footer(text=f"UUID: {utils.misc.format_uuid(uuid)}")

    await guildMemberLogData.log(LogEntryType.MEMBER_NAME_CHANGE,
                                 f"Name changed: {prev_name} -> {new_name}",
                                 uuid)

    await _upload_to_discord(client, em)
