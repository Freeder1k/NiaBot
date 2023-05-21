from abc import ABC, abstractmethod
from enum import Enum

from discord import Permissions, Member, Message, TextChannel, Embed

import config
import util


class PermissionLevel(Enum):
    ANYONE = 0
    MEMBER = 1
    MOD = 2
    ADMIN = 3
    DEV = 4


class Command(ABC):
    def __init__(self, name: str, aliases: list[str], usage: str, description: str, req_perms: Permissions,
                 permission_lvl: PermissionLevel):
        self.name = name.lower()
        self.aliases = [a.lower() for a in aliases]
        self.usage = usage
        self.description = description
        self.req_perms = req_perms
        self.permission_lvl = permission_lvl

    @abstractmethod
    async def _execute(self, message: Message):
        pass

    async def run(self, message: Message):
        if type(message.channel) is not TextChannel:
            return
        if message.webhook_id is not None:
            return
        if message.author.bot:
            return

        if self._allowed_user(message.author):
            if not message.channel.permissions_for(message.guild.me).send_messages():
                return
            if not message.channel.permissions_for(message.guild.me).embed_links():
                await message.channel.send("Please give me the Embed Links permission to run commands.")
                return

            m_perms = util.get_missing_perms(message.channel, self.req_perms)
            if m_perms is not None:
                embed = Embed(
                    color=config.ERROR_COLOR,
                    title="**To use this command please give me the following permission(s):**",
                    description=m_perms
                )
                await message.channel.send(embed=embed)
                return

            # TODO new thread?
            await self._execute(message)

    async def send_help(self, channel: TextChannel):
        help_embed = Embed(
            color=config.DEFAULT_COLOR,
            title=f"**{self.name} command info:**"
        )
        help_embed.add_field(name="**Usage:**", value=f"``{self.usage}``", inline=False)
        if len(self.aliases) > 0:
            help_embed.add_field(name="**Aliases:**", value=', '.join(self.aliases), inline=False)
        help_embed.add_field(name="**Permission level:**", value=str(self.permission_lvl.value), inline=False)
        help_embed.add_field(name="**Description:**", value=self.description, inline=False)
        if self.req_perms != Permissions.none():
            help_embed.add_field(name="**Required permissions:**", value=str(self.req_perms), inline=False)

        await channel.send(embed=help_embed)

    def _allowed_user(self, member: Member) -> bool:
        if self.permission_lvl == PermissionLevel.ANYONE:
            return True
        if self.permission_lvl == PermissionLevel.MEMBER:
            # TODO
            return True
        if self.permission_lvl <= PermissionLevel.MOD:
            # TODO
            return True
        if self.permission_lvl <= PermissionLevel.ADMIN:
            return member.guild_permissions.administrator()
        if self.permission_lvl == PermissionLevel.DEV:
            return member.id == config.DEV_USER_ID

    def is_this_command(self, command: str) -> bool:
        command = command.lower()
        return command == self.name or command in self.aliases
