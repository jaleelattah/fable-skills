import unittest
from pathlib import Path
from assets import resolve_asset


class AssetTests(unittest.TestCase):
    def test_child(self):
        self.assertEqual(resolve_asset("/tmp/assets", "logo.png"), Path("/tmp/assets/logo.png"))

    def test_outside(self):
        with self.assertRaises(ValueError):
            resolve_asset("/tmp/assets", "../private/key")
