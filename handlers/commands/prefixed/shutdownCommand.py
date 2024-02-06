from discord import Permissions

from handlers.commands import command
from niatypes.dataTypes import PrefixedCommandEvent


class ShutdownCommand(command.Command):
    def __init__(self):
        super().__init__(
            name="shutdown",
            aliases=("stop",),
            usage=f"shutdown",
            description="Shuts down the bot.",
            req_perms=Permissions().none(),
            permission_lvl=command.PermissionLevel.DEV
        )

    async def _execute(self, event: PrefixedCommandEvent):
        await event.channel.send(f":warning: **System shutting down...** :warning:")
        exit(1)
