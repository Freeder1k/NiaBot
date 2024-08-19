import unittest

from common.utils import TableBuilder


class TestPlayer(unittest.TestCase):
    def test_table_builder(self):
        table_builder = TableBuilder.from_str(' l|c r ')
        table_builder.add_row('a', 'b', 'c')
        table_builder.add_seperator_row()
        for i in range(10):
            x = 10**i
            table_builder.add_row(str(x), str(x), str(x))

        res = table_builder.build()
        print(res)
        self.assertIsNotNone(res)


if __name__ == '__main__':
    unittest.main()
