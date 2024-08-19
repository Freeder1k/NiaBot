from discord import Embed, Client, TextChannel

from discord.utils import escape_markdown
import common.logging
import common.utils.misc
from common.types.enums import LogEntryType
from common import botConfig
from common.storage import guildMemberLogData, serverConfig

_client: Client = None

async def _upload_to_discord(embed):
    if _client is None:
        return

    channel = _client.get_channel(serverConfig.get_log_channel_id(botConfig.GUILD_DISCORD2))
    if not isinstance(channel, TextChannel):
        print(channel)
        common.logging.error("Log channel for guild server is not text channel!")
        return

    perms = channel.permissions_for(channel.guild.me)
    if not perms.send_messages and perms.embed_links:
        print(channel)
        common.logging.error("Missing perms for info channel for guild server!")
        return

    await channel.send(embed=embed)


async def log_member_join(username: str, uuid: str):
    """
    Log a member join event.
    """
    em = Embed(
        title=f"**{escape_markdown(username)} has joined the guild**",
        color=botConfig.DEFAULT_COLOR,
    )
    em.set_footer(text=f"UUID: {common.utils.misc.format_uuid(uuid)}")

    await guildMemberLogData.log(LogEntryType.MEMBER_JOIN,
                                 f"{escape_markdown(username)} has joined the guild",
                                 uuid)

    await _upload_to_discord(em)


async def log_member_leave(username: str, uuid: str):
    """
    Log a member leave event.
    """
    em = Embed(
        title=f"**{escape_markdown(username)} has left the guild**",
        color=botConfig.DEFAULT_COLOR,
    )
    em.set_footer(text=f"UUID: {common.utils.misc.format_uuid(uuid)}")

    await guildMemberLogData.log(LogEntryType.MEMBER_LEAVE,
                                 f"{escape_markdown(username)} has left the guild",
                                 uuid)

    await _upload_to_discord(em)


async def log_member_name_change(uuid: str, prev_name: str, new_name: str):
    """
    Log a member name change event.
    """
    em = Embed(
        title=f"Name changed: **{escape_markdown(prev_name)} -> {escape_markdown(new_name)}**",
        color=botConfig.DEFAULT_COLOR,
    )
    em.set_footer(text=f"UUID: {common.utils.misc.format_uuid(uuid)}")

    await guildMemberLogData.log(LogEntryType.MEMBER_NAME_CHANGE,
                                 f"Name changed: {prev_name} -> {new_name}",
                                 uuid)

    await _upload_to_discord(em)

def set_client(client: Client):
    """
    Set the client for the logging module.
    """
    global _client
    _client = client
