import dataclasses
import datetime
import re
from datetime import datetime, timezone
from typing import TypeVar, Any, Type

from common.types.enums import AnsiFormat


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
        fields[f] = _from_dict_inner(fieldtypes[f], d.get(f, None))
    return dataclass(**fields)


def _from_dict_inner(cls: Any, json: dict) -> Any:
    if json is None:
        return None
    elif type(json) == list:
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
        # error(f"Couldn't determine type of {json} in {cls} in dict conversion.")
        # TODO log error somehow?
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


_dashed_uuid_re = re.compile(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}')
_undashed_uuid_re = re.compile(r'[0-9a-fA-F]{32}')


def format_uuid(uuid: str, dashed: bool = True) -> str:
    """
    Convert a minecraft uuid to the specified format.

    :param uuid: The uuid to convert. Can be either in dashed or un-dashed format.
    :param dashed: If True, the uuid is formatted with dashes, otherwise without.

    :return: The formatted uuid.

    :raises ValueError: If the uuid is not in a valid format.
    """
    if _dashed_uuid_re.fullmatch(uuid):
        return uuid if dashed else uuid.replace("-", "")
    elif _undashed_uuid_re.fullmatch(uuid):
        return f"{uuid[0:8]}-{uuid[8:12]}-{uuid[12:16]}-{uuid[16:20]}-{uuid[20:32]}" if dashed else uuid
    else:
        raise ValueError(f"Invalid uuid format: {uuid}")


def ansi_format(*formatting: AnsiFormat):
    """
    Get the ANSI escape sequence for the specified formatting.
    """
    return f"\u001b[{';'.join((str(f.value) for f in formatting))}m"


def pluralize(num, s) -> str:
    """
    Pluralize a string if num is not 1.
    """
    if num == 1:
        return s
    return s + "s"


def create_inverted_index(strings, ignore_case=False, max_key_len=None, max_bucket_len=None) -> dict[str, list[str]]:
    """
    Create an inverted index for the specified strings.
    :param strings: The strings to index.
    :param ignore_case: If True, ignore case when indexing.
    :param max_key_len: The maximum length of the substring keys in the index.
    :param max_bucket_len: The maximum length of the list of strings for each key. Additional strings will be ignored.
     If None, all strings will be included.
    :return: A dictionary with substrings as keys and the strings containing them as values sorted by how early the
     substring appeared in the string.
    """
    index = {}
    max_str_len = max(len(string) for string in strings)

    if max_key_len is None:
        max_key_len = max_str_len

    for i in range(max_str_len):
        for string in strings:
            for j in range(i, i + max_key_len):
                if j >= len(string):
                    break

                sub_str = string[i:j]
                if ignore_case:
                    sub_str = sub_str.lower()

                if sub_str not in index:
                    index[sub_str] = [string]
                elif max_bucket_len is not None and len(index[sub_str]) >= max_bucket_len:
                    pass
                else:
                    index[sub_str].append(string)
    return index
