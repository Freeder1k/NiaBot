from dataclasses import dataclass
from typing import NamedTuple

from common.types.dataTypes import Point2D
from common.types.jsonableDataclass import JsonableDataclass


@dataclass(frozen=True)
class TrackedPlayerStats:
    record_time: str  # datetime in ISO8601 format
    uuid: str
    username: str
    rank: str
    support_rank: str
    first_join: str  # datetime in ISO8601 format
    last_join: str  # datetime in ISO8601 format
    playtime: float
    guild_name: str
    guild_rank: str
    wars: int
    total_levels: int
    killed_mobs: int
    chests_found: int
    dungeons_total: int
    dungeons_ds: int
    dungeons_ip: int
    dungeons_ls: int
    dungeons_uc: int
    dungeons_ss: int
    dungeons_ib: int
    dungeons_gg: int
    dungeons_ur: int
    dungeons_cds: int
    dungeons_cip: int
    dungeons_cls: int
    dungeons_css: int
    dungeons_cuc: int
    dungeons_cgg: int
    dungeons_cur: int
    dungeons_cib: int
    dungeons_ff: int
    dungeons_eo: int
    dungeons_ts: int
    raids_total: int
    raids_notg: int
    raids_nol: int
    raids_tcc: int
    raids_tna: int
    completed_quests: int
    pvp_kills: int
    pvp_deaths: int


@dataclass(frozen=True)
class GuildStats(JsonableDataclass):
    uuid: str
    name: str
    prefix: str
    level: int
    xpPercent: int
    territories: int
    wars: int
    created: str

    @dataclass(frozen=True)
    class MemberList(JsonableDataclass):
        total: int

        @dataclass(frozen=True)
        class GuildMember(JsonableDataclass):
            username: str
            online: bool
            server: str | None
            contributed: int
            contributionRank: int
            joined: str

        owner: dict[str, GuildMember]
        chief: dict[str, GuildMember]
        strategist: dict[str, GuildMember]
        captain: dict[str, GuildMember]
        recruiter: dict[str, GuildMember]
        recruit: dict[str, GuildMember]

        @property
        def all(self) -> dict[str, GuildMember]:
            return self.owner | self.chief | self.strategist | self.captain | self.recruiter | self.recruit

    members: MemberList
    online: int
    banner: dict

    @dataclass(frozen=True)
    class SeasonRank(JsonableDataclass):
        rating: int
        finalTerritories: int

    seasonRanks: dict[str, SeasonRank]


@dataclass(frozen=True)
class Territory(JsonableDataclass):
    @dataclass(frozen=True)
    class Guild(JsonableDataclass):
        uuid: str
        name: str
        prefix: str

    guild: Guild
    acquired: str

    @dataclass(frozen=True)
    class Location(JsonableDataclass):
        start: Point2D
        end: Point2D

    location: Location


@dataclass(frozen=True)
class CharacterStats(JsonableDataclass):
    type: str
    nickname: str
    level: int
    xp: int
    xpPercent: int
    totalLevel: int
    wars: int
    playtime: float
    mobsKilled: int
    chestsFound: int
    blocksWalked: int
    itemsIdentified: int
    logins: int
    deaths: int
    discoveries: int

    @dataclass(frozen=True)
    class Pvp(JsonableDataclass):
        kills: int
        deaths: int

    pvp: Pvp
    gamemode: list[str]
    skillPoints: dict[str, int]

    @dataclass(frozen=True)
    class Profession(JsonableDataclass):
        level: int
        xpPercent: int

    professions: dict[str, Profession]

    @dataclass(frozen=True)
    class Dungeons(JsonableDataclass):
        total: int
        list: dict[str, int]  # dungeon name: completions

    dungeons: Dungeons

    @dataclass(frozen=True)
    class Raids(JsonableDataclass):
        total: int
        list: dict[str, int]  # raid name: completions

    raids: Raids
    quests: list[str]


@dataclass(frozen=True)
class PlayerStats(JsonableDataclass):
    username: str
    online: bool
    server: str
    uuid: str
    rank: str
    rankBadge: str  # URL to the badge SVG in the Wynncraft CDN (only path)

    @dataclass(frozen=True)
    class LegacyRankColour(JsonableDataclass):
        def __init__(self, main=None, sub=None, color=None):
            if color is None:
                object.__setattr__(self, "main", main)
                object.__setattr__(self, "sub", sub)
            else:
                object.__setattr__(self, "main", color)
                object.__setattr__(self, "sub", color)

        main: str
        sub: str

    legacyRankColour: LegacyRankColour
    shortenedRank: str
    supportRank: str
    firstJoin: str
    lastJoin: str
    playtime: float

    @dataclass(frozen=True)
    class Guild(JsonableDataclass):
        uuid: str
        name: str
        prefix: str
        rank: str
        rankStars: str

    guild: Guild

    @dataclass(frozen=True)
    class GlobalData(JsonableDataclass):
        wars: int
        totalLevel: int
        killedMobs: int
        chestsFound: int

        @dataclass(frozen=True)
        class Dungeons(JsonableDataclass):
            total: int
            list: dict[str, int]  # dungeon name: completions

        dungeons: Dungeons

        @dataclass(frozen=True)
        class Raids(JsonableDataclass):
            total: int
            list: dict[str, int]  # raid name: completions

        raids: Raids
        completedQuests: int

        @dataclass(frozen=True)
        class Pvp(JsonableDataclass):
            kills: int
            deaths: int

        pvp: Pvp

    globalData: GlobalData

    forumLink: int
    ranking: dict[str, int]  # ranking type: rank
    publicProfile: bool
    characters: dict[str, CharacterStats]


@dataclass(frozen=True)
class CharacterShort(JsonableDataclass):
    type: str
    nickname: str
    level: int
    xp: int
    xpPercent: int
    totalLevel: int
    gamemode: list[str]


@dataclass(frozen=True)
class AbilityMap(JsonableDataclass):
    pages: int

    @dataclass(frozen=True)
    class AbilityMapPiece(JsonableDataclass):
        type: str

        @dataclass(frozen=True)
        class Coordinates(JsonableDataclass):
            x: int
            y: int

        coordinates: Coordinates

        @dataclass(frozen=True)
        class Meta(JsonableDataclass):
            icon: str  # Minecraft legacy item id e.g. 275:67
            page: int
            id: str  # Internal id of the ability, abilities in AT response are referred by the same id

        meta: Meta
        family: list[str]

    map: list[AbilityMapPiece]


@dataclass(frozen=True)
class AbilityNode(JsonableDataclass):
    type: str

    @dataclass(frozen=True)
    class Coordinates(JsonableDataclass):
        x: int
        y: int

    coordinates: Coordinates

    @dataclass(frozen=True)
    class Meta(JsonableDataclass):
        @dataclass(frozen=True)
        class Icon(JsonableDataclass):
            @dataclass(frozen=True)
            class IconValue(JsonableDataclass):
                id: str
                name: str
                customModelData: str

            value: IconValue
            format: str

        icon: Icon
        page: int
        id: str  # Internal id of the ability, abilities in AT response are referred by the same id

    meta: Meta
    family: list[str]


class WynncraftGuild(NamedTuple):
    name: str
    tag: str
    uuid: str = None  # TODO make non-optional
