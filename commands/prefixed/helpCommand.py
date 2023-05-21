from discord import Permissions, Embed

import config
import util
from commands import commandListener, command, commandEvent


class HelpCommand(command.Command):

    def __init__(self):
        super().__init__(
            "help",
            ("?", "h"),
            f"{config.PREFIX}help [command]",
            "Displays the command list or info on a command if one is specified.",
            Permissions().none(),
            command.PermissionLevel.ANYONE
        )

    async def _execute(self, event: commandEvent.CommandEvent):
        commands = commandListener.get_commands()
        if len(event.args) > 1:
            cmd = event.args[1]
            for c in commands:
                if c.is_this_command(cmd):
                    await c.send_help(event.channel)
                    return
            await util.send_error(event.channel, f"Unknown command: ``{cmd}``")
        else:
            help_embed = Embed(
                color=config.DEFAULT_COLOR,
                title="**Help:**",
                description=f"See: ``{config.PREFIX}help <command>`` for help on individual commands.\n"
            )
            anyone = [f"``{c.usage}``" for c in commands if c.permission_lvl == command.PermissionLevel.ANYONE]
            member = [f"``{c.usage}``" for c in commands if c.permission_lvl == command.PermissionLevel.MEMBER]
            mod = [f"``{c.usage}``" for c in commands if c.permission_lvl == command.PermissionLevel.MOD]
            admin = [f"``{c.usage}``" for c in commands if c.permission_lvl == command.PermissionLevel.ADMIN]
            dev = [f"``{c.usage}``" for c in commands if c.permission_lvl == command.PermissionLevel.DEV]

            if len(anyone) > 0:
                help_embed.add_field(name="**General commands:**", value='\n'.join(anyone), inline=False)
            if len(member) > 0:
                help_embed.add_field(name="**Member-only commands:**", value='\n'.join(member), inline=False)
            if len(mod) > 0:
                help_embed.add_field(name="**Moderator commands:**", value='\n'.join(mod), inline=False)
            if len(admin) > 0:
                help_embed.add_field(name="**Admin commands:**", value='\n'.join(admin), inline=False)
            if len(dev) > 0 and event.sender.id == config.DEV_USER_ID:
                help_embed.add_field(name="**Admin commands:**", value='\n'.join(admin), inline=False)

            await event.channel.send(embed=help_embed)
