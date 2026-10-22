import importlib.util
import pathlib
import unittest


SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "check_processes.py"
spec = importlib.util.spec_from_file_location("check_processes", SCRIPT)
check_processes = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(check_processes)


class SearchTermTests(unittest.TestCase):
    def test_trims_nonempty_terms(self):
        self.assertEqual(check_processes.search_term("  python  "), "python")

    def test_rejects_empty_terms(self):
        with self.assertRaises(Exception):
            check_processes.search_term("   ")


if __name__ == "__main__":
    unittest.main()
