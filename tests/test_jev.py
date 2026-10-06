import importlib.util
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
JEV_DIR = ROOT / "config" / "ai" / "jev"


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, JEV_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


client_mod = load("jev_client", "client.py")
sys.modules["client"] = client_mod
risk_mod = load("jev_commit_risk", "commit_risk.py")


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode()


class JevClientTests(unittest.TestCase):
    def test_missing_api_key_is_rejected(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(client_mod.JevError):
                client_mod.JevClient().decide({}, {"q": {"type": "choice"}})

    def test_request_uses_bearer_auth_without_returning_key(self):
        captured = {}

        def fake_urlopen(req, timeout):
            captured["auth"] = req.headers["Authorization"]
            captured["payload"] = json.loads(req.data.decode())
            return FakeResponse({"answers": {"risk": {"choice": "low"}}})

        with patch.dict(os.environ, {"JEV_API_KEY": "test-secret"}, clear=True), patch.object(client_mod, "urlopen", fake_urlopen):
            result = client_mod.JevClient().decide({"x": 1}, {"risk": {"type": "choice"}})

        self.assertEqual(captured["auth"], "Bearer test-secret")
        self.assertEqual(captured["payload"]["model"], client_mod.DEFAULT_MODEL)
        self.assertNotIn("test-secret", json.dumps(result))

    def test_commit_risk_rejects_empty_diff_before_api_call(self):
        with self.assertRaises(ValueError):
            risk_mod.classify("   ")


if __name__ == "__main__":
    unittest.main()
