import re

from discord import TextChannel, Embed, Guild, Member

import config


async def send_success(channel: TextChannel, message: str):
    await channel.send(embed=Embed(color=config.SUCCESS_COLOR, description=f"{chr(0x2705)} {message}"))


async def send_error(channel, message: str):
    await channel.send(embed=Embed(color=config.ERROR_COLOR, description=f"{chr(0x274c)} {message}"))


async def send_info(channel, message: str):
    await channel.send(embed=Embed(color=config.INFO_COLOR, description=f":information_source: {message}"))


async def send_exception(channel, exception: Exception):
    await channel.send(embed=Embed(
        color=config.ERROR_COLOR,
        title=f"A wild {type(exception)} appeared!",
        description=str(exception))
    )


mention_reg = re.compile(r"\\?<(?:#|@[!&]?)(\d+)>")


def parse_id(input_str: str) -> int:
    """
    Parse the ID of a discord mention.

    :return int: The ID contained in the str or 0 if it couldn't be parsed.
    """
    match = mention_reg.fullmatch(input_str)
    if match:
        return int(match.group(1))
    else:
        return 0


def parse_member(guild: Guild, input_str: str) -> Member | None:
    """
    Get a member specified by a String (raw ID, mention, discord name or nickname).

    :return: The member if found otherwise None
    """
    if input_str.isnumeric():
        m = guild.get_member(int(input_str))
        if m is not None:
            return m

    parsed_id = parse_id(input_str)
    if parsed_id != 0:
        m = guild.get_member(parsed_id)
        if m is not None:
            return m

    return guild.get_member_named(input_str)


def parse_name(nickname: str):
    """
    Get the minecraft name out of a nickname.

    :param nickname:  This should be in the form "RANK NAME".
    :return: The name if found otherwise ""
    """
    return nickname.split(" ")[-1]

"""/**
     * Get an easy readable time from ann amount in seconds.
     *
     * @param timeInSec The time in seconds.
     * @return The time in days, hours, minutes, seconds.
     */"""


def parseTime(timeInSec: int):
    pass
    """    List<String> time = new LinkedList<>();
        time.add(timeInSec / (60 * 60 * 24 * 365) + "y");
        time.add(timeInSec / (60 * 60 * 24) % 365 + "d");
        time.add((timeInSec / (60 * 60)) % 24 + "h");
        time.add((timeInSec / 60) % 60 + "m");
        time.add(timeInSec % 60 + "s");
        time.removeIf(v -> v.charAt(0) == '0');
        if (time.size() == 0)
            return "0s";
        return String.join(", ", time);
    }"""

    """/**
     * Get the highest role of a user.
     *
     * @param member The member to parse.
     * @return The highest {@link Role role} of the specified member or null if the member doesn't have any roles.
     */"""


def getHighestRoleFrom(member):
    pass
    """    List<Role> roles = member.getRoles();
        if (roles.isEmpty()) {
            return null;
        }

        return roles.stream().min((first, second) -> {
            if (first.getPosition() == second.getPosition()) {
                return 0;
            }
            return first.getPosition() > second.getPosition() ? -1 : 1;
        }).get();
    }"""

    """/**
     * Check if a member1 has a higher role than the bot.
     *
     * @param member1   The member to check for a higher role.
     * @param member2   The member to check against.
     * @return True, if member1 has a higher (or equally high) role than member2.
     */"""


def hasHigherRole(member1, member2):
    pass
    """
        Role roleUser = getHighestRoleFrom(member1);
        Role roleSelf = getHighestRoleFrom(member2);
        if(roleSelf == null)
            return true;
        if(roleUser == null)
            return false;
        return roleUser.getPosition() >= roleSelf.getPosition();
    }"""

    """/**
     * Returns a list containing all specified permissions the bot is missing in a channel.
     *
     * @param channel The channel to check.
     * @return A list containing the missing permissions.
     */"""


def missingPerms(channel, permissions):
    pass
    """    LinkedList<Permission> missingPerms = new LinkedList<>();

        for (Permission p : permissions) {
            if (!channel.getGuild().getSelfMember().hasPermission(channel, p))
                missingPerms.add(p);
        }
        return missingPerms;
    }"""
