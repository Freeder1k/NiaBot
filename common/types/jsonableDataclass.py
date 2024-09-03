import dataclasses

from common.types.jsonable import Jsonable, JsonType


@dataclasses.dataclass(frozen=True)
class JsonableDataclass(Jsonable):
    @classmethod
    def from_json(cls, json_obj: dict[str, JsonType]):
        fieldtypes = {f.name: f.type for f in dataclasses.fields(cls)}

        fields = {}
        for f in fieldtypes:
            fields[f] = Jsonable.json_to_cls(fieldtypes[f], json_obj.get(f, None))

        # unknown = set(json_obj.keys()) - set(fieldtypes.keys())
        # missing = set(fieldtypes.keys()) - set(json_obj.keys())
        #
        # if unknown:
        #     logging.debug(f"Unknown fields: {unknown}")
        # if missing:
        #     logging.debug(f"Missing fields: {missing}")

        return cls(**fields)
