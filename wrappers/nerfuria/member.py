from dataclasses import dataclass
from enum import Enum


class WynnRank(Enum):
    OWNER = 5
    CHIEF = 4
    STRATEGIST = 3
    CAPTAIN = 2
    RECRUITER = 1
    RECRUIT = 0
    NONE = -1


class NiaGroup(Enum):
    ASPECT_OF_LIGHT = 6
    ASCENDED = 5
    ENLIGHTENED = 4
    PROVIDENCE = 3
    AWAKENED = 2
    LUMEN = 1
    OTHER = 0


class NiaRank(Enum):
    ORIGIN =          (WynnRank.OWNER, NiaGroup.ASPECT_OF_LIGHT)
    GENESIS =         (WynnRank.CHIEF, NiaGroup.ASPECT_OF_LIGHT)
    STARFORGER =      (WynnRank.CHIEF, NiaGroup.ASCENDED)
    STARGAZER =       (WynnRank.CHIEF, NiaGroup.ASCENDED)
    BLAZAR =          (WynnRank.CHIEF, NiaGroup.ENLIGHTENED)
    QUASAR =          (WynnRank.STRATEGIST, NiaGroup.ENLIGHTENED)
    ZENITH =          (WynnRank.STRATEGIST, NiaGroup.ENLIGHTENED)
    MYSTIC =          (WynnRank.STRATEGIST, NiaGroup.ENLIGHTENED)
    ECLIPSE =         (WynnRank.CAPTAIN, NiaGroup.PROVIDENCE)
    CELESTIAL =       (WynnRank.CAPTAIN, NiaGroup.PROVIDENCE)
    PENUMBRA =        (WynnRank.RECRUITER, NiaGroup.PROVIDENCE)
    NOVA =            (WynnRank.RECRUITER, NiaGroup.AWAKENED)
    STARCHILD =       (WynnRank.RECRUIT, NiaGroup.AWAKENED)
    WANDERER =        (WynnRank.RECRUIT, NiaGroup.AWAKENED)
    ASCENDED_LUMINA = (WynnRank.NONE, NiaGroup.LUMEN)
    LUMINA =          (WynnRank.NONE, NiaGroup.LUMEN)
    LUX =             (WynnRank.NONE, NiaGroup.LUMEN)
    LUX_NOVIAN =      (WynnRank.NONE, NiaGroup.LUMEN)


@dataclass
class Member:
    rank: NiaRank
    discord_id: int
    mc_uuid: str
    notes: list[str]
    