import unittest
from credit import qualifies_for_credit


class CreditTests(unittest.TestCase):
    def test_current_threshold(self):
        self.assertFalse(qualifies_for_credit(1))
        self.assertTrue(qualifies_for_credit(2))
