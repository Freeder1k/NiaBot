import dataclasses
import datetime
from datetime import datetime, timezone
from typing import TypeVar, Any, Type

from utils.logging import elog


def parse_name(nickname: str):
    """
    Get the minecraft name out of a nickname.

    :param nickname:  This should be in the form "RANK NAME".
    :return: The name if found otherwise ""
    """
    return nickname.split(" ")[-1]


T = TypeVar("T")


def dataclass_from_dict(dataclass: Type[T], d: dict) -> T:
    """
    Convert a dictionary to the specified dataclass.

    :param dataclass: the dataclass to convert to
    :param d: the (nested) dictionary corresponding to the cls
    :return: an instance of cls
    """
    if not dataclasses.is_dataclass(dataclass):
        raise TypeError(f"{dataclass} is not a dataclass!")

    fieldtypes = {f.name: f.type for f in dataclasses.fields(dataclass)}
    fields = {}
    for f in fieldtypes:
        fields[f] = _from_dict_inner(fieldtypes[f], d[f])
    return dataclass(**fields)


def _from_dict_inner(cls: Any, json: dict) -> Any:
    if type(json) == list:
        return [_from_dict_inner(cls.__args__[0], j) for j in json]
    elif isinstance(cls, type):
        if dataclasses.is_dataclass(cls):
            return dataclass_from_dict(cls, json)
        elif cls == Any:
            return json
        elif isinstance(json, cls):
            return json
    elif type(json) == dict:
        return {k: _from_dict_inner(cls.__args__[0], v) for k, v in json.items()}
    else:
        elog(f"Couldn't determine type of {json} in {cls} in dict conversion.")
        return json


def split_str(s: str, length: int, splitter: chr) -> list[str]:
    """
    Split a string into parts of length `length` at the specified splitter character.
    """
    res = []
    i = 0
    while True:
        start = i
        i += length

        # At end of string
        if i >= len(s):
            res.append(s[start:i])
            return res

        # Back up until splitter
        while s[i - 1] != splitter:
            i -= 1
        res.append(s[start:i])


def get_relative_date_str(dt: datetime, years=False, months=False, weeks=False, days=False, hours=False, minutes=False,
                          seconds=False) -> str:
    """
    Get a string of the date relative to today in the form "x time".
     The boolean parameters indicate if that specific time form should be enabled.
    """
    delta = (datetime.now(timezone.utc) - dt)

    if years and delta.days >= 2 * 365:
        return f"{delta.days // 365} years"
    elif years and delta.days >= 365:
        return "1 year"
    elif months and delta.days >= 2 * 30:
        return f"{delta.days // 30} months"
    elif months and delta.days >= 30:
        return "1 month"
    elif weeks and delta.days >= 2 * 7:
        return f"{delta.days // 7} weeks"
    elif weeks and delta.days >= 7:
        return "1 week"
    elif days and delta.days >= 2:
        return f"{delta.days} days"
    elif days and delta.days >= 1:
        return "1 day"

    elif hours and delta.seconds >= 2 * 60 * 60:
        return f"{delta.seconds // (60 * 60)} hours"
    elif hours and delta.seconds >= 60 * 60:
        return "1 hour"
    elif minutes and delta.seconds >= 2 * 60:
        return f"{delta.seconds // 60} minutes"
    elif minutes and delta.seconds >= 60:
        return "1 minute"
    elif seconds and delta.seconds >= 2:
        return f"{delta.seconds} seconds"
    elif seconds and delta.seconds >= 1:
        return "1 second"
    else:
        return "0 " + (
            "seconds" if seconds
            else "minutes" if minutes
            else "hours" if hours
            else "days" if days
            else "weeks" if weeks
            else "months" if months
            else "years" if years
            else ""
        )


def get_dashed_uuid(uuid: str) -> str:
    if len(uuid) != 32:
        raise ValueError("uuid parameter must be a string of length 32")

    return f"{uuid[0:8]}-{uuid[8:12]}-{uuid[12:16]}-{uuid[16:20]}-{uuid[20:32]}"
