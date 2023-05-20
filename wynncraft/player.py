import dataclasses
from dataclasses import dataclass

import wynncraft.wynnAPI

@dataclass
class Stats:
    @dataclass
    class Meta:
        @dataclass
        class Location:
            online: bool
            server: str

        @dataclass
        class Tag:
            display: bool
            value: str

        firstJoin: str
        lastJoin: str
        location: Location
        playtime: int
        tag: Tag
        veteran: bool

    @dataclass
    class Guild:
        name: str
        rank: str

    username: str
    uuid: str
    rank: str
    meta: Meta
    characters: list[dict]
    guild: Guild
    global_stats: dict
    ranking: dict

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

def stats(player: str):
    json = wynncraft.wynnAPI.get_v2(f"/player/{player}/stats")
    json["global_stats"] = json.pop("global")
    return Stats.from_dict(json['data'][0])

