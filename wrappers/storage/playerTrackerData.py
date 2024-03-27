from datetime import datetime

from async_lru import alru_cache

from niatypes.dataTypes import WynncraftGuild
from niatypes.enums import PlayerStatsIdentifier
from wrappers.api.wynncraft.v3.types import PlayerStats
from wrappers.storage import manager
import wrappers.api.wynncraft.v3.guild


@alru_cache(ttl=600)
async def get_stats(uuid: str, stat: PlayerStatsIdentifier, after: datetime = None, before: datetime = None) -> tuple:
    uuid = uuid.replace("-", "").lower()
    if after is None:
        after = datetime.min
    if before is None:
        before = datetime.max

    cur = await manager.get_cursor()
    res = await cur.execute(f"""
                SELECT {stat} as stat FROM player_tracking
                WHERE uuid = ?
                AND record_time >= ?
                AND record_time <= ?
                ORDER BY record_time
            """, (uuid, after, before))

    return tuple(row['stat'] for row in await res.fetchall())

@alru_cache(ttl=600)
async def get_leaderboard(stat: PlayerStatsIdentifier, guild: WynncraftGuild = None, after: datetime = None, before: datetime = None) -> dict[str, tuple]:
    if after is None:
        after = datetime.min
    if before is None:
        before = datetime.max

    uuids = None
    if guild is not None:
        try:
            guild_stats: wrappers.api.wynncraft.v3.types.GuildStats = await wrappers.api.wynncraft.v3.guild.stats(name=guild.name)
            uuids = tuple(uuid.replace("-", "").lower() for uuid in guild_stats.members.all.keys())
        except wrappers.api.wynncraft.v3.guild.UnknownGuildException:
            raise ValueError(f"Guild {guild.name} not found.")

    params = (after, before) + (uuids if uuids is not None else ())

    cur = await manager.get_cursor()
    res = await cur.execute(f"""
                SELECT uuid, stat from (
                    SELECT uuid, max(record_time), {stat} as stat from player_tracking
                    WHERE record_time >= ?
                    AND record_time <= ?
                    {f"AND uuid IN ({', '.join('?' for _ in uuids)})" if uuids is not None else ""}
                    GROUP BY uuid
                )
                WHERE stat > 0
                ORDER BY stat DESC
                LIMIT 100
            """, params)

    return {row['uuid']: row['stat'] for row in await res.fetchall()}


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
