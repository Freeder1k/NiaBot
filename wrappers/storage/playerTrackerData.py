from datetime import datetime

from async_lru import alru_cache

from niatypes.wynncraft.trackedPlayerStats import TrackedPlayerStats
from . import manager
from ..api.wynncraft.v3.types import PlayerStats


@alru_cache(ttl=60)
async def get_stats_before(uuid: str, record_time: datetime) -> TrackedPlayerStats | None:
    uuid = uuid.replace("-", "").lower()

    cur = await manager.get_cursor()
    res = await cur.execute("""
                SELECT * FROM player_tracking
                WHERE uuid = ?
                AND record_time <= ?
                ORDER BY record_time desc
                LIMIT 1
            """, (uuid, record_time))

    data = tuple(await res.fetchall())
    if len(data) == 0:
        return None

    return TrackedPlayerStats(**{k: data[0][k] for k in data[0].keys()})


@alru_cache(ttl=60)
async def get_stats_after(uuid: str, record_time: datetime) -> TrackedPlayerStats | None:
    uuid = uuid.replace("-", "").lower()

    cur = await manager.get_cursor()
    res = await cur.execute("""
                SELECT * FROM player_tracking
                WHERE uuid = ?
                AND record_time >= ?
                ORDER BY record_time
                LIMIT 1
            """, (uuid, record_time))

    data = tuple(await res.fetchall())
    if len(data) == 0:
        return None

    return TrackedPlayerStats(**{k: data[0][k] for k in data[0].keys()})


async def add_record(stats: PlayerStats, record_time: datetime = None):
    if record_time is None:
        record_time = datetime.utcnow()

    has_dungeons = stats.globalData.dungeons is not None
    has_raids = stats.globalData.raids is not None

    con = manager.get_connection()
    cur = await manager.get_cursor()
    await cur.execute(
        """
            INSERT INTO player_tracking (
                record_time,
                uuid,
                username,
                rank,
                support_rank, 
                first_join, 
                last_join, 
                playtime, 
                guild_uuid,
                guild_name, 
                guild_rank, 
                wars, 
                total_levels, 
                killed_mobs, 
                chests_found, 
                dungeons_total, 
                dungeons_ds, 
                dungeons_ip, 
                dungeons_ls, 
                dungeons_uc, 
                dungeons_ss, 
                dungeons_ib, 
                dungeons_gg,
                dungeons_ur, 
                dungeons_cds, 
                dungeons_cip, 
                dungeons_cls, 
                dungeons_css, 
                dungeons_cuc, 
                dungeons_cgg, 
                dungeons_cur, 
                dungeons_cib, 
                dungeons_ff, 
                dungeons_eo, 
                dungeons_ts, 
                raids_total, 
                raids_notg, 
                raids_nol, 
                raids_tcc, 
                raids_tna, 
                completed_quests, 
                pvp_kills, 
                pvp_deaths
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            record_time,
            stats.uuid.replace("-", "").lower(),
            stats.username,
            stats.rank,
            stats.supportRank,
            stats.firstJoin,
            stats.lastJoin,
            stats.playtime,
            stats.guild.uuid if stats.guild is not None else None,
            stats.guild.name if stats.guild is not None else None,
            stats.guild.rank if stats.guild is not None else None,
            stats.globalData.wars,
            stats.globalData.totalLevel,
            stats.globalData.killedMobs,
            stats.globalData.chestsFound,
            stats.globalData.dungeons.total if has_dungeons else 0,
            stats.globalData.dungeons.list.get('Decrepit Sewers', 0) if has_dungeons else 0,
            stats.globalData.dungeons.list.get('Infested Pit', 0) if has_dungeons else 0,
            stats.globalData.dungeons.list.get('Lost Sanctuary', 0) if has_dungeons else 0,
            stats.globalData.dungeons.list.get('Underworld Crypt', 0) if has_dungeons else 0,
            stats.globalData.dungeons.list.get('Sand-Swept Tomb', 0) if has_dungeons else 0,
            stats.globalData.dungeons.list.get('Ice Barrows', 0) if has_dungeons else 0,
            stats.globalData.dungeons.list.get('Galleon\'s Graveyard', 0) if has_dungeons else 0,
            stats.globalData.dungeons.list.get('Undergrowth Ruins', 0) if has_dungeons else 0,
            stats.globalData.dungeons.list.get('Corrupted Decrepit Sewers', 0) if has_dungeons else 0,
            stats.globalData.dungeons.list.get('Corrupted Infested Pit', 0) if has_dungeons else 0,
            stats.globalData.dungeons.list.get('Corrupted Lost Sanctuary', 0) if has_dungeons else 0,
            stats.globalData.dungeons.list.get('Corrupted Sand-Swept Tomb', 0) if has_dungeons else 0,
            stats.globalData.dungeons.list.get('Corrupted Underworld Crypt', 0) if has_dungeons else 0,
            stats.globalData.dungeons.list.get('Corrupted Galleon\'s Graveyard',
                                               0) if has_dungeons else 0,
            stats.globalData.dungeons.list.get('Corrupted Undergrowth Ruins', 0) if has_dungeons else 0,
            stats.globalData.dungeons.list.get('Corrupted Ice Barrows', 0) if has_dungeons else 0,
            stats.globalData.dungeons.list.get('Fallen Factory', 0) if has_dungeons else 0,
            stats.globalData.dungeons.list.get('Eldritch Outlook', 0) if has_dungeons else 0,
            stats.globalData.dungeons.list.get('Timelost Sanctum', 0) if has_dungeons else 0,
            stats.globalData.raids.total if has_raids else 0,
            stats.globalData.raids.list.get('Nest of the Grootslangs', 0) if has_raids else 0,
            stats.globalData.raids.list.get('Orphion\'s Nexus of Light', 0) if has_raids else 0,
            stats.globalData.raids.list.get('The Canyon Colossus', 0) if has_raids else 0,
            stats.globalData.raids.list.get('The Nameless Anomaly', 0) if has_raids else 0,
            stats.globalData.completedQuests,
            stats.globalData.pvp.kills,
            stats.globalData.pvp.deaths
        ))

    await con.commit()
