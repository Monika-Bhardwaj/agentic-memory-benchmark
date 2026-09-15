"""Model adapters.

Deterministic mock models require no API and are used for tests + the
smoke-scale instrument-validation run. The live adapter talks to an OpenAI-compatible
``/v1/chat/completions`` endpoint via stdlib ``urllib`` (no vendor SDK dependency);
keys come from environment variables only (see ``.env.example``).
"""

from __future__ import annotations

import abc
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

MEMORY_MARKER = "=== MEMORY (retrieved) ==="
MEMORY_END = "=== END ==="

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def load_dotenv(path: str | os.PathLike | None = None) -> None:
    """Minimal .env loader (stdlib only). Existing env vars take precedence."""
    p = Path(path) if path else Path(_REPO_ROOT) / ".env"
    if not p.is_file():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


class ModelClient(abc.ABC):
    model_name: str

    @abc.abstractmethod
    def complete(self, prompt: str, temperature: float, max_output_tokens: int) -> str: ...

    def metadata(self) -> dict[str, Any]:
        return {"model": self.model_name}


class FixedMockModel(ModelClient):
    """Returns a constant string. Exercises the pipeline without any prior knowledge."""

    model_name = "mock_fixed"

    def __init__(self, response: str = "MOCK_ANSWER_NOT_INFORMATIVE") -> None:
        self._response = response

    def complete(self, prompt: str, temperature: float, max_output_tokens: int) -> str:
        return self._response

    def metadata(self) -> dict[str, Any]:
        return {"model": self.model_name, "kind": "deterministic_mock"}


class PatternMockModel(ModelClient):
    """Deterministic 'perfect reader of the injected memory section'.

    Extracts the content of every retrieved item from the prompt and returns it
    verbatim (space-joined). It never sees ground truth and has no prior knowledge.
    This mock fs software-validates the instrument by making success depend only on
    whether the right memory was surfaced: it isolates the retrieval/management path
    from LLM reasoning.
    """

    model_name = "mock_pattern_reader"

    def complete(self, prompt: str, temperature: float, max_output_tokens: int) -> str:
        if MEMORY_MARKER not in prompt:
            return "MOCK: no memory available"
        body = prompt.split(MEMORY_MARKER, 1)[1].split(MEMORY_END, 1)[0]
        chunks = []
        for line in body.splitlines():
            line = line.strip()
            if not line:
                continue
            chunks.append(line)
        if not chunks:
            return "MOCK: no memory available"
        return " ".join(chunks)

    def metadata(self) -> dict[str, Any]:
        return {"model": self.model_name, "kind": "deterministic_mock"}


class LiveLLMClient(ModelClient):
    """OpenAI-compatible chat completions client (stdlib only).

    Config via env: LLM_BASE_URL (default https://api.openai.com/v1),
    LLM_API_KEY, LLM_MODEL (default from config), timeouts/retries from harness config.
    """

    def __init__(self, model: str, base_url: str | None = None, api_key: str | None = None,
                 timeout: float = 60.0, max_retries: int = 2) -> None:
        self.model_name = model
        self._base_url = (base_url or os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        self._api_key = api_key or os.environ.get("LLM_API_KEY", "")
        if not self._api_key:
            raise RuntimeError("LLM_API_KEY is not set (required for the live adapter)")

        self._timeout = timeout
        self._max_retries = max_retries

    def complete(self, prompt: str, temperature: float, max_output_tokens: int) -> str:
        url = f"{self._base_url}/chat/completions"
        payload = json.dumps({
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_output_tokens,
        }).encode("utf-8")
        last_err: Exception | None = None
        for attempt in range(self._max_retries + 1):
            if attempt:
                time.sleep(2 ** attempt)
            try:
                req = urllib.request.Request(url, data=payload, headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._api_key}",
                })
                with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"]
            except (urllib.error.URLError, urllib.error.HTTPError, KeyError, json.JSONDecodeError) as exc:
                last_err = exc
        raise RuntimeError(f"live model failed after {self._max_retries + 1} attempts: {last_err}")

    def metadata(self) -> dict[str, Any]:
        return {"model": self.model_name, "kind": "live_openai_compatible", "base_url": self._base_url}


def build_model(cfg_model: dict, harness_cfg: dict) -> ModelClient:
    load_dotenv()
    name = str(cfg_model.get("name", "mock_pattern_reader"))
    if name == "mock_pattern_reader":
        return PatternMockModel()
    if name == "mock_fixed":
        return FixedMockModel(str(cfg_model.get("mock_response", "MOCK_ANSWER_NOT_INFORMATIVE")))
    if name in ("REPLACE_WITH_MODEL", "", "None"):
        name = os.environ.get("LLM_MODEL", "")
    if not name:
        raise RuntimeError(
            "live model selected but no model id: set configs/benchmark_v0.yaml model.name "
            "or the LLM_MODEL env var"
        )
    return LiveLLMClient(
        model=name,
        timeout=float(harness_cfg.get("timeout_seconds", 60)),
        max_retries=int(harness_cfg.get("max_retries", 1)),
    )