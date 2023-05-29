import dataclasses
import datetime
import re
import typing
from datetime import datetime, timezone

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


def get_missing_perms(channel: TextChannel, permissions: Permissions) -> Permissions:
    """
    Get all specified permissions the bot is missing in a channel.

    :return: None, if the bot has all the specified perms, otherwise a Permissions object of all the missing perms.
    """
    channel_perms = channel.permissions_for(channel.guild.me)

    return (channel_perms ^ permissions) & permissions


def from_dict(cls, json: dict):
    """
    Convert a dictionary to the specified dataclass.

    :param cls: the dataclass type to convert to
    :param json: the (nested) dictionary corresponding to the cls
    :return: an instance of cls
    """
    if not dataclasses.is_dataclass(cls):
        raise TypeError(f"{cls} is not a dataclass!")

    fieldtypes = {f.name: f.type for f in dataclasses.fields(cls)}
    fields = {}
    for f in fieldtypes:
        fields[f] = _f_d_inner(fieldtypes[f], json[f])
    return cls(**fields)


def _f_d_inner(cls, json):
    if type(json) == list:
        return [_f_d_inner(cls.__args__[0], j) for j in json]
    elif isinstance(cls, type):
        if dataclasses.is_dataclass(cls):
            return from_dict(cls, json)
        elif cls == typing.Any:
            return json
        elif isinstance(json, cls):
            return json
    else:
        elog(f"Couldn't determine type of {json} in {cls} in dict conversion.")
        return json


def split_str(s: str, length: int, splitter: chr) -> list[str]:
    res = []
    i = 0
    while True:
        start = i
        i += length

        # At end of string
        if i >= len(s):
            res.append(s[start:i])
            return res

        # Back up until splitter
        while s[i - 1] != splitter:
            i -= 1
        res.append(s[start:i])


def get_relative_date_str(dt: datetime, years=False, months=False, weeks=False, days=False, hours=False, minutes=False,
                          seconds=False) -> str:
    """
    Get a string of the date relative to today in the form "x time".
     The boolean parameters indicate if that specific time form should be enabled.
    """
    delta = (datetime.now(timezone.utc) - dt)

    if years and delta.days >= 2 * 365:
        return f"{delta.days // 365} years"
    elif years and delta.days >= 365:
        return "1 year"
    elif months and delta.days >= 2 * 30:
        return f"{delta.days // 30} months"
    elif months and delta.days >= 30:
        return "1 month"
    elif weeks and delta.days >= 2 * 7:
        return f"{delta.days // 7} weeks"
    elif weeks and delta.days >= 7:
        return "1 week"
    elif days and delta.days >= 2:
        return f"{delta.days} days"
    elif days and delta.days >= 1:
        return "1 day"

    elif hours and delta.seconds >= 2 * 60 * 60:
        return f"{delta.seconds // (60 * 60)} hours"
    elif hours and delta.seconds >= 60 * 60:
        return "1 hour"
    elif minutes and delta.seconds >= 2 * 60:
        return f"{delta.seconds // 60} minutes"
    elif minutes and delta.seconds >= 60:
        return "1 minute"
    elif seconds and delta.seconds >= 2:
        return f"{delta.seconds} seconds"
    elif seconds and delta.seconds >= 1:
        return "1 second"
    else:
        return ""


def add_table_fields(base_embed: Embed, max_l_len: int, max_r_len: int, splitter: bool,
                     fields: typing.Iterable[tuple[str, list[tuple[str, str]]]]):
    """
    Create an embed in the form of a table.

    :param base_embed: The base embed to add the fields to
    :param fields: The fields of the embed in the form: ``(field_name, [(left_entry, right_entry),...])``
    :param max_l_len: The max length of the left entries
    :param max_r_len: The max length of the right entries
    """
    embed = base_embed
    space_num = max(0, 25 - max_l_len - max_r_len)

    first_field = True

    for field in fields:
        if splitter and not first_field:
            embed.add_field(name='⎯' * 32, value='', inline=False)
        else:
            first_field = False

        name = field[0]
        val = "\n".join([f"{l_val:<{max_l_len}} {' ' * space_num}{r_val:>{max_r_len}}"
                         for l_val, r_val in field[1]])

        first = True
        for s in split_str(val, 1000, '\n'):
            embed.add_field(
                name=name if first else "",
                value=">>> ```\n" + s + "```",
                inline=False
            )
            first = False
