import aiohttp
from aiohttp import ClientSession
from yarl import URL

_sessions: dict[int, ClientSession] = {}
_session_urls: dict[int, str | URL | None] = {}
_initialized = False
_next_id = 0


def register_session(base_url: str | URL = None) -> int:
    global _next_id
    curr_id = _next_id
    _next_id += 1

    _session_urls[curr_id] = base_url
    if _initialized:
        _sessions[curr_id] = aiohttp.ClientSession(base_url)

    return curr_id


def get_session(session_id: int) -> ClientSession:
    if not _initialized:
        raise RuntimeError("Client sessions have not been initialized yet (run init_sessions first)!")

    if session_id not in _sessions:
        raise ValueError(f"There is no session with ID {session_id}.")

    return _sessions[session_id]


async def init_sessions():
    global _initialized
    if _initialized:
        raise RuntimeWarning("init_sessions() should only be called once")
    _initialized = True

    for s_id, url in _session_urls.items():
        _sessions[s_id] = aiohttp.ClientSession(url)


async def close():
    for session in _sessions.values():
        await session.close()

    global _initialized
    _initialized = False
