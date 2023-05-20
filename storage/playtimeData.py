from datetime import datetime
import json

class PlaytimeData:
    def __init__(self, start: datetime, playtimes: dict[str, list[int]]):
        self.start = start
        self.playtimes = playtimes

    def set_playtime(self, uuid: str, date: datetime, playtime: int):
        playtime_list = self.playtimes[uuid]
        day_diff = (date - self.start).days

        while len(playtime_list) < day_diff:
            playtime_list.append(0)

        playtime_list.append(playtime)

    def to_json(self, file):
        with open(file, 'w') as f:
            json.dump({"start": self.start.isoformat(), "playtimes": self.playtimes}, f, indent=4)

    @classmethod
    def from_json(cls, file):
        with open(file, "r") as f:
            data = json.load(f)
            return cls(datetime.fromisoformat(data["start"]), data["playtimes"])



