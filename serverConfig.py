import dataclasses
import json
import os.path
from dataclasses import dataclass

import aiofiles

import botConfig
import utils.misc


@dataclass
class _ServerConfig:
    cmd_prefix: str = botConfig.PREFIX
    member_role_id: int = 0
    strat_role_id: int = 0
    log_channel_id: int = 0


_server_configs: dict[int, _ServerConfig] = {}
_default_conf = _ServerConfig()
_configs_file = "server_conf.json"


async def load_server_configs():
    if os.path.isfile(_configs_file):
        async with aiofiles.open(_configs_file, mode='r') as f:
            content = await f.read()
            data = json.loads(content)
            global _server_configs
            _server_configs = {int(server_id): utils.misc.dataclass_from_dict(_ServerConfig, v) for server_id, v in
                               data.items()}


async def _store_server_configs():
    async with aiofiles.open(_configs_file, mode='w') as f:
        await f.write(json.dumps({k: dataclasses.asdict(v) for k, v in _server_configs.items()}, indent=4))


async def _set(server_id: int, attr: str, value):
    if server_id not in _server_configs:
        _server_configs[server_id] = _ServerConfig()

    setattr(_server_configs[server_id], attr, value)
    await _store_server_configs()



def get_cmd_prefix(server_id: int) -> str:
    return _server_configs.get(server_id, _default_conf).cmd_prefix


async def set_cmd_prefix(server_id: int, prefix: str):
    await _set(server_id, "cmd_prefix", prefix)


def get_member_role_id(server_id: int) -> int:
    """
    Get the member role ID of the specified server
    :returns: 0 if no member role is set, otherwise the ID.
    """
    return _server_configs.get(server_id, _default_conf).member_role_id


async def set_member_role_id(server_id: int, role_id: int):
    await _set(server_id, "member_role_id", role_id)


def get_strat_role_id(server_id: int) -> int:
    """
    Get the strat role ID of the specified server
    :returns: 0 if no strat role is set, otherwise the ID.
    """
    return _server_configs.get(server_id, _default_conf).strat_role_id


async def set_strat_role_id(server_id: int, role_id: int):
    await _set(server_id, "strat_role_id", role_id)


def get_log_channel_id(server_id: int) -> int:
    """
    Get the log channel ID of the specified server
    :returns: 0 if no log channel is set, otherwise the ID.
    """
    return _server_configs.get(server_id, _default_conf).log_channel_id


async def set_log_channel_id(server_id: int, channel_id: int):
    await _set(server_id, "log_channel_id", channel_id)
