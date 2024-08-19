import unittest

import common.types.wynncraft
import tests.test_main
from common.api.wynncraft.v3 import guild
from common.types.wynncraft import GuildStats


class TestGuild(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await tests.test_main.start()

    async def asyncTearDown(self):
        await tests.test_main.stop()

    async def test_stats(self):
        stats = await guild.stats(name="Nerfuria")
        self.assertIsInstance(stats, GuildStats)
        self.assertEqual(stats.name, "Nerfuria")

        stats = await guild.stats(tag="Nia")
        self.assertIsInstance(stats, GuildStats)
        self.assertEqual(stats.name, "Nerfuria")

        print(stats)

        with self.assertRaises(guild.UnknownGuildException):
            await guild.stats(name="X")

    async def test_list_guilds(self):
        guilds = await guild.list_guilds()
        self.assertIsInstance(guilds, list)
        self.assertIsInstance(guilds[0], common.types.wynncraft.WynncraftGuild)
        print(guilds[:5])

    async def test_list_territories(self):
        territories = await guild.list_territories()
        self.assertIsInstance(territories, dict)
        self.assertIsInstance(list(territories.values())[0], common.types.wynncraft.Territory)
        print(list(territories.items())[:5])

    async def test_find(self):
        guilds = await guild.find("Nerfuria")
        self.assertIsInstance(guilds, tuple)
        self.assertIsInstance(guilds[0], common.types.wynncraft.WynncraftGuild)
        print(guilds)

        guilds = await guild.find("Nia")
        self.assertIsInstance(guilds, tuple)
        self.assertIsInstance(guilds[0], common.types.wynncraft.WynncraftGuild)
        print(guilds)

        guilds = await guild.find("ico")
        self.assertIsInstance(guilds, tuple)
        self.assertIsInstance(guilds[0], common.types.wynncraft.WynncraftGuild)
        print(guilds)

        guilds = await guild.find("X")
        self.assertIsInstance(guilds, tuple)
        self.assertEqual(len(guilds), 0)
        print(guilds)

