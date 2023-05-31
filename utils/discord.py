import re
import typing

from discord import TextChannel, Embed, Guild, Member, Permissions

import const
from utils.misc import split_str

mention_reg = re.compile(r"\\?<(?:#|@[!&]?)(\d+)>")


async def send_success(channel: TextChannel, message: str):
    await channel.send(embed=Embed(color=const.SUCCESS_COLOR, description=f"{chr(0x2705)} {message}"))


async def send_error(channel: TextChannel, message: str):
    await channel.send(embed=Embed(color=const.ERROR_COLOR, description=f"{chr(0x274c)} {message}"))


async def send_info(channel: TextChannel, message: str):
    await channel.send(embed=Embed(color=const.INFO_COLOR, description=f":information_source: {message}"))


async def send_exception(channel: TextChannel, exception: Exception):
    await channel.send(embed=Embed(
        color=const.ERROR_COLOR,
        title=f"A wild {type(exception)} appeared!",
        description=str(exception))
    )


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
