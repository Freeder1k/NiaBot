import dataclasses
import json
import os.path
from collections import defaultdict
from dataclasses import dataclass

import aiofiles


@dataclass
class _Options:
    cmd_prefix: str = "."  # TODO use botconfig?
    member_role_id: int = 0
    strat_role_id: int = 0
    chief_role_id: int = 0
    log_channel_id: int = 0


class ServerConfig:
    def __init__(self, path: str):
        self.path = path
        self._server_configs = defaultdict(_Options)

    async def load(self):
        if not os.path.isfile(self.path):
            return

        async with aiofiles.open(self.path, mode='r') as f:
            content = await f.read()

        data = json.loads(content)
        self._server_configs = {int(server_id): _Options(**v) for server_id, v in data.items()}

    async def save(self):
        if not os.path.isfile(self.path):
            os.makedirs(os.path.dirname(self.path), exist_ok=True)

        async with aiofiles.open(self.path, mode='w') as f:
            await f.write(json.dumps({k: dataclasses.asdict(v) for k, v in self._server_configs.items()}, indent=4))

    def get(self, server_id: int) -> _Options:
        return self._server_configs.get(server_id)

    def __getitem__(self, server_id: int) -> _Options:
        return self.get(server_id)
