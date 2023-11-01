from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class TrackedPlayerStats:
    record_time: str   # datetime in ISO8601 format
    uuid: str
    username: str
    rank: str
    support_rank: str
    first_join: str     # datetime in ISO8601 format
    last_join: str      # datetime in ISO8601 format
    playtime: int
    guild_name: str
    guild_rank: str
    wars: int
    total_levels: int
    killed_mobs: int
    chests_found: int
    dungeons_total: int
    dungeons_ds: int
    dungeons_ip: int
    dungeons_ls: int
    dungeons_uc: int
    dungeons_ss: int
    dungeons_ib: int
    dungeons_gg: int
    dungeons_ur: int
    dungeons_cds: int
    dungeons_cip: int
    dungeons_cls: int
    dungeons_css: int
    dungeons_cuc: int
    dungeons_cgg: int
    dungeons_cur: int
    dungeons_cib: int
    dungeons_ff: int
    dungeons_eo: int
    dungeons_ts: int
    raids_total: int
    raids_notg: int
    raids_nol: int
    raids_tcc: int
    raids_tna: int
    completed_quests: int
    pvp_kills: int
    pvp_deaths: int