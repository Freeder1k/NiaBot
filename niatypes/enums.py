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


class AnsiFormat(Enum):
    RESET = 0

    BOLD = 1
    UNDERLINE = 4

    FG_GRAY = 30
    FG_RED = 31
    FG_GREEN = 32
    FG_YELLOW = 33
    FG_BLUE = 34
    FG_PINK = 35
    FG_CYAN = 36
    FG_WHITE = 37

    BG_FIREFLY_DARK_BLUE = 40
    BG_ORANGE = 41
    BG_MARBLE_BLUE = 42
    BG_GREYISH_TURQUOISE = 43
    BG_GRAY = 44
    BG_INDIGO = 45
    BG_LIGHT_GRAY = 46
    BG_WHITE = 47