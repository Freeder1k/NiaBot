from discord import Permissions, Embed

import common.utils.discord
from common.commands import command
from common.commands.commandEvent import PrefixedCommandEvent


class EvalCommand(command.Command):
    def __init__(self):
        super().__init__(
            name="eval",
            aliases=(),
            usage=f"eval <code>",
            description="Run the specified python code. The CommandEvent is provided as 'event'.",
            req_perms=Permissions().none(),
            permission_lvl=command.PermissionLevel.DEV
        )

    async def _execute(self, event: PrefixedCommandEvent):
        if len(event.args) < 2:
            return

        context = {"event": event}
        code = event.message.content.split(" ", 1)[1]
        if code.startswith("```python\n") and code.endswith("```"):
            code = code[10:-3]

        lines = code.split("\n")
        if lines[-1] == "":
            lines = lines[:-1]
        if len(lines) == 0:
            return
        lines[-1] = "return " + lines[-1]
        lines = ["    " + l for l in lines]

        async with event.waiting():
            try:
                exec("async def f():\n" + '\n'.join(lines), context)
                res = await eval("f()", context)
                if res is not None:
                    await event.reply(embed=Embed(
                        description=f"```{res}```",
                        color=event.bot.config.DEFAULT_COLOR
                    ))
            except Exception as e:
                await event.reply_exception(e)
