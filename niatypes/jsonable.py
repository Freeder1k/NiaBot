import dataclasses
import types
from typing import Union

from handlers.logging import log_error

JsonBaseType = Union[int, float, str, bool, None]

JsonType = Union[dict[str, 'JsonType'], list['JsonType'], JsonBaseType]


@dataclasses.dataclass(frozen=True)
class Jsonable:
    @classmethod
    def from_json(cls, json_obj: dict[str, JsonType]):
        """
        Convert a json dictionary to an object of this class.
o
        :param json_obj: the (nested) json dictionary corresponding to the cls
        :return: an instance of cls
        """
        if not dataclasses.is_dataclass(cls):
            raise TypeError(f"{cls} is not a dataclass!")

        fieldtypes = {f.name: f.type for f in dataclasses.fields(cls)}

        fields = {}
        for f in fieldtypes:
            fields[f] = Jsonable._from_json_inner(fieldtypes[f], json_obj.get(f, None))

        return cls(**fields)

    @staticmethod
    def _from_json_inner(cls, json_obj: JsonType):
        if isinstance(json_obj, JsonBaseType):
            return json_obj

        elif isinstance(json_obj, dict):
            if cls is dict:
                return json_obj
            if isinstance(cls, types.GenericAlias) and cls.__origin__ is dict:
                return {k: Jsonable._from_json_inner(cls.__args__[1], v) for k, v in json_obj.items()}
            elif issubclass(cls, Jsonable):
                return cls.from_json(json_obj)

        elif isinstance(json_obj, list):
            if cls is list:
                return json_obj
            if isinstance(cls, types.GenericAlias) and cls.__origin__ is list:
                return [Jsonable._from_json_inner(cls.__args__[0], j) for j in json_obj]

        log_error(f"Couldn't determine type of {json_obj} in {cls} in dict conversion.")
        return json_obj
