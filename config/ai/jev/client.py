"""Small standard-library client for the Jev decision API."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_ENDPOINT = "https://jev-ai.org/api/v1/systemone/"
DEFAULT_MODEL = "jev-1.13"
DEFAULT_KEY_FILE = Path(__file__).resolve().parents[3] / "local_keys.txt"


class JevError(RuntimeError):
    """Raised when a Jev request cannot be completed."""


@dataclass(frozen=True)
class JevClient:
    endpoint: str = DEFAULT_ENDPOINT
    model: str = DEFAULT_MODEL
    timeout: float = 30.0

    def decide(self, state: Any, questions: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
        api_key = os.environ.get("JEV_API_KEY")
        if not api_key:
            key_file = Path(os.environ.get("JEV_API_KEY_FILE", DEFAULT_KEY_FILE))
            try:
                lines = key_file.read_text(encoding="utf-8").splitlines()
            except FileNotFoundError:
                lines = []
            except (OSError, UnicodeError):
                raise JevError("Could not read the Jev key file.") from None
            for line in lines:
                name, separator, value = line.partition("=")
                if separator and name.strip() == "JEV_API_KEY":
                    api_key = value.strip()
                    break
        if not api_key:
            raise JevError("JEV_API_KEY is not set. Export it locally or add it to the Jev key file.")
        if not questions or len(questions) > 20:
            raise ValueError("questions must contain between 1 and 20 entries")

        payload = json.dumps({"model": self.model, "state": state, "questions": questions}).encode("utf-8")
        request = Request(
            self.endpoint,
            data=payload,
            method="POST",
            headers={
                "Authorization": "Bearer " + api_key,
                "Content-Type": "application/json",
                "User-Agent": "dotfiles-jev-study/1.0",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            reason = ""
            if exc.code == 401:
                try:
                    error = json.load(exc).get("error", {})
                    code = error.get("reason") if isinstance(error, dict) else None
                    if code in ("missing_bearer", "empty_token", "unknown_key", "wrong_key_type", "disabled", "revoked"):
                        reason = f" ({code})"
                except (ValueError, UnicodeError, OSError, AttributeError):
                    pass
            raise JevError(f"Jev API request failed with HTTP {exc.code}{reason}.") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise JevError("Could not reach Jev API. Check the connection and try again.") from exc
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise JevError("Jev API returned invalid JSON.") from exc
        if not isinstance(result, dict) or not isinstance(result.get("answers"), dict):
            raise JevError("Jev API response is missing an answers object.")
        if set(result["answers"]) != set(questions):
            raise JevError("Jev API response does not match the requested questions.")
        return result
