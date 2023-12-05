from dataclasses import dataclass

from niatypes.dataTypes import Point2D
from niatypes.jsonableDataclass import JsonableDataclass


@dataclass(frozen=True)
class GuildStats(JsonableDataclass):
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
        def all(self):
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
        name: str
        prefix: str

    guild: _Guild
    acquired: str

    @dataclass(frozen=True)
    class _Location(JsonableDataclass):
        start: Point2D
        end: Point2D

    location: _Location
