from discord import Permissions

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
            await common.utils.discord.send_error(event.channel, "Please specify a strike!")
            return

        if not event.args[1].isnumeric():
            await common.utils.discord.send_error(event.channel, "Strike ID must be a number!")
            return

        strike_id = int(event.args[1])

        strike = await common.wrappers.storage.strikeData.get_strike_by_id(strike_id)
        if strike is None:
            await common.utils.discord.send_error(event.channel, f"Couldn't find Strike with ID ``{strike_id}``!")
            return
        if strike.pardoned:
            await common.utils.discord.send_info(event.channel, f"Strike is already pardoned.")
            return

        await common.wrappers.storage.strikeData.pardon_strike(strike_id)

        await common.utils.discord.send_success(event.channel,
                                         f"Pardoned strike with ID ``{strike_id}`` for <@{strike.user_id}>")
