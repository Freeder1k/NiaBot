from dataclasses import dataclass
from typing import NamedTuple

from common.types.enums import NiaRank
from common.types.simpleJsonable import SimpleJsonable


class MinecraftPlayer(NamedTuple):
    uuid: str
    name: str


@dataclass(frozen=True)
class Point2D(SimpleJsonable):
    x: int
    z: int


@dataclass
class NiaMember:
    rank: NiaRank
    discord_id: int
    mc_uuid: str
    notes: list[str]
