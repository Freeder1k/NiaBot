from enum import Enum, IntEnum, StrEnum


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
    ORIGIN = (WynnGuildRank.OWNER, NiaGroup.ASPECT_OF_LIGHT)
    GENESIS = (WynnGuildRank.CHIEF, NiaGroup.ASPECT_OF_LIGHT)
    STARFORGER = (WynnGuildRank.CHIEF, NiaGroup.ASCENDED)
    STARGAZER = (WynnGuildRank.CHIEF, NiaGroup.ASCENDED)
    BLAZAR = (WynnGuildRank.CHIEF, NiaGroup.ENLIGHTENED)
    QUASAR = (WynnGuildRank.STRATEGIST, NiaGroup.ENLIGHTENED)
    ZENITH = (WynnGuildRank.STRATEGIST, NiaGroup.ENLIGHTENED)
    MYSTIC = (WynnGuildRank.STRATEGIST, NiaGroup.ENLIGHTENED)
    ECLIPSE = (WynnGuildRank.CAPTAIN, NiaGroup.PROVIDENCE)
    CELESTIAL = (WynnGuildRank.CAPTAIN, NiaGroup.PROVIDENCE)
    PENUMBRA = (WynnGuildRank.RECRUITER, NiaGroup.PROVIDENCE)
    NOVA = (WynnGuildRank.RECRUITER, NiaGroup.AWAKENED)
    STARCHILD = (WynnGuildRank.RECRUIT, NiaGroup.AWAKENED)
    WANDERER = (WynnGuildRank.RECRUIT, NiaGroup.AWAKENED)
    ASCENDED_LUMINA = (WynnGuildRank.NONE, NiaGroup.LUMEN)
    LUMINA = (WynnGuildRank.NONE, NiaGroup.LUMEN)
    LUX = (WynnGuildRank.NONE, NiaGroup.LUMEN)
    LUX_NOVIAN = (WynnGuildRank.NONE, NiaGroup.LUMEN)


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


class LogEntryType(IntEnum):
    MEMBER_JOIN = 1
    MEMBER_LEAVE = 2
    MEMBER_NAME_CHANGE = 3


class PlayerIdentifier(StrEnum):
    UUID = "uuid"
    USERNAME = "username"


class PlayerStatsIdentifier(StrEnum):
    UUID = "uuid",
    USERNAME = "username",
    RANK = "rank",
    SUPPORT_RANK = "support_rank",
    FIRST_JOIN = "first_join",
    LAST_JOIN = "last_join",
    LAST_LEAVE = "record_time"
    PLAYTIME = "playtime",
    GUILD_UUID = "guild_uuid",
    GUILD_NAME = "guild_name",
    GUILD_RANK = "guild_rank",
    WARS = "wars",
    TOTAL_LEVELS = "total_levels",
    KILLED_MOBS = "killed_mobs",
    CHESTS_FOUND = "chests_found",
    DUNGEONS_TOTAL = "dungeons_total",
    DUNGEONS_DS = "dungeons_ds",
    DUNGEONS_IP = "dungeons_ip",
    DUNGEONS_LS = "dungeons_ls",
    DUNGEONS_UC = "dungeons_uc",
    DUNGEONS_SS = "dungeons_ss",
    DUNGEONS_IB = "dungeons_ib",
    DUNGEONS_GG = "dungeons_gg",
    DUNGEONS_UR = "dungeons_ur",
    DUNGEONS_CDS = "dungeons_cds",
    DUNGEONS_CIP = "dungeons_cip",
    DUNGEONS_CLS = "dungeons_cls",
    DUNGEONS_CSS = "dungeons_css",
    DUNGEONS_CUC = "dungeons_cuc",
    DUNGEONS_CGG = "dungeons_cgg",
    DUNGEONS_CUR = "dungeons_cur",
    DUNGEONS_CIB = "dungeons_cib",
    DUNGEONS_FF = "dungeons_ff",
    DUNGEONS_EO = "dungeons_eo",
    DUNGEONS_TS = "dungeons_ts",
    RAIDS_TOTAL = "raids_total",
    RAIDS_NOTG = "raids_notg",
    RAIDS_NOL = "raids_nol",
    RAIDS_TCC = "raids_tcc",
    RAIDS_TNA = "raids_tna",
    COMPLETED_QUESTS = "completed_quests",
    PVP_KILLS = "pvp_kills",
    PVP_DEATHS = "pvp_deaths"
