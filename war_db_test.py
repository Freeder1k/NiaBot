import asyncio
import time

from wrappers.storage import manager


async def main():
    await manager.init_database()

    cur = await manager.get_cursor()
    t = time.time()
    res = await cur.execute(f"""
        SELECT row_number() over () as rank, uuid, wars FROM (
            SELECT a.uuid as uuid, wars_max - wars_min as wars
            FROM (
                SELECT uuid, max(wars) as wars_max
                FROM player_tracking
                INDEXED BY wars_idx
                where wars > 0
                AND record_time <= '2024-03-10 00:00:00'
                AND record_time >= '2024-02-01 00:00:00'
                --- AND uuid in ('5c8c3075d6774b32b92bdf0aad06eb2b', '5b76bb77eb864817919a2ca25014323f')
                GROUP BY uuid
            ) as a
            JOIN (
                SELECT uuid, min(wars) as wars_min
                FROM player_tracking
                INDEXED BY wars_idx
                WHERE wars > 0
                AND record_time <= '2024-03-10 00:00:00'
                AND record_time >= '2024-02-01 00:00:00'
                --- AND uuid in ('5c8c3075d6774b32b92bdf0aad06eb2b', '5b76bb77eb864817919a2ca25014323f')
                GROUP BY uuid
            ) as b
            ON a.uuid = b.uuid AND a.wars_max > b.wars_min
            ORDER BY wars DESC
            LIMIT 1000
        );
                """)

    print("\n".join([f"{row['rank']: >5} {row['uuid']} {row['wars']: >6}" for row in await res.fetchall()]))
    print("Time: ", time.time() - t)

    await manager.close()


if __name__ == '__main__':
    asyncio.run(main())