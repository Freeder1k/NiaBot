import asyncio
import traceback
from queue import Queue

import aiohttp.client_exceptions
from discord import Client, TextChannel, Embed
from discord.ext import tasks

import api.minecraft
import api.rateLimit
import api.wynncraft.guild
import api.wynncraft.network
import botConfig
import nerfuria.guild
import serverConfig
import storage.usernameData
import utils.logging
from dataTypes import MinecraftPlayer

_online_players: set[str] = set()
_unknown_players: Queue[str] = Queue()
_reservation_id: int = api.minecraft._usernames_rate_limit.reserve(20)
_server_list: dict[str, list[str]] = None


async def _get_and_store_from_api(*, uuid: str = None, username: str = None) -> MinecraftPlayer | None:
    p = await api.minecraft.get_player(uuid=uuid, username=username)
    if p is not None:
        await storage.usernameData.update(*p)
    return p


# TODO caching
async def get_player(*, uuid: str = None, username: str = None) -> MinecraftPlayer | None:
    p = await storage.usernameData.get_player(uuid=uuid, username=username)
    if p is not None:
        return p

    return await _get_and_store_from_api(uuid=uuid, username=username)


async def get_players(*, uuids: list[str] = None, usernames: list[str] = None) -> list[MinecraftPlayer]:
    """
    Get a list of players by uuids and names.

    :return: A list containing all players that were found.
    """
    if uuids is None:
        uuids = []
    if usernames is None or len(usernames) == 0:
        usernames = []

    uuids = [uuid.replace("-", "").lower() for uuid in uuids]

    stored = await storage.usernameData.get_players(uuids=uuids, usernames=usernames)
    known_uuids = {p.uuid for p in stored}
    known_names = {p.name for p in stored}

    unkown_uuids = set(uuids) - known_uuids
    unknown_names = set(usernames) - known_names

    if len(unkown_uuids) + len(unknown_names) > api.minecraft._mojang_rate_limit.get_remaining():
        raise api.rateLimit.RateLimitException("API usage would exceed ratelimit!")

    if len(unkown_uuids) > 0:
        stored += [p for p in (await asyncio.gather(*(_get_and_store_from_api(uuid=uuid) for uuid in unkown_uuids))) if
                   p is not None]
    if len(unknown_names) > 0:
        stored += [p for p in
                   (await asyncio.gather(*(_get_and_store_from_api(username=name) for name in unknown_names))) if
                   p is not None]

    return stored


def get_online_wynncraft_players() -> set[str]:
    return _online_players


async def get_server_list() -> dict[str, list[str]]:
    global _server_list
    if _server_list is None:
        _server_list = await api.wynncraft.network.server_list()

    return _server_list


async def _update_server_list():
    global _server_list
    _server_list = await api.wynncraft.network.server_list()


async def _update_online_members():
    global _online_players
    _online_players = set().union(*(_server_list.values()))


async def _update_unkown_players(joined_players: set[str]):
    known_names = {p.name for p in await storage.usernameData.get_players(usernames=list(joined_players))}
    [_unknown_players.put(name) for name in joined_players if name not in known_names]


async def _notify_guild_member_name_changes(client: Client, prev_names: list[MinecraftPlayer],
                                            updated_names: list[MinecraftPlayer]):
    channel = client.get_channel(serverConfig.get_log_channel_id(botConfig.GUILD_DISCORD))
    if not isinstance(channel, TextChannel):
        print(channel)
        utils.logging.elog("Log channel for guild server is not text channel!")
        return

    perms = channel.permissions_for(channel.guild.me)
    if not perms.send_messages and perms.embed_links:
        print(channel)
        utils.logging.elog("Missing perms for log channel for guild server!")
        return

    prev_names_dict = {p.uuid: p.name for p in prev_names if p is not None}

    guild_members = {m.uuid.replace("-", ""): m.name for m in nerfuria.guild.get_members()}
    updated_guild_members = []
    for player in updated_names:
        if player.uuid in guild_members:
            updated_guild_members.append(player)

    embeds = []
    for player in updated_guild_members:
        em = Embed(
            title=f"Name changed: **{prev_names_dict.get(player.uuid, '*unknown*')} -> {player.name}**",
            color=botConfig.DEFAULT_COLOR,
        )
        em.set_footer(text=f"UUID: {api.minecraft.format_uuid(player.uuid)}")
        embeds.append(em)

    if len(embeds) > 0:
        for i in range(0, len(embeds), 10):
            await channel.send(embeds=embeds[i:i + 10])


@tasks.loop(minutes=1, reconnect=True)
async def update_players(client: Client):
    try:
        await _update_server_list()

        prev_online_players = _online_players
        await _update_online_members()

        await _update_unkown_players(_online_players - prev_online_players)

        if _unknown_players.empty():
            return

        prev_names = []
        updated_names = []

        utils.logging.dlog(f"Updating {min(_unknown_players.qsize(), 200)} minecraft usernames.")

        for i in range(0, min((_unknown_players.qsize() + 9) // 10, 20)):
            unkown_players_batch = [_unknown_players.get() for _ in range(0, min(_unknown_players.qsize(), 10))]

            res = await api.minecraft.get_players_from_usernames(unkown_players_batch, reservation_id=_reservation_id)
            prev_names += await asyncio.gather(*(storage.usernameData.update(uuid, name) for uuid, name in res))

            for name in unkown_players_batch:
                if not any(name == t_name for _, t_name in res):
                    utils.logging.dlog(f"{name} not a minecraft name but online on wynncraft!")

            updated_names += res

        await _notify_guild_member_name_changes(client, prev_names, updated_names)

        api.minecraft._usernames_rate_limit.free(_reservation_id)

    except Exception as ex:
        traceback.print_exc()
        await asyncio.sleep(60)  # Wait here so the loop reconnect doesn't trigger a RateLimitException directly
        raise ex


update_players.add_exception_type(
    aiohttp.client_exceptions.ClientError,
    api.rateLimit.RateLimitException
)


async def update_nia():
    nia = await api.wynncraft.guild.stats("Nerfuria")
    known_uuids = {p.uuid for p in await storage.usernameData.get_players(uuids=[m.uuid for m in nia.members])}
    unknown_uuids = [m.uuid.replace("-", "").lower() for m in nia.members if
                     m.uuid.replace("-", "").lower() not in known_uuids]
    print(list(known_uuids))
    print(unknown_uuids)
    to_update = Queue()

    for i in range(0, len(unknown_uuids), 50):
        to_update.put(unknown_uuids[i:i + 50])
    print(to_update.qsize())
    while not to_update.empty():
        l = to_update.get()
        print(f"Updating {len(l)} Nia members")
        for uuid in l:
            await get_player(uuid=uuid)
        await asyncio.sleep(65)

    print("done updating")
