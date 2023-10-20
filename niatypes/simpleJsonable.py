from niatypes.jsonable import Jsonable, JsonType


class SimpleJsonable(Jsonable):
    """
    A simple implementation of Jsonable.
    """
    @classmethod
    def from_json(cls, json_obj: JsonType):
        if json_obj is None:
            return None
        elif isinstance(json_obj, list):
            return cls(*json_obj)
        elif isinstance(json_obj, dict):
            return cls(**json_obj)
        else:
            return cls(json_obj)
