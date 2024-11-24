import asyncio
from abc import ABC, abstractmethod

import aiohttp.client_exceptions
from discord.ext import tasks

import common.api.minecraft
import common.api.rateLimit
import common.api.wynncraft.v3.guild
import common.api.wynncraft.v3.player
import common.api.wynncraft.v3.session
import common.logging
import common.storage.playerTrackerData
import common.storage.usernameData
from common.types.dataTypes import MinecraftPlayer
from common.types.enums import PlayerIdentifier
from workers.queueWorker import QueueWorker

_online_players: set[str] = set()
_updated_players: list[tuple[MinecraftPlayer, MinecraftPlayer]] = []
_worker = QueueWorker(delay=0.5)


class NameChangeSubscriber(ABC):
    @abstractmethod
    async def name_changed(self, uuid: str, prev_name: str, new_name: str):
        pass


_subscribers: list[NameChangeSubscriber] = []


def subscribe(subscriber: NameChangeSubscriber):
    """
    Subscribe to name change updates.
    """
    _subscribers.append(subscriber)


async def _fetch_and_update_username(username: str, tries: int = 1):
    if common.api.minecraft.calculate_remaining_calls() < 1:
        await common.api.minecraft.wait_on_rate_limit()

    try:
        player = await common.api.minecraft.get_player(username=username)
    except common.api.rateLimit.RateLimitException as e:
        common.logging.error("Rate limit reached for mojang api!", e)
        await common.api.minecraft.wait_on_rate_limit()
        _worker.put(_fetch_and_update_username, username)
        return
    except aiohttp.client_exceptions.ClientError as e:
        common.logging.error(f"Failed to update username ({tries}/3): ", username)
        if tries <= 3:
            await asyncio.sleep(60)
            _worker.put(_fetch_and_update_username, username, tries + 1)
        raise e

    if player is None:
        common.logging.debug(f"{username} is not a minecraft name but online on wynncraft ({tries}/3)!")
        if tries <= 3:
            await asyncio.sleep(60)
            _worker.put(_fetch_and_update_username, username, tries + 1)
        return

    prev_p = await common.storage.usernameData.update(player.uuid, player.name)

    if prev_p is not None and prev_p.name != player.name:
        for subscriber in _subscribers:
            await subscriber.name_changed(player.uuid, prev_p.name, player.name)


@tasks.loop(seconds=61, reconnect=True)
async def _update_usernames():
    try:
        global _online_players
        prev_online_players = _online_players
        _online_players = set((await common.api.wynncraft.v3.player.player_list(PlayerIdentifier.USERNAME)).keys())

        joined_players = _online_players - prev_online_players

        known_names = {p.name for p in await common.storage.usernameData.get_players(usernames=list(joined_players))}
        unknown_names = [name for name in joined_players if name not in known_names]

        for username in unknown_names:
            _worker.put(_fetch_and_update_username, username)

        if len(unknown_names) >= 0:
            common.logging.debug(f"Updating {len(unknown_names)}({_worker.qsize()}) minecraft usernames.")

    except common.api.rateLimit.RateLimitException:
        pass
    except Exception as ex:
        await common.logging.error(exc_info=ex)
        raise ex


_update_usernames.add_exception_type(aiohttp.client_exceptions.ClientError, Exception)


def start():
    _update_usernames.start()
    _worker.start()
    common.logging.info("Username updater workers started.")


def stop():
    _worker.stop()
    _update_usernames.stop()
