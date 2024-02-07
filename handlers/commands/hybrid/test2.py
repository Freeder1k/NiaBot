import discord
from discord import Permissions

from handlers.commands.command import PermissionLevel
from handlers.commands.hybridCommand import HybridCommand, CommandParam


class Test2Command(HybridCommand):
    def __init__(self):
        super().__init__(
            name="test2",
            aliases=[],
            params=[
                CommandParam(
                    name="test",
                    description="Test parameter",
                    required=False,
                    default="asdf",
                    ptype=discord.AppCommandOptionType.string
                )
            ],
            description="Test command 2",
            base_perms=Permissions().none(),
            permission_lvl=PermissionLevel.ANYONE,
        )

    async def _execute(self, event):
        await event.interaction.response.send_message(f"Test command2 {event.args}")
