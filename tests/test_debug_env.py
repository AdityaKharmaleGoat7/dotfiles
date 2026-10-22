import importlib.util
import pathlib
import unittest


SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "debug_env.py"
spec = importlib.util.spec_from_file_location("debug_env", SCRIPT)
debug_env = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(debug_env)


class DisplayEnvTests(unittest.TestCase):
    def test_redacts_sensitive_token_names(self):
        for name in ("API_TOKEN", "SECRET_KEY", "DB_PASSWORD", "HTTP_PROXY", "AUTH_COOKIE"):
            with self.subTest(name=name):
                self.assertEqual(debug_env.display_env(name, "value"), "<redacted>")

    def test_does_not_redact_substring_false_positives(self):
        for name in ("GIT_AUTHOR_NAME", "MONKEY_PATCH", "KEYBOARD_LAYOUT", "AUTHORS"):
            with self.subTest(name=name):
                self.assertEqual(debug_env.display_env(name, "value"), "value")


if __name__ == "__main__":
    unittest.main()
