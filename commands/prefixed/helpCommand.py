from discord import Permissions, Embed

import const
import utils.discord
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
        if len(event.args) > 1:
            cmd = event.args[1]
            cmd_map = commandListener.get_command_map()
            if cmd in cmd_map:
                await cmd_map[cmd].send_help(event.channel)
            else:
                await utils.discord.send_error(event.channel, f"Unknown command: ``{cmd}``")
            return

        commands = commandListener.get_commands()

        help_embed = Embed(
            color=config.DEFAULT_COLOR,
            title="**Help:**",
            description=f"Bot prefix: ``{config.PREFIX}``\n"
                        f"See: ``{config.PREFIX}help <command>`` for help on individual commands.\n"
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
            help_embed.add_field(name="**Dev commands:**", value='\n'.join(dev), inline=False)

        await event.channel.send(embed=help_embed)
