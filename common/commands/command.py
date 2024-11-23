from __future__ import annotations

from abc import ABC, abstractmethod
from enum import IntEnum
from typing import Collection

from discord import Permissions, Member, Embed

import common.utils.discord
from common import botInstance
from common.commands.commandEvent import CommandEvent


class PermissionLevel(IntEnum):
    ANYONE = 0
    MEMBER = 1
    STRAT = 2
    CHIEF = 3
    DEV = 4


class Command(ABC):
    """
    Base class for all commands. This class should be inherited and the _execute method should be overridden to
    create a new command. The run method should not be overridden.
    """

    def __init__(self, name: str, aliases: Collection[str], usage: str, description: str, req_perms: Permissions,
                 permission_lvl: PermissionLevel):
        self.name = name.lower()
        self.aliases = tuple(a.lower() for a in aliases)
        self.usage = usage
        self.description = description
        self.req_perms = req_perms
        self.permission_lvl = permission_lvl

    @abstractmethod
    async def _execute(self, event: CommandEvent):
        """
        This method should be overridden to create a new command. This method is called when the command is run.
        """
        pass

    async def run(self, event: CommandEvent):
        """
        Runs the command and checks if the user has the required permissions to run the command.
        """
        if not event.channel.permissions_for(event.guild.me).send_messages:
            return

        if not event.channel.permissions_for(event.guild.me).embed_links:
            await event.reply("Please give me the Embed Links permission to run commands.")
            return

        if not self._allowed_user(event.sender, event.bot):
            await event.reply_error(f"This command is only available for {self.permission_lvl.name}s.")
            return

        m_perms = common.utils.discord.get_missing_perms(event.channel, self.req_perms)
        if m_perms != Permissions.none():
            embed = Embed(color=event.bot.config.ERROR_COLOR,
                title="**To use this command please give me the following permission(s):**",
                description=[p for p in Permissions.VALID_FLAGS if getattr(m_perms, p)])
            await event.reply(embed=embed)
            return

        await self._execute(event)

    async def man(self, event: CommandEvent):
        """
        Sends an embed with information about the command to the specified channel.
        """
        embed = Embed(color=event.bot.config.DEFAULT_COLOR, title=f"**{self.name.capitalize()} Command Info:**")
        embed.add_field(name="**Usage:**", value=f"``{self.usage}``", inline=False)
        if len(self.aliases) > 0:
            embed.add_field(name="**Aliases:**", value=', '.join(self.aliases), inline=False)
        embed.add_field(name="**Permission level:**", value=str(self.permission_lvl.name), inline=False)
        embed.add_field(name="**Description:**", value=self.description, inline=False)
        if self.req_perms != Permissions.none():
            embed.add_field(name="**Required permissions:**", value=str(self.req_perms), inline=False)

        await event.reply(embed=embed)

    def _allowed_user(self, member: Member, bot: botInstance.BotInstance) -> bool:
        if member.id in bot.config.DEV_USER_IDS:
            return True

        if self.permission_lvl == PermissionLevel.ANYONE:
            return True

        if self.permission_lvl == PermissionLevel.MEMBER:
            member_role = bot.server_configs.get(member.guild.id).member_role_id
            if member.get_role(member_role) is not None:
                return True

        if self.permission_lvl <= PermissionLevel.STRAT:
            strat_role = bot.server_configs.get(member.guild.id).strat_role_id
            if member.get_role(strat_role) is not None:
                return True

        if self.permission_lvl <= PermissionLevel.CHIEF:
            if member.guild_permissions.administrator:
                return True

            chief_role = bot.server_configs.get(member.guild.id).chief_role_id
            if member.get_role(chief_role) is not None:
                return True

        return False

    def is_this_command(self, command: str) -> bool:
        """
        Returns True if the given command string corresponds to this command or one of its aliases.
        """
        command = command.lower()
        return command == self.name or command in self.aliases
