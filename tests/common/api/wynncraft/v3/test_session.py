import unittest

import tests.test_main
from common.api.wynncraft.v3 import session


class TestSession(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await tests.test_main.start()

    async def asyncTearDown(self):
        await tests.test_main.stop()

    async def test(self):
        print("Quests count:", await session.get("/map/quests"))
        print("Remaining req:", session.calculate_remaining_requests())
        print("Reset time:", session.ratelimit_reset_time())
