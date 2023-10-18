from dataclasses import dataclass

from niatypes.jsonable import Jsonable


@dataclass(frozen=True)
class CharacterStats(Jsonable):
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
    class Pvp(Jsonable):
        kills: int
        deaths: int

    pvp: Pvp
    gamemode: list[str]
    skillPoints: dict[str, int]

    @dataclass(frozen=True)
    class Profession(Jsonable):
        level: int
        xpPercent: int

    professions: dict[str, Profession]

    @dataclass(frozen=True)
    class Dungeons(Jsonable):
        total: int
        list: dict[str, int]  # dungeon name: completions

    dungeons: Dungeons

    @dataclass(frozen=True)
    class Raids(Jsonable):
        total: int
        list: dict[str, int]  # raid name: completions

    raids: Raids
    quests: list[str]


@dataclass(frozen=True)
class Stats(Jsonable):
    username: str
    online: bool
    server: str
    uuid: str
    rank: str
    rankBadge: str  # URL to the badge SVG in the Wynncraft CDN (only path)

    @dataclass(frozen=True)
    class LegacyRankColour(Jsonable):
        main: str
        sub: str

    legacyRankColour: LegacyRankColour
    shortenedRank: str
    supportRank: str
    firstJoin: str
    lastJoin: str
    playtime: int

    @dataclass(frozen=True)
    class Guild(Jsonable):
        name: str
        prefix: str
        rank: str
        rankStars: str

    guild: Guild

    @dataclass(frozen=True)
    class GlobalData(Jsonable):
        wars: int
        totalLevels: int
        killedMobs: int
        chestsFound: int

        @dataclass(frozen=True)
        class Dungeons(Jsonable):
            total: int
            list: dict[str, int]  # dungeon name: completions

        dungeons: Dungeons

        @dataclass(frozen=True)
        class Raids(Jsonable):
            total: int
            list: dict[str, int]  # raid name: completions

        raids: Raids
        completedQuests: int

        @dataclass(frozen=True)
        class Pvp(Jsonable):
            kills: int
            deaths: int

        pvp: Pvp

    globalData: GlobalData

    @dataclass(frozen=True)
    class ForumLink(Jsonable):
        forumUsername: str
        forumId: int
        gameUsername: str

    forumLink: ForumLink
    ranking: dict[str, int]  # ranking type: rank
    publicProfile: bool
    characters: dict[str, CharacterStats]


@dataclass(frozen=True)
class CharacterShort(Jsonable):
    type: str
    nickname: str
    level: int
    xp: int
    xpPercent: int
    totalLevel: int
    gamemode: list[str]


@dataclass(frozen=True)
class AbilityMap(Jsonable):
    pages: int

    @dataclass(frozen=True)
    class AbilityMapPiece(Jsonable):
        type: str

        @dataclass(frozen=True)
        class Coordinates(Jsonable):
            x: int
            y: int

        coordinates: Coordinates

        @dataclass(frozen=True)
        class Meta(Jsonable):
            icon: str  # Minecraft legacy item id e.g. 275:67
            page: int
            id: str  # Internal id of the ability, abilities in AT response are refered by the same id

        meta: Meta
        family: list[str]

    map: list[AbilityMapPiece]
