import unittest
from cache import is_expired


class CacheTests(unittest.TestCase):
    def test_before_and_after(self):
        self.assertFalse(is_expired(10, 9))
        self.assertTrue(is_expired(10, 11))
