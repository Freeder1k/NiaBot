from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum

from . import manager


class LogEntryType(IntEnum):
    MEMBER_JOIN = 1
    MEMBER_LEAVE = 2
    MEMBER_NAME_CHANGE = 3


@dataclass(frozen=True)
class LogEntry:
    log_id: int
    entry_type: LogEntryType
    content: str
    uuid: str
    timestamp: datetime

    @classmethod
    def make(cls, entry_type: int, timestamp: str, **kwargs):
        return cls(entry_type=LogEntryType(entry_type), timestamp=datetime.fromisoformat(timestamp), **kwargs)


async def log(entry_type: LogEntryType, content: str, uuid: str):
    con = manager.get_connection()
    cur = await con.cursor()
    await cur.execute("""
            INSERT INTO guild_member_log (entry_type, content, uuid)
            VALUES (?, ?, ?)
        """, (entry_type.value, content, uuid))

    await con.commit()


async def get_logs(*,
                   log_ids: list[int] | None = None,
                   entry_types: list[LogEntryType] | None = None,
                   uuids: list[str] | None = None,
                   before: datetime | None = None,
                   after: datetime | None = None):
    cur = await manager.get_cursor()

    conditions = []
    parameters = []
    if log_ids is not None:
        conditions.append(f"log_id IN ({', '.join('?' for _ in log_ids)})")
        parameters += log_ids
    if entry_types is not None:
        conditions.append(f"entry_type IN ({', '.join('?' for _ in entry_types)})")
        parameters += [t.value for t in entry_types]
    if uuids is not None:
        conditions.append(f"uuid IN ({', '.join('?' for _ in uuids)})")
        parameters += [uuid.replace("-", "").lower() for uuid in uuids]
    if before is not None:
        conditions.append(f"timestamp <= ?")
        parameters.append(before)
    if after is not None:
        conditions.append(f"timestamp >= ?")
        parameters.append(after)

    query = "SELECT * FROM guild_member_log"
    if len(conditions) > 0:
        query += " WHERE " + " AND ".join(condition for condition in conditions)

    res = await cur.execute(query, parameters)

    data = await res.fetchall()

    return tuple(LogEntry.make(**{k: row[k] for k in row.keys()}) for row in data)
