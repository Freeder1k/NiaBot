import unittest

from common.api.wynncraft.v3.types import guild
from common.types.wynncraft import GuildStats


class TestGuild(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await common.wrappers.api.sessionManager.init_sessions()

    async def asyncTearDown(self):
        await common.wrappers.api.sessionManager.close()

    async def test_stats(self):
        stats1: GuildStats = await guild.stats(guild_name='Nerfuria')
        print(stats1)
        self.assertIsNotNone(stats1)

        stats2 = await guild.stats(guild_tag='Nia')
        print(stats2)
        self.assertIsNotNone(stats2)

        with self.assertRaises(common.wrappers.api.wynncraft.v3.guild.UnknownGuildException):
            await guild.stats(guild_name='a')

        with self.assertRaises(common.wrappers.api.wynncraft.v3.guild.UnknownGuildException):
            await guild.stats(guild_tag='a')

    async def test_guild_list(self):
        glist = await guild.list_guilds()
        print(glist)

    async def test_territory_list(self):
        tlist = await guild.list_territories()
        print(tlist)


if __name__ == '__main__':
    unittest.main()
