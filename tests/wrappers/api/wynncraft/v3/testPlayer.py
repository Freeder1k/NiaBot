import unittest

import wrappers.api.sessionManager
from wrappers.api.wynncraft.v3 import player


class TestPlayer(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await wrappers.api.sessionManager.init_sessions()

    async def asyncTearDown(self):
        await wrappers.api.sessionManager.close()

    async def test_stats(self):
        stats = await player.stats('catboyfred')
        print(stats)
        self.assertIsNotNone(stats)

        statsfull = await player.stats('catboyfred', full_result=True)
        print(statsfull)
        self.assertIsNotNone(statsfull)

        with self.assertRaises(player.UnknownPlayerException):
            await player.stats('a')

        with self.assertRaises(player.UnknownPlayerException):
            await player.stats('a', full_result=True)

    async def test_characters(self):
        chars = await player.characters('catboyfred')
        print(chars)
        self.assertIsNotNone(chars)

        with self.assertRaises(player.UnknownPlayerException):
            await player.characters('a')

    async def test_abilities(self):
        abilities = await player.abilities('CatGirlBarnus', '6806753d-2067-4bba-9b82-81d2db86b7d4')
        print(abilities)
        self.assertIsNotNone(abilities)

        with self.assertRaises(player.UnknownPlayerException):
            await player.abilities('CatGirlBarnus', '6806753d-2067-4bba-9b82-81d2db86b7d5')

        with self.assertRaises(player.UnknownPlayerException):
            await player.abilities('a', '6806753d-2067-4bba-9b82-81d2db86b7d4')

        with self.assertRaises(player.HiddenProfileException):
            await player.abilities('catboyfred', 'fa9e0dc3-7249-4483-990d-db08bba70229')

    async def test_player_list(self):
        player_list = await player.player_list()
        print(player_list)
        self.assertIsNotNone(player_list)


if __name__ == '__main__':
    unittest.main()
