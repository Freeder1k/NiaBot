from abc import ABC, abstractmethod

import common.api.minecraft
import common.api.rateLimit
import common.api.wynncraft.v3.guild
import common.api.wynncraft.v3.player
import common.api.wynncraft.v3.session
import common.logging
import common.storage.playerTrackerData
import common.storage.usernameData
from common.types.dataTypes import MinecraftPlayer
from workers.queueWorker import QueueWorker

_online_players: set[str] = set()
_worker = QueueWorker(delay=0.5)
_queued_names: set[str] = set()


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


async def update_username(player: MinecraftPlayer):
    prev_p = await common.storage.usernameData.update(player.uuid, player.name)

    if prev_p is not None and prev_p.name != player.name:
        for subscriber in _subscribers:
            await subscriber.name_changed(player.uuid, prev_p.name, player.name)
