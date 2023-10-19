import dataclasses

from niatypes.jsonable import Jsonable, JsonType


@dataclasses.dataclass(frozen=True)
class JsonableDataclass(Jsonable):
    @classmethod
    def from_json(cls, json_obj: dict[str, JsonType]):
        fieldtypes = {f.name: f.type for f in dataclasses.fields(cls)}

        fields = {}
        for f in fieldtypes:
            fields[f] = Jsonable.json_to_cls(fieldtypes[f], json_obj.get(f, None))

        return cls(**fields)
