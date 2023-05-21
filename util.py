import datetime
import re
from datetime import datetime

from discord import TextChannel, Embed, Guild, Member, Permissions

import config


def log(*args):
    print(end="\r")
    print("[" + datetime.now().strftime("%H:%M:%S") + "]", *args)
    if config.LOG_FILE != "":
        with open(config.LOG_FILE, 'a') as f:
            print("[" + datetime.now().strftime("%H:%M:%S") + "]", *args, file=f)


def dlog(*args):
    if config.ENABLE_DEBUG:
        print(end="\r")
        print("\033[90m" + "[" + datetime.now().strftime("%H:%M:%S") + "] (DEBUG)", *args, end="\033[97m\n")
        if config.LOG_FILE != "":
            with open(config.LOG_FILE, 'a') as f:
                print("[" + datetime.now().strftime("%H:%M:%S") + "] (DEBUG)", *args, file=f)


def elog(*args):
    print(end="\r")
    print("\033[91m" + "[" + datetime.now().strftime("%H:%M:%S") + "] (ERROR)", *args, end="\033[97m\n")
    if config.LOG_FILE != "":
        with open(config.LOG_FILE, 'a') as f:
            print("[" + datetime.now().strftime("%H:%M:%S") + "] (ERROR)", *args, file=f)


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

    :return: The ID contained in the str or 0 if it couldn't be parsed.
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


def parse_time(time_in_sec: int):
    return str(datetime.timedelta(seconds=time_in_sec))


def get_highest_role(member: Member):
    return member.roles[-1]


def cmp_roles(member1: Member, member2: Member) -> bool:
    """
    Compare the role hierarchy of two members.

    :return bool: True, if member1 has a higher or equal position to member2.
    """
    return get_highest_role(member1) >= get_highest_role(member2)


def get_missing_perms(channel: TextChannel, permissions: Permissions) -> Permissions | None:
    """
    Get all specified permissions the bot is missing in a channel.

    :return: None, if the bot has all the specified perms, otherwise a Permissions object of all the missing perms.
    """
    channel_perms = channel.permissions_for(channel.guild.me)
    if channel_perms <= permissions:
        return None

    return (channel_perms ^ permissions) & permissions
