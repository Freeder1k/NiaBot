import datetime
import unittest
import tests.test_main
from common.storage import playerTrackerData

class TestPlayerTrackerData(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await tests.test_main.start()

    async def asyncTearDown(self):
        await tests.test_main.stop()

    async def test_get_playtimes_for_guild(self):
        after = datetime.datetime.fromisoformat("2024-10-01")
        playtimes = await playerTrackerData.get_playtimes_for_guild("Cat Cafe", after=after)

        self.assertIsInstance(playtimes, dict)
        print(playtimes)