import asyncio
import io
import re
import typing

import discord
from discord import TextChannel, Embed, Guild, Member, Permissions
from matplotlib import pyplot as plt

import wrappers.minecraftPlayer
from utils.misc import split_str
from utils.tableBuilder import TableBuilder
from wrappers import botConfig
from wrappers.api.wynncraft.v3.types import GuildStats

mention_reg = re.compile(r"\\?<(?:#|@[!&]?)(\d+)>")


# TODO remove redundant

async def send(channel: TextChannel, message: str):
    await channel.send(embed=Embed(color=botConfig.DEFAULT_COLOR, description=message))


async def send_success(channel: TextChannel, message: str):
    await channel.send(embed=Embed(color=botConfig.SUCCESS_COLOR, description=f"{chr(0x2705)} {message}"))


async def send_error(channel: TextChannel, message: str):
    await channel.send(embed=Embed(color=botConfig.ERROR_COLOR, description=f"{chr(0x274c)} {message}"))


async def send_info(channel: TextChannel, message: str):
    await channel.send(embed=Embed(color=botConfig.INFO_COLOR, description=f":information_source: {message}"))


async def send_exception(channel: TextChannel, exception: Exception):
    await channel.send(embed=Embed(
        color=botConfig.ERROR_COLOR,
        title=f"A wild {type(exception)} appeared!",
        description="Please scream at the bot owner to fix it."
    ))


def parse_id(input_str: str) -> int:
    """
    Parse the ID of a discord mention.

    :return: The ID contained in the str or 0 if it couldn't be parsed.
    """
    if input_str.isnumeric():
        return int(input_str)

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


_T = typing.TypeVar('_T')


async def add_guild_member_tables(
        # TODO seperate display function
        base_embed: Embed,
        guild: GuildStats,
        data_function: typing.Callable[
            [str, GuildStats._MemberList._Member], typing.Coroutine[typing.Any, typing.Any, _T]],
        display_function: typing.Callable[
            [_T], typing.Coroutine[typing.Any, typing.Any, typing.Any]] = str,
        sort_function: typing.Callable[[_T], typing.Any] = None,
        sort_reverse: bool = False):
    uuids = [uuid.replace('-', '') for uuid in guild.members.all.keys()]
    names = {p.uuid: p.name for p in await wrappers.minecraftPlayer.get_players(uuids=uuids)}

    async with asyncio.TaskGroup() as tg:
        data = {
            "OWNER": [(uuid.replace('-', ''), tg.create_task(data_function(uuid, m)))
                      for uuid, m in guild.members.owner.items()],
            "CHIEF": [(uuid.replace('-', ''), tg.create_task(data_function(uuid, m)))
                      for uuid, m in guild.members.chief.items()],
            "STRATEGIST": [(uuid.replace('-', ''), tg.create_task(data_function(uuid, m)))
                           for uuid, m in guild.members.strategist.items()],
            "CAPTAIN": [(uuid.replace('-', ''), tg.create_task(data_function(uuid, m)))
                        for uuid, m in guild.members.captain.items()],
            "RECRUITER": [(uuid.replace('-', ''), tg.create_task(data_function(uuid, m)))
                          for uuid, m in guild.members.recruiter.items()],
            "RECRUIT": [(uuid.replace('-', ''), tg.create_task(data_function(uuid, m)))
                        for uuid, m in guild.members.recruit.items()],
        }

    tb = TableBuilder.from_str('l  r')
    ranks = []
    for k, v in data.items():
        if len(v) == 0:
            continue
        ranks.append(k)
        tb.add_row('$', '$')

        if sort_function is not None:
            v = sorted(v, key=lambda t: sort_function(t[1].result()), reverse=sort_reverse)

        [tb.add_row(names.get(t[0], t[0]), display_function(t[1].result())) for t in v]

    tables = tb.build().split(f"${' ' * (tb.get_width() - 2)}$\n")[1:]
    for i, table in enumerate(tables):
        splits = split_str(table, 1000, '\n')
        first = True
        for split in splits:
            base_embed.add_field(name=ranks[i] if first else "", value=f">>> ```\n{split}```", inline=False)
            first = False


def create_chart(x, y, xlabel, ylabel):
    # Initialize IO
    data_stream = io.BytesIO()

    plt.plot(x, y)

    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True)

    # Save content into the data stream
    plt.savefig(data_stream, format='png', bbox_inches="tight", dpi=80)
    plt.close()

    ## Create file
    # Reset point back to beginning of stream
    data_stream.seek(0)
    chart = discord.File(data_stream, filename="chart.png")

    return chart
