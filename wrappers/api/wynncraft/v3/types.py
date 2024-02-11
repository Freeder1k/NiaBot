from dataclasses import dataclass

from niatypes.dataTypes import Point2D
from niatypes.jsonableDataclass import JsonableDataclass


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
    class _MemberList(JsonableDataclass):
        total: int

        @dataclass(frozen=True)
        class _Member(JsonableDataclass):
            username: str
            online: bool
            server: str | None
            contributed: int
            contributionRank: int
            joined: str

        owner: dict[str, _Member]
        chief: dict[str, _Member]
        strategist: dict[str, _Member]
        captain: dict[str, _Member]
        recruiter: dict[str, _Member]
        recruit: dict[str, _Member]

        @property
        def all(self) -> dict[str, _Member]:
            return self.owner | self.chief | self.strategist | self.captain | self.recruiter | self.recruit

    members: _MemberList
    online: int
    banner: dict

    @dataclass(frozen=True)
    class _SeasonRank(JsonableDataclass):
        rating: int
        finalTerritories: int

    seasonRanks: dict[str, _SeasonRank]


@dataclass(frozen=True)
class Territory(JsonableDataclass):
    @dataclass(frozen=True)
    class _Guild(JsonableDataclass):
        uuid: str
        name: str
        prefix: str

    guild: _Guild
    acquired: str

    @dataclass(frozen=True)
    class _Location(JsonableDataclass):
        start: Point2D
        end: Point2D

    location: _Location


@dataclass(frozen=True)
class CharacterStats(JsonableDataclass):
    type: str
    nickname: str
    level: int
    xp: int
    xpPercent: int
    totalLevel: int
    wars: int
    playtime: int
    mobsKilled: int
    chestsFound: int
    blocksWalked: int
    itemsIdentified: int
    logins: int
    death: int
    discoveries: int

    @dataclass(frozen=True)
    class _Pvp(JsonableDataclass):
        kills: int
        deaths: int

    pvp: _Pvp
    gamemode: list[str]
    skillPoints: dict[str, int]

    @dataclass(frozen=True)
    class _Profession(JsonableDataclass):
        level: int
        xpPercent: int

    professions: dict[str, _Profession]

    @dataclass(frozen=True)
    class _Dungeons(JsonableDataclass):
        total: int
        list: dict[str, int]  # dungeon name: completions

    dungeons: _Dungeons

    @dataclass(frozen=True)
    class _Raids(JsonableDataclass):
        total: int
        list: dict[str, int]  # raid name: completions

    raids: _Raids
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
    class _LegacyRankColour(JsonableDataclass):
        def __init__(self, main=None, sub=None, color=None):
            if color is None:
                object.__setattr__(self, "main", main)
                object.__setattr__(self, "sub", sub)
            else:
                object.__setattr__(self, "main", color)
                object.__setattr__(self, "sub", color)

        main: str
        sub: str

    legacyRankColour: _LegacyRankColour
    shortenedRank: str
    supportRank: str
    firstJoin: str
    lastJoin: str
    playtime: int

    @dataclass(frozen=True)
    class _Guild(JsonableDataclass):
        uuid: str
        name: str
        prefix: str
        rank: str
        rankStars: str

    guild: _Guild

    @dataclass(frozen=True)
    class _GlobalData(JsonableDataclass):
        wars: int
        totalLevel: int
        killedMobs: int
        chestsFound: int

        @dataclass(frozen=True)
        class _Dungeons(JsonableDataclass):
            total: int
            list: dict[str, int]  # dungeon name: completions

        dungeons: _Dungeons

        @dataclass(frozen=True)
        class _Raids(JsonableDataclass):
            total: int
            list: dict[str, int]  # raid name: completions

        raids: _Raids
        completedQuests: int

        @dataclass(frozen=True)
        class _Pvp(JsonableDataclass):
            kills: int
            deaths: int

        pvp: _Pvp

    globalData: _GlobalData

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
    class _AbilityMapPiece(JsonableDataclass):
        type: str

        @dataclass(frozen=True)
        class _Coordinates(JsonableDataclass):
            x: int
            y: int

        coordinates: _Coordinates

        @dataclass(frozen=True)
        class _Meta(JsonableDataclass):
            icon: str  # Minecraft legacy item id e.g. 275:67
            page: int
            id: str  # Internal id of the ability, abilities in AT response are referred by the same id

        meta: _Meta
        family: list[str]

    map: list[_AbilityMapPiece]
