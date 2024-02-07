from dataclasses import dataclass
from typing import NamedTuple

from niatypes.enums import NiaRank
from niatypes.simpleJsonable import SimpleJsonable


class MinecraftPlayer(NamedTuple):
    uuid: str
    name: str


class WynncraftGuild(NamedTuple):
    name: str
    tag: str


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
