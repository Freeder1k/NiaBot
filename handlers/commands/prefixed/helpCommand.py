from discord import Permissions, Embed

import utils.discord
from handlers.commands import commandListener, command
from niatypes.dataTypes import CommandEvent
from wrappers import botConfig
from handlers import serverConfig


class HelpCommand(command.Command):

    def __init__(self):
        super().__init__(
            "help",
            ("?", "h"),
            f"help [command]",
            "Displays the command list or info on a command if one is specified.",
            Permissions().none(),
            command.PermissionLevel.ANYONE
        )

    async def _execute(self, event: CommandEvent):
        if len(event.args) > 1:
            cmd = event.args[1]
            cmd_map = commandListener.get_command_map()
            if cmd in cmd_map:
                await cmd_map[cmd].send_help(event.channel)
            else:
                await utils.discord.send_error(event.channel, f"Unknown command: ``{cmd}``")
            return

        commands = commandListener.get_commands()
        cmd_prefix = serverConfig.get_cmd_prefix(event.guild.id)

        help_embed = Embed(
            color=botConfig.DEFAULT_COLOR,
            title="**Help:**",
            description=f"Bot prefix: ``{cmd_prefix}``\n"
                        f"See: ``{cmd_prefix}help <command>`` for help on individual commands.\n"
        )
        anyone = [f"``{cmd_prefix}{c.usage}``" for c in commands if c.permission_lvl == command.PermissionLevel.ANYONE]
        member = [f"``{cmd_prefix}{c.usage}``" for c in commands if c.permission_lvl == command.PermissionLevel.MEMBER]
        mod = [f"``{cmd_prefix}{c.usage}``" for c in commands if c.permission_lvl == command.PermissionLevel.STRAT]
        admin = [f"``{cmd_prefix}{c.usage}``" for c in commands if c.permission_lvl == command.PermissionLevel.CHIEF]
        dev = [f"``{cmd_prefix}{c.usage}``" for c in commands if c.permission_lvl == command.PermissionLevel.DEV]

        if len(anyone) > 0:
            help_embed.add_field(name="**General Commands:**", value='\n'.join(anyone), inline=False)
        if len(member) > 0:
            help_embed.add_field(name="**Member-Only Commands:**", value='\n'.join(member), inline=False)
        if len(mod) > 0:
            help_embed.add_field(name="**Strat+ Commands:**", value='\n'.join(mod), inline=False)
        if len(admin) > 0:
            help_embed.add_field(name="**Chief Commands:**", value='\n'.join(admin), inline=False)
        if len(dev) > 0 and event.sender.id in botConfig.DEV_USER_IDS:
            help_embed.add_field(name="**Dev Commands:**", value='\n'.join(dev), inline=False)

        await event.channel.send(embed=help_embed)
