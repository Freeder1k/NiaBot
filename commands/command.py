from abc import ABC, abstractmethod
from enum import Enum
from typing import Collection

from discord import Permissions, Member, TextChannel, Embed

import config
import util
from commands.commandEvent import CommandEvent


class PermissionLevel(Enum):
    ANYONE = 0
    MEMBER = 1
    MOD = 2
    ADMIN = 3
    DEV = 4


class Command(ABC):
    def __init__(self, name: str, aliases: Collection[str], usage: str, description: str, req_perms: Permissions,
                 permission_lvl: PermissionLevel):
        self.name = name.lower()
        self.aliases = tuple(a.lower() for a in aliases)
        self.usage = usage
        self.description = description
        self.req_perms = req_perms
        self.permission_lvl = permission_lvl

    @abstractmethod
    async def _execute(self, command_event: CommandEvent):
        pass

    async def run(self, command_event: CommandEvent):
        if self._allowed_user(command_event.sender):
            if not command_event.channel.permissions_for(command_event.guild.me).send_messages:
                return
            if not command_event.channel.permissions_for(command_event.guild.me).embed_links:
                await command_event.channel.send("Please give me the Embed Links permission to run commands.")
                return

            m_perms = util.get_missing_perms(command_event.channel, self.req_perms)
            if m_perms != Permissions.none():
                embed = Embed(
                    color=config.ERROR_COLOR,
                    title="**To use this command please give me the following permission(s):**",
                    description=[p for p in Permissions.VALID_FLAGS if getattr(m_perms, p)]
                )
                await command_event.channel.send(embed=embed)
                return

            await self._execute(command_event)

    async def send_help(self, channel: TextChannel):
        help_embed = Embed(
            color=config.DEFAULT_COLOR,
            title=f"**{self.name} command info:**"
        )
        help_embed.add_field(name="**Usage:**", value=f"``{self.usage}``", inline=False)
        if len(self.aliases) > 0:
            help_embed.add_field(name="**Aliases:**", value=', '.join(self.aliases), inline=False)
        help_embed.add_field(name="**Permission level:**", value=str(self.permission_lvl.name), inline=False)
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
            return member.guild_permissions.administrator
        if self.permission_lvl == PermissionLevel.DEV:
            return member.id == config.DEV_USER_ID

    def is_this_command(self, command: str) -> bool:
        command = command.lower()
        return command == self.name or command in self.aliases
