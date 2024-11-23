import discord
from discord import Permissions, Embed

from common.botInstance import BotInstance
from common.commands import command
from common.commands.commandEvent import PrefixedCommandEvent
from common.commands.hybridCommand import HybridCommand, CommandParam


class HelpCommand(HybridCommand):
    def __init__(self, bot: BotInstance):
        super().__init__(
            name="help",
            aliases=("?", "h"),
            params=[CommandParam("cmd", "The name of a command.",
                                 required=False, ptype=discord.AppCommandOptionType.string)],
            description="Displays the command list or info on a command if one is specified.",
            base_perms=Permissions().none(),
            permission_lvl=command.PermissionLevel.ANYONE,
            bot=bot
        )

    async def _execute(self, event: PrefixedCommandEvent):
        if len(event.args) > 1:
            cmd = event.args[1]
            cmd_map = event.bot.get_command_map()
            if cmd in cmd_map:
                await cmd_map[cmd].man(event)
            else:
                await event.reply_error(f"Unknown command: ``{cmd}``")
            return

        commands = event.bot.get_commands()
        cmd_prefix = event.bot.server_configs.get(event.guild.id).cmd_prefix

        help_embed = Embed(
            color=event.bot.config.DEFAULT_COLOR,
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
        if len(dev) > 0 and event.sender.id in event.bot.config.DEV_USER_IDS:
            help_embed.add_field(name="**Dev Commands:**", value='\n'.join(dev), inline=False)

        await event.reply(embed=help_embed)
