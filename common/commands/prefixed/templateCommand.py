from discord import Permissions

from common.commands import command
from common.commands.commandEvent import PrefixedCommandEvent


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

    async def _execute(self, event: PrefixedCommandEvent):
        pass
