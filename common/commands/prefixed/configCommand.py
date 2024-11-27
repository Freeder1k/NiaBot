from discord import Permissions, Embed

import common.utils.discord
from common.commands import command
from common.commands.commandEvent import PrefixedCommandEvent


class ConfigCommand(command.Command):
    def __init__(self):
        super().__init__(
            name="config",
            aliases=("settings", "prefs"),
            usage=f"config [option] [value]",
            description="Modify/see server config options.\n"
                        "Valid options are: ``prefix``, ``memberrole``, ``stratrole``, ``chiefrole``, ``logchannel``",
            req_perms=Permissions().none(),
            permission_lvl=command.PermissionLevel.CHIEF
        )

    async def _execute(self, event: PrefixedCommandEvent):
        server_id = event.guild.id

        server_config = event.bot.server_configs.get(server_id)

        if len(event.args) < 2:
            embed = Embed(
                color=event.bot.config.DEFAULT_COLOR,
                title=f"{event.guild.name} Server Config:",
                description=f"- Prefix: ``{server_config.cmd_prefix}``\n"
                            f"- Member Role:  <@&{server_config.member_role_id}>\n"
                            f"- Strat Role: <@&{server_config.strat_role_id}>\n"
                            f"- Chief Role: <@&{server_config.chief_role_id}>\n"
                            f"- Log Channel: <#{server_config.log_channel_id}>"
            )
            await event.channel.send(embed=embed)
            return

        if len(event.args) == 2:
            match event.args[1]:
                case "prefix":
                    await common.utils.discord.send_info(event.channel, f"The current command prefix is: "
                                                                        f"``{server_config.cmd_prefix}``")
                case "memberrole":
                    await common.utils.discord.send_info(event.channel, f"The current member role is: "
                                                                        f"<@&{server_config.member_role_id}>")
                case "stratrole":
                    await common.utils.discord.send_info(event.channel, f"The current strat role is: "
                                                                        f"<@&{server_config.strat_role_id}>")
                case "chiefrole":
                    await common.utils.discord.send_info(event.channel, f"The current chief role is: "
                                                                        f"<@&{server_config.chief_role_id}>")
                case "logchannel":
                    await common.utils.discord.send_info(event.channel, f"The current info channel is: "
                                                                        f"<#{server_config.log_channel_id}>")
                case _:
                    await common.utils.discord.send_error(event.channel, f"Invalid option: {event.args[1]}.\n"
                                                                         f"Valid options are: ``prefix``, ``stratrole``, ``memberrole``, ``logchannel``")
            return

        match event.args[1]:
            case "prefix":
                prefix = event.message.content.split(" ", 2)[2]
                if len(prefix) > 1 and prefix[0] == "\"" and prefix[-1] == "\"":
                    prefix = prefix[1:-1]
                server_config.cmd_prefix = prefix
                await common.utils.discord.send_success(event.channel, f"Set the command prefix to ``{prefix}``")
            case "memberrole":
                role_id = common.utils.discord.parse_id(event.args[2])
                role = event.guild.get_role(role_id)
                if role is None:
                    await common.utils.discord.send_error(event.channel, f"Couldn't parse role: {event.args[2]}\n"
                                                                         f"Please use a role mention or specify the role ID.")
                    return

                server_config.member_role_id = role_id
                await common.utils.discord.send_success(event.channel, f"Set the member role to <@&{role_id}>")
            case "stratrole":
                role_id = common.utils.discord.parse_id(event.args[2])
                role = event.guild.get_role(role_id)
                if role is None:
                    await common.utils.discord.send_error(event.channel, f"Couldn't parse role: {event.args[2]}\n"
                                                                         f"Please use a role mention or specify the role ID.")
                    return

                server_config.strat_role_id = role_id
                await common.utils.discord.send_success(event.channel, f"Set the strat role to <@&{role_id}>")
            case "chiefrole":
                role_id = common.utils.discord.parse_id(event.args[2])
                role = event.guild.get_role(role_id)
                if role is None:
                    await common.utils.discord.send_error(event.channel, f"Couldn't parse role: {event.args[2]}\n"
                                                                         f"Please use a role mention or specify the role ID.")
                    return

                server_config.chief_role_id = role_id
                await common.utils.discord.send_success(event.channel, f"Set the chief role to <@&{role_id}>")
            case "logchannel":
                channel_id = common.utils.discord.parse_id(event.args[2])
                channel = event.guild.get_channel(channel_id)
                if channel is None:
                    await common.utils.discord.send_error(event.channel, f"Couldn't parse channel: {event.args[2]}\n"
                                                                         f"Please use a channel mention or specify the channel ID.")
                    return

                server_config.log_channel_id = channel_id
                await common.utils.discord.send_success(event.channel, f"Set the info channel to <#{channel_id}>")
            case _:
                await common.utils.discord.send_error(event.channel, f"Invalid option: {event.args[1]}.\n"
                                                                     f"Valid options are: ``prefix``, ``stratrole``, ``memberrole``, ``logchannel``")
                return

        event.bot.server_configs.save()
