import importlib.util
import pathlib
import sys
import unittest
from unittest import mock


SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "check_imports.py"
spec = importlib.util.spec_from_file_location("check_imports", SCRIPT)
check_imports = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(check_imports)


class CheckImportsTests(unittest.TestCase):
    def test_system_exit_is_reported_as_failure(self):
        with mock.patch.object(sys, "argv", ["check_imports.py", "demo"]), mock.patch.object(
            check_imports.importlib, "import_module", side_effect=SystemExit(2)
        ):
            self.assertEqual(check_imports.main(), 1)

    def test_keyboard_interrupt_is_not_swallowed(self):
        with mock.patch.object(sys, "argv", ["check_imports.py", "demo"]), mock.patch.object(
            check_imports.importlib, "import_module", side_effect=KeyboardInterrupt()
        ):
            with self.assertRaises(KeyboardInterrupt):
                check_imports.main()


if __name__ == "__main__":
    unittest.main()
