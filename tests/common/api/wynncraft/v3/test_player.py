import unittest

import common.types.wynncraft
import tests.test_main
from common.api.wynncraft.v3 import player
from common.types.wynncraft import PlayerStats


class TestPlayer(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await tests.test_main.start()

    async def asyncTearDown(self):
        await tests.test_main.stop()

    async def test_stats(self):
        stats = await player.stats("1ed075fc-5aa9-42e0-a29f-640326c1d80c", full_result=True)
        self.assertIsInstance(stats, PlayerStats)
        print(stats)

        with self.assertRaises(player.UnknownPlayerException):
            await player.stats("00000000-0000-0000-0000-000000000000")

    async def test_characters(self):
        characters = await player.characters("1ed075fc-5aa9-42e0-a29f-640326c1d80c")
        self.assertIsInstance(characters, dict)
        self.assertIsInstance(list(characters.values())[0], common.types.wynncraft.CharacterShort)
        print(list(characters.items())[0])

        with self.assertRaises(player.UnknownPlayerException):
            await player.characters("00000000-0000-0000-0000-000000000000")

    async def test_abilities(self):
        abilities = await player.abilities("1ed075fc-5aa9-42e0-a29f-640326c1d80c",
                                           "13a4351c-8787-44e8-b3af-20a18d531bda")
        self.assertIsInstance(abilities[0], common.types.wynncraft.AbilityNode)
        print(abilities)

        with self.assertRaises(player.UnknownPlayerException):
            await player.abilities("00000000-0000-0000-0000-000000000000", "00000000-0000-0000-0000-000000000000")

        with self.assertRaises(player.UnknownPlayerException):
            await player.abilities("1ed075fc-5aa9-42e0-a29f-640326c1d80c",
                                   "00000000-0000-0000-0000-000000000000")

        with self.assertRaises(player.HiddenProfileException):
            await player.abilities("6e7e7d74-b813-400d-beff-71d7c4a98029",
                                   "fa9e0dc3-7249-4483-990d-db08bba70229")

    async def test_player_list(self):
        players = await player.player_list()
        self.assertIsInstance(players, dict)
        print({k: v for k, v in list(players.items())[:10]})

    async def test_player_count(self):
        count = await player.player_count()
        self.assertIsInstance(count, int)
        print("Player count:", count)
