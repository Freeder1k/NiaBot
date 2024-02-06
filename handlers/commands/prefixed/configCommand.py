from discord import Permissions, Embed

import utils.discord
from handlers.commands import command
from niatypes.dataTypes import PrefixedCommandEvent
from wrappers import botConfig
from handlers import serverConfig


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

        if len(event.args) < 2:
            embed = Embed(
                color=botConfig.DEFAULT_COLOR,
                title=f"{event.guild.name} Server Config:",
                description=f"- Prefix: ``{serverConfig.get_cmd_prefix(server_id)}``\n"
                            f"- Member Role:  <@&{serverConfig.get_member_role_id(server_id)}>\n"
                            f"- Strat Role: <@&{serverConfig.get_strat_role_id(server_id)}>\n"
                            f"- Chief Role: <@&{serverConfig.get_chief_role_id(server_id)}>\n"
                            f"- Log Channel: <#{serverConfig.get_log_channel_id(server_id)}>"
            )
            await event.channel.send(embed=embed)
            return

        if len(event.args) == 2:
            match event.args[1]:
                case "prefix":
                    await utils.discord.send_info(event.channel, f"The current command prefix is: "
                                                                 f"``{serverConfig.get_cmd_prefix(server_id)}``")
                case "memberrole":
                    await utils.discord.send_info(event.channel, f"The current member role is: "
                                                                 f"<@&{serverConfig.get_member_role_id(server_id)}>")
                case "stratrole":
                    await utils.discord.send_info(event.channel, f"The current strat role is: "
                                                                 f"<@&{serverConfig.get_strat_role_id(server_id)}>")
                case "chiefrole":
                    await utils.discord.send_info(event.channel, f"The current chief role is: "
                                                                 f"<@&{serverConfig.get_chief_role_id(server_id)}>")
                case "logchannel":
                    await utils.discord.send_info(event.channel, f"The current info channel is: "
                                                                 f"<#{serverConfig.get_log_channel_id(server_id)}>")
                case _:
                    await utils.discord.send_error(event.channel, f"Invalid option: {event.args[1]}.\n"
                                                                  f"Valid options are: ``prefix``, ``stratrole``, ``memberrole``, ``logchannel``")
            return

        match event.args[1]:
            case "prefix":
                prefix = event.message.content.split(" ", 2)[2]
                if len(prefix) > 1 and prefix[0] == "\"" and prefix[-1] == "\"":
                    prefix = prefix[1:-1]
                await serverConfig.set_cmd_prefix(server_id, prefix)
                await utils.discord.send_success(event.channel, f"Set the command prefix to ``{prefix}``")
            case "memberrole":
                role_id = utils.discord.parse_id(event.args[2])
                role = event.guild.get_role(role_id)
                if role is None:
                    await utils.discord.send_error(event.channel, f"Couldn't parse role: {event.args[2]}\n"
                                                                  f"Please use a role mention or specify the role ID.")
                    return

                await serverConfig.set_member_role_id(server_id, role_id)
                await utils.discord.send_success(event.channel, f"Set the member role to <@&{role_id}>")
            case "stratrole":
                role_id = utils.discord.parse_id(event.args[2])
                role = event.guild.get_role(role_id)
                if role is None:
                    await utils.discord.send_error(event.channel, f"Couldn't parse role: {event.args[2]}\n"
                                                                  f"Please use a role mention or specify the role ID.")
                    return

                await serverConfig.set_strat_role_id(server_id, role_id)
                await utils.discord.send_success(event.channel, f"Set the strat role to <@&{role_id}>")
            case "chiefrole":
                role_id = utils.discord.parse_id(event.args[2])
                role = event.guild.get_role(role_id)
                if role is None:
                    await utils.discord.send_error(event.channel, f"Couldn't parse role: {event.args[2]}\n"
                                                                  f"Please use a role mention or specify the role ID.")
                    return

                await serverConfig.set_chief_role_id(server_id, role_id)
                await utils.discord.send_success(event.channel, f"Set the chief role to <@&{role_id}>")
            case "logchannel":
                channel_id = utils.discord.parse_id(event.args[2])
                channel = event.guild.get_channel(channel_id)
                if channel is None:
                    await utils.discord.send_error(event.channel, f"Couldn't parse channel: {event.args[2]}\n"
                                                                  f"Please use a channel mention or specify the channel ID.")
                    return

                await serverConfig.set_log_channel_id(server_id, channel_id)
                await utils.discord.send_success(event.channel, f"Set the info channel to <#{channel_id}>")
            case _:
                await utils.discord.send_error(event.channel, f"Invalid option: {event.args[1]}.\n"
                                                              f"Valid options are: ``prefix``, ``stratrole``, ``memberrole``, ``logchannel``")
