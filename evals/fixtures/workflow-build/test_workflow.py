import unittest

from workflow import run_workflow


class WorkflowSmokeTests(unittest.TestCase):
    def test_empty_input(self):
        def unused(*args):
            self.fail("empty input must not invoke callbacks")
        self.assertEqual(run_workflow([], unused, unused), [])

    def test_invalid_budget(self):
        with self.assertRaises(ValueError):
            run_workflow([], None, None, max_attempts=0)


if __name__ == "__main__":
    unittest.main()
