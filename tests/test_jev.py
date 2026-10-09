import importlib.util
import io
import json
import os
import sys
import subprocess
import tempfile
import threading
import unittest
from contextlib import redirect_stderr, redirect_stdout
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from unittest.mock import Mock, patch

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
        client = Mock()
        with self.assertRaises(ValueError):
            risk_mod.classify("   ", client)
        client.decide.assert_not_called()


class CommitRiskTests(unittest.TestCase):
    def test_large_diff_is_rejected_before_api_call(self):
        client = Mock()
        with self.assertRaisesRegex(ValueError, "Stage a smaller change"):
            risk_mod.classify("x" * (risk_mod.MAX_DIFF_CHARS + 1), client)
        client.decide.assert_not_called()

    def test_limit_sized_diff_is_sent_in_full(self):
        response = {"answers": {"risk": {"type": "choice", "choice": "medium"}}}
        client = Mock()
        client.decide.return_value = response
        diff = "x" * risk_mod.MAX_DIFF_CHARS
        self.assertEqual(risk_mod.classify(diff, client), response)
        request = client.decide.call_args.kwargs
        self.assertEqual(request["state"], {"staged_git_diff": diff})
        self.assertEqual(set(request["questions"]["risk"]["criteria"]), {"low", "medium", "high"})

    def test_invalid_risk_choices_are_rejected(self):
        for answer in (None, [], {}, {"type": "score", "choice": "low"}, {"type": "choice", "choice": "unknown"}):
            client = Mock()
            client.decide.return_value = {"answers": {"risk": answer}}
            with self.subTest(answer=answer), self.assertRaisesRegex(client_mod.JevError, "invalid risk choice"):
                risk_mod.classify("diff", client)

    def test_cli_failures_leave_stdout_empty(self):
        for error in (ValueError("No staged changes"), client_mod.JevError("HTTP 401"), subprocess.CalledProcessError(128, "git")):
            stdout, stderr = io.StringIO(), io.StringIO()
            with self.subTest(error=type(error).__name__), patch.object(risk_mod, "staged_diff", side_effect=error), redirect_stdout(stdout), redirect_stderr(stderr):
                self.assertEqual(risk_mod.main(), 2)
            self.assertEqual(stdout.getvalue(), "")
            self.assertIn("jev-risk:", stderr.getvalue())

    def test_staged_git_diff_flows_through_http_to_json_output(self):
        response = {
            "answers": {
                "risk": {
                    "type": "choice", "choice": "low",
                    "probabilities": {"low": 0.9, "medium": 0.08, "high": 0.02},
                    "confidence": 0.9,
                }
            }
        }
        captured = {}

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                captured["path"] = self.path
                captured["auth"] = self.headers["Authorization"]
                captured["payload"] = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())

            def log_message(self, *args):
                pass

        with tempfile.TemporaryDirectory() as directory, HTTPServer(("127.0.0.1", 0), Handler) as server:
            repo = Path(directory)
            subprocess.run(["git", "init", "--quiet", str(repo)], check=True, capture_output=True)
            (repo / "example.txt").write_text("staged content\n")
            subprocess.run(["git", "add", "--", "example.txt"], cwd=repo, check=True, capture_output=True)
            (repo / "example.txt").write_text("unstaged content\n")
            client = client_mod.JevClient(endpoint=f"http://127.0.0.1:{server.server_port}/api/v1/systemone/")
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            stdout, stderr = io.StringIO(), io.StringIO()
            try:
                with patch.dict(os.environ, {"JEV_API_KEY": "test-secret"}, clear=True), patch.object(risk_mod.Path, "cwd", return_value=repo), patch.object(risk_mod, "JevClient", return_value=client), redirect_stdout(stdout), redirect_stderr(stderr):
                    self.assertEqual(risk_mod.main(), 0)
            finally:
                server.shutdown()
                thread.join()
            self.assertEqual(json.loads(stdout.getvalue()), response)
            self.assertEqual(stderr.getvalue(), "")
            self.assertEqual(captured["path"], "/api/v1/systemone/")
            self.assertEqual(captured["auth"], "Bearer test-secret")
            diff = captured["payload"]["state"]["staged_git_diff"]
            self.assertIn("+staged content", diff)
            self.assertNotIn("unstaged content", diff)


if __name__ == "__main__":
    unittest.main()
