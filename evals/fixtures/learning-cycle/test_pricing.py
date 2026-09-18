import unittest

from pricing import quote


class PricingTests(unittest.TestCase):
    def test_below_threshold(self):
        self.assertEqual(quote(5000), 5000)

    def test_above_threshold(self):
        self.assertEqual(quote(12000), 10800)


if __name__ == "__main__":
    unittest.main()
