from discord import Client
from discord import Embed, TextChannel
from discord.utils import escape_markdown

import common.logging
import common.utils.misc
from common.botConfig import BotConfig
from common.storage import guildMemberLogData, serverConfig
from common.types.enums import LogEntryType


class GuildLogger:
    def __init__(self, client: Client, bot_config: BotConfig):
        self.client = client
        self.bot_config = bot_config

    async def _upload_to_discord(self, embed):
        channel_id = serverConfig.get_log_channel_id(self.bot_config.GUILD_DISCORD)
        if channel_id == 0:
            return
        channel = self.client.get_channel(channel_id)
        if not isinstance(channel, TextChannel):
            print(channel)
            common.logging.error("Log channel for guild server is not text channel!")
            return

        perms = channel.permissions_for(channel.guild.me)
        if not perms.send_messages and perms.embed_links:
            print(channel)
            common.logging.error("Missing perms for log channel for guild server!")
            return

        await channel.send(embed=embed)

    async def log_member_join(self, username: str, uuid: str):
        """
        Log a member join event.
        """
        em = Embed(
            title=f"**{escape_markdown(username)} has joined the guild**",
            color=self.bot_config.DEFAULT_COLOR,
        )
        em.set_footer(text=f"UUID: {common.utils.misc.format_uuid(uuid)}")

        await guildMemberLogData.log(LogEntryType.MEMBER_JOIN,
                                     f"{escape_markdown(username)} has joined the guild",
                                     uuid)

        await self._upload_to_discord(em)

    async def log_member_leave(self, username: str, uuid: str):
        """
        Log a member leave event.
        """
        em = Embed(
            title=f"**{escape_markdown(username)} has left the guild**",
            color=self.bot_config.DEFAULT_COLOR,
        )
        em.set_footer(text=f"UUID: {common.utils.misc.format_uuid(uuid)}")

        await guildMemberLogData.log(LogEntryType.MEMBER_LEAVE,
                                     f"{escape_markdown(username)} has left the guild",
                                     uuid)

        await self._upload_to_discord(em)

    async def log_member_name_change(self, uuid: str, prev_name: str, new_name: str):
        """
        Log a member name change event.
        """
        em = Embed(
            title=f"Name changed: **{escape_markdown(prev_name)} -> {escape_markdown(new_name)}**",
            color=self.bot_config.DEFAULT_COLOR,
        )
        em.set_footer(text=f"UUID: {common.utils.misc.format_uuid(uuid)}")

        await guildMemberLogData.log(LogEntryType.MEMBER_NAME_CHANGE,
                                     f"Name changed: {prev_name} -> {new_name}",
                                     uuid)

        await self._upload_to_discord(em)
