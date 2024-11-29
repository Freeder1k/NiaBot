from discord import Permissions

import common.storage.strikeData
import common.utils.discord
from common.commands import command
from common.commands.commandEvent import PrefixedCommandEvent


class UnstrikeCommand(command.Command):
    def __init__(self):
        super().__init__(
            name="unstrike",
            aliases=(),
            usage=f"unstrike <strike ID>",
            description="Pardon a specific strike.",
            req_perms=Permissions().none(),
            permission_lvl=command.PermissionLevel.CHIEF
        )

    async def _execute(self, event: PrefixedCommandEvent):
        if len(event.args) < 2:
            await event.reply_error("Please specify a strike!")
            return

        if not event.args[1].isnumeric():
            await event.reply_error("Strike ID must be a number!")
            return

        strike_id = int(event.args[1])

        strike = await common.storage.strikeData.get_strike_by_id(strike_id)
        if strike is None:
            await event.reply_error(f"Couldn't find Strike with ID ``{strike_id}``!")
            return
        if strike.pardoned:
            await event.reply_info(f"Strike is already pardoned.")
            return

        await common.storage.strikeData.pardon_strike(strike_id)

        await event.reply_success(f"Pardoned strike with ID ``{strike_id}`` for <@{strike.user_id}>")
