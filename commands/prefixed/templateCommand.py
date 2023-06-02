from discord import Permissions

import const
from commands import command, commandEvent


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

    async def _execute(self, event: commandEvent.CommandEvent):
        pass
