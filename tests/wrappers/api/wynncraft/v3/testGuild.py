import unittest

import wrappers.api.sessionManager
from niatypes.wynncraft.v3.guild import GuildStats
from wrappers.api.wynncraft.v3 import guild


class TestGuild(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await wrappers.api.sessionManager.init_sessions()

    async def asyncTearDown(self):
        await wrappers.api.sessionManager.close()

    async def test_stats(self):
        stats1: GuildStats = await guild.stats(guild_name='Nerfuria')
        print(stats1)
        self.assertIsNotNone(stats1)

        stats2 = await guild.stats(guild_prefix='Nia')
        print(stats2)
        self.assertIsNotNone(stats2)

        with self.assertRaises(guild.UnknownGuildException):
            await guild.stats(guild_name='a')

        with self.assertRaises(guild.UnknownGuildException):
            await guild.stats(guild_prefix='a')

    async def test_guild_list(self):
        glist = await guild.list_guilds()
        print(glist)

    async def test_territory_list(self):
        tlist = await guild.list_territories()
        print(tlist)


if __name__ == '__main__':
    unittest.main()
