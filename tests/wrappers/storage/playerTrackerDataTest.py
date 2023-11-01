import unittest

import wrappers.api.sessionManager
import wrappers.api.wynncraft.v3.player
import wrappers.storage.manager
from wrappers.storage import playerTrackerData
from datetime import datetime, timedelta

class TestGuild(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await wrappers.storage.manager.init_database()

    async def asyncTearDown(self):
        await wrappers.storage.manager.close()

    async def test_add_record(self):
        await wrappers.api.sessionManager.init_sessions()
        stats = await wrappers.api.wynncraft.v3.player.stats('catboyfred')
        await wrappers.api.sessionManager.close()
        await playerTrackerData.add_record(stats)


    async def test_get_stats(self):
        now = datetime.utcnow()
        stats_after = await playerTrackerData.get_stats_after('6e7e7d74b813400dbeff71d7c4a98029', (now - timedelta(hours=1)))
        stats_before = await playerTrackerData.get_stats_before('6e7e7d74b813400dbeff71d7c4a98029', (now + timedelta(hours=1)))
        print(stats_after)
        print(stats_before)
        self.assertIsNotNone(stats_after)
        self.assertIsNotNone(stats_before)

if __name__ == '__main__':
    unittest.main()
