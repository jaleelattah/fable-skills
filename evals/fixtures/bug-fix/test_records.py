import unittest
from records import merge_records


class MergeTests(unittest.TestCase):
    def test_unique_records(self):
        first = {"id": "a", "value": 1}
        second = {"id": "b", "value": 2}
        self.assertEqual(merge_records([first], [second]), [first, second])
