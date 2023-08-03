from abc import ABC, abstractmethod
from enum import IntEnum
from typing import Collection

from discord import Permissions, Member, TextChannel, Embed

import utils.discord
from dataTypes import CommandEvent
from wrappers import serverConfig, botConfig


class PermissionLevel(IntEnum):
    ANYONE = 0
    MEMBER = 1
    STRAT = 2
    CHIEF = 3
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
        if not command_event.channel.permissions_for(command_event.guild.me).send_messages:
            return

        if not command_event.channel.permissions_for(command_event.guild.me).embed_links:
            await command_event.channel.send("Please give me the Embed Links permission to run commands.")
            return

        if not self._allowed_user(command_event.sender):
            await utils.discord.send_error(command_event.channel,
                                           f"This command is only available for {self.permission_lvl.name}s.")
            return

        m_perms = utils.discord.get_missing_perms(command_event.channel, self.req_perms)
        if m_perms != Permissions.none():
            embed = Embed(
                color=botConfig.ERROR_COLOR,
                title="**To use this command please give me the following permission(s):**",
                description=[p for p in Permissions.VALID_FLAGS if getattr(m_perms, p)]
            )
            await command_event.channel.send(embed=embed)
            return

        await self._execute(command_event)

    async def send_help(self, channel: TextChannel):
        help_embed = Embed(
            color=botConfig.DEFAULT_COLOR,
            title=f"**{self.name.capitalize()} Command Info:**"
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
        if member.id in botConfig.DEV_USER_IDS:
            return True

        if self.permission_lvl == PermissionLevel.ANYONE:
            return True

        if self.permission_lvl == PermissionLevel.MEMBER:
            member_role = serverConfig.get_member_role_id(member.guild.id)
            if member.get_role(member_role) is not None:
                return True

        if self.permission_lvl <= PermissionLevel.STRAT:
            strat_role = serverConfig.get_strat_role_id(member.guild.id)
            if member.get_role(strat_role) is not None:
                return True

        if self.permission_lvl <= PermissionLevel.CHIEF:
            if member.guild_permissions.administrator:
                return True
            chief_role = serverConfig.get_chief_role_id(member.guild.id)
            if member.get_role(chief_role) is not None:
                return True

        if self.permission_lvl == PermissionLevel.DEV:
            return False

    def is_this_command(self, command: str) -> bool:
        command = command.lower()
        return command == self.name or command in self.aliases
