import unittest

import common.api.sessionManager
import common.api.wynncraft.v3.player
from common.storage import playerTrackerData
from datetime import datetime, timedelta
from common.types.enums import PlayerStatsIdentifier
from common.types.wynncraft import WynncraftGuild


class TestGuild(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await common.wrappers.storage.manager.init_database()

    async def asyncTearDown(self):
        await common.wrappers.storage.manager.close()

    async def test_add_record(self):
        await common.api.sessionManager.init_sessions()
        stats = await common.api.wynncraft.v3.player.stats('catboyfred')
        await common.api.sessionManager.close()
        await playerTrackerData.add_record(stats)


    async def test_get_stats(self):
        now = datetime.utcnow()
        stats_after = await playerTrackerData.get_stats('6e7e7d74b813400dbeff71d7c4a98029', PlayerStatsIdentifier.PLAYTIME, after=(now - timedelta(days=20)))
        stats_before = await playerTrackerData.get_stats('6e7e7d74b813400dbeff71d7c4a98029', PlayerStatsIdentifier.PLAYTIME, before=(now + timedelta(hours=1)))
        print(stats_after)
        print(stats_before)
        self.assertIsNotNone(stats_after)
        self.assertIsNotNone(stats_before)

    async def test_get_leaderboard(self):
        await common.api.sessionManager.init_sessions()
        now = datetime.utcnow()
        leaderboard = await playerTrackerData.get_leaderboard(PlayerStatsIdentifier.PLAYTIME, guild=WynncraftGuild('Nerfuria', 'Nia'))
        print(leaderboard)
        self.assertIsNotNone(leaderboard)

if __name__ == '__main__':
    unittest.main()
