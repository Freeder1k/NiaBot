import dataclasses
from dataclasses import dataclass

from . import wynnAPI

@dataclass
class Stats:
    @dataclass
    class Member:
        name: str
        uuid: str
        rank: str
        contributed: str
        joined: str
        joinedFriendly: str

    @dataclass
    class Guild:
        name: str
        rank: str

    name: str
    prefix: str
    members: list[Member]
    xp: int
    level: int
    created: str
    createdFriendly: str
    territories: int
    banner: dict

    @staticmethod
    def _from_dict_inner(cls, d):
        try:
            fieldtypes = {f.name: f.type for f in dataclasses.fields(cls)}
            return cls(**{f: Stats._from_dict_inner(fieldtypes[f], d[f]) for f in d})
        except:
            return d  # Not a dataclass field

    @classmethod
    def from_dict(cls, d):
        return Stats._from_dict_inner(cls, d)


def guild_list():
    json = wynnAPI.get_legacy("guildList")
    return Stats.from_dict(json)


def stats(guild: str) -> Stats:
    json = wynnAPI.get_legacy("guildStats", guild)
    return Stats.from_dict(json)
