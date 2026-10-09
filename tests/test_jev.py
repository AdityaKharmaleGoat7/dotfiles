import importlib.util
import json
import os
import sys
import unittest
from pathlib import Path
from urllib.error import HTTPError, URLError
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
            captured["url"] = req.full_url
            captured["method"] = req.method
            captured["timeout"] = timeout
            return FakeResponse({"answers": {"risk": {"choice": "low"}}})

        with patch.dict(os.environ, {"JEV_API_KEY": "test-secret"}, clear=True), patch.object(client_mod, "urlopen", fake_urlopen):
            result = client_mod.JevClient().decide({"x": 1}, {"risk": {"type": "choice"}})

        self.assertEqual(captured["auth"], "Bearer test-secret")
        self.assertEqual(captured["payload"]["model"], client_mod.DEFAULT_MODEL)
        self.assertEqual(captured["payload"]["state"], {"x": 1})
        self.assertEqual(captured["payload"]["questions"], {"risk": {"type": "choice"}})
        self.assertEqual(captured["url"], client_mod.DEFAULT_ENDPOINT)
        self.assertEqual(captured["method"], "POST")
        self.assertEqual(captured["timeout"], 30.0)
        self.assertNotIn("test-secret", json.dumps(result))

    def test_question_count_is_checked_before_http(self):
        with patch.dict(os.environ, {"JEV_API_KEY": "test-secret"}, clear=True), patch.object(client_mod, "urlopen") as send:
            for questions in ({}, {f"q{i}": {"type": "noul"} for i in range(21)}):
                with self.subTest(count=len(questions)), self.assertRaises(ValueError):
                    client_mod.JevClient().decide({}, questions)
            send.assert_not_called()

    def test_transport_errors_do_not_expose_exception_details(self):
        errors = [
            (HTTPError(client_mod.DEFAULT_ENDPOINT, 401, "test-secret", {}, None), "HTTP 401"),
            (URLError("test-secret"), "Could not reach"),
            (TimeoutError("test-secret"), "Could not reach"),
        ]
        for error, message in errors:
            with self.subTest(error=type(error).__name__), patch.dict(os.environ, {"JEV_API_KEY": "test-secret"}, clear=True), patch.object(client_mod, "urlopen", side_effect=error):
                with self.assertRaisesRegex(client_mod.JevError, message) as raised:
                    client_mod.JevClient().decide({}, {"risk": {"type": "choice"}})
                self.assertNotIn("test-secret", str(raised.exception))

    def test_invalid_json_is_rejected(self):
        response = FakeResponse(None)
        with patch.dict(os.environ, {"JEV_API_KEY": "test-secret"}, clear=True), patch.object(response, "read", return_value=b"not JSON"), patch.object(client_mod, "urlopen", return_value=response):
            with self.assertRaisesRegex(client_mod.JevError, "invalid JSON"):
                client_mod.JevClient().decide({}, {"risk": {"type": "choice"}})

    def test_invalid_response_envelopes_are_rejected(self):
        for payload in ([], {}, {"answers": []}, {"answers": {}}, {"answers": {"other": {}}}):
            with self.subTest(payload=payload), patch.dict(os.environ, {"JEV_API_KEY": "test-secret"}, clear=True), patch.object(client_mod, "urlopen", return_value=FakeResponse(payload)):
                with self.assertRaises(client_mod.JevError):
                    client_mod.JevClient().decide({}, {"risk": {"type": "choice"}})

    def test_commit_risk_rejects_empty_diff_before_api_call(self):
        with self.assertRaises(ValueError):
            risk_mod.classify("   ")


if __name__ == "__main__":
    unittest.main()
