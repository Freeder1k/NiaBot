from abc import ABC, abstractmethod

from discord import Permissions

from commands.permissionLevel import PermissionLevel


class Command(ABC):
    def __init__(self, name: str, aliases: list[str], usage: str, description: str, req_perms: list[Permissions],
                 permission_lvl: PermissionLevel):
        self.name = name.lower()
        self.aliases = [a.lower() for a in aliases]
        self.usage = usage
        self.description = description
        self.req_perms = req_perms
        self.permission_lvl = permission_lvl

    @abstractmethod
    def _execute(self, command_event):
        pass

    def run(self, event):
        # TODO
        pass

    def send_help(self, channel):
        # TODO
        pass

    def _allowed_user(self, member):
        # TODO
        pass

    def __eq__(self, other):
        # TODO
        pass

    def _get_missing_perms(self, channel):
        # TODO
        pass
