import dataclasses
import json
import os.path
from dataclasses import dataclass


@dataclass
class _Config:
    cmd_prefix: str = "."  # TODO use botconfig?
    member_role_id: int = 0
    strat_role_id: int = 0
    chief_role_id: int = 0
    log_channel_id: int = 0


class ServerConfigs:
    def __init__(self, path: str):
        """
        Class that holds the server configurations for each server a bot instance is in.
        :param path: The path to the json file where the configurations are stored.
        """
        self.path = path
        self._server_configs = {}
        self.loaded = False

    def load(self):
        """
        Loads the server configurations from the json file.
        """
        if not os.path.isfile(self.path):
            return

        with open(self.path, mode='r') as f:
            content = f.read()

        data = json.loads(content)
        self._server_configs = {int(server_id): _Config(**v) for server_id, v in data.items()}
        self.loaded = True

    async def save(self):
        """
        Saves the server configurations to the json file.
        """
        if not os.path.isfile(self.path):
            os.makedirs(os.path.dirname(self.path), exist_ok=True)

        with open(self.path, mode='w') as f:
            f.write(json.dumps({k: dataclasses.asdict(v) for k, v in self._server_configs.items()}, indent=4))

    def get(self, server_id: int) -> _Config:
        """
        Gets the configuration for a server.
        """
        if not self.loaded:
            self.load()

        if server_id not in self._server_configs:
            self._server_configs[server_id] = _Config()
            self.save()

        return self._server_configs.get(server_id)

    def __getitem__(self, server_id: int) -> _Config:
        return self.get(server_id)
