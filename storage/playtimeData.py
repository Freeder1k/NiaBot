import json
import os.path
from datetime import datetime
from typing import Final

_start: datetime = datetime.today()
_playtimes: dict[str, list[int]] = {}
PLAYTIME_FILE: Final = "playtimes.json"


def get_playtimes(uuid: str):
    return tuple(_playtimes[uuid])


def set_playtime(uuid: str, date: datetime, playtime: int):
    day_diff = (date - _start).days

    if uuid in _playtimes:
        playtime_list = _playtimes[uuid]
        playtime_list +=  ([playtime_list[-1]] * (day_diff - len(playtime_list)))
    else:
        playtime_list = [0] * day_diff

    if len(playtime_list) <= day_diff:
        playtime_list.append(playtime)

    _playtimes[uuid] = playtime_list


def store_data():
    with open(PLAYTIME_FILE, 'w') as f:
        json.dump({"start": _start.isoformat(), "playtimes": _playtimes}, f, indent=4)


def load_data() -> bool:
    """
    :return: True, if successfully loaded data.
    """
    if os.path.exists(PLAYTIME_FILE):
        with open(PLAYTIME_FILE, "r") as f:
            data = json.load(f)
            global _start, _playtimes
            _start = datetime.fromisoformat(data["start"])
            _playtimes = data["playtimes"]
            return True
    return False
