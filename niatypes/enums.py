from enum import Enum


class WynnGuildRank(Enum):
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
    ORIGIN =          (WynnGuildRank.OWNER, NiaGroup.ASPECT_OF_LIGHT)
    GENESIS =         (WynnGuildRank.CHIEF, NiaGroup.ASPECT_OF_LIGHT)
    STARFORGER =      (WynnGuildRank.CHIEF, NiaGroup.ASCENDED)
    STARGAZER =       (WynnGuildRank.CHIEF, NiaGroup.ASCENDED)
    BLAZAR =          (WynnGuildRank.CHIEF, NiaGroup.ENLIGHTENED)
    QUASAR =          (WynnGuildRank.STRATEGIST, NiaGroup.ENLIGHTENED)
    ZENITH =          (WynnGuildRank.STRATEGIST, NiaGroup.ENLIGHTENED)
    MYSTIC =          (WynnGuildRank.STRATEGIST, NiaGroup.ENLIGHTENED)
    ECLIPSE =         (WynnGuildRank.CAPTAIN, NiaGroup.PROVIDENCE)
    CELESTIAL =       (WynnGuildRank.CAPTAIN, NiaGroup.PROVIDENCE)
    PENUMBRA =        (WynnGuildRank.RECRUITER, NiaGroup.PROVIDENCE)
    NOVA =            (WynnGuildRank.RECRUITER, NiaGroup.AWAKENED)
    STARCHILD =       (WynnGuildRank.RECRUIT, NiaGroup.AWAKENED)
    WANDERER =        (WynnGuildRank.RECRUIT, NiaGroup.AWAKENED)
    ASCENDED_LUMINA = (WynnGuildRank.NONE, NiaGroup.LUMEN)
    LUMINA =          (WynnGuildRank.NONE, NiaGroup.LUMEN)
    LUX =             (WynnGuildRank.NONE, NiaGroup.LUMEN)
    LUX_NOVIAN =      (WynnGuildRank.NONE, NiaGroup.LUMEN)
