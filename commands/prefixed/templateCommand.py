from discord import Permissions

from commands import command
from dataTypes import CommandEvent


class TemplateCommand(command.Command):
    def __init__(self):
        super().__init__(
            name="cmd",
            aliases=(),
            usage=f"cmd [args]",
            description="",
            req_perms=Permissions().none(),
            permission_lvl=command.PermissionLevel.ANYONE
        )

    async def _execute(self, event: CommandEvent):
        pass
