"""Disk cache for LLM calls: every completion is recorded, scoring replays the record.

One JSONL file. Each line is one call::

    {"key", "request": {"model", "system", "prompt", "params"}, "response", "model_returned",
     "usage": {"input_tokens", "output_tokens"}, "timestamp"}

``key`` is the SHA-256 of the canonical JSON of the request, so a changed model, system prompt,
user prompt or parameter is a different entry. The API key is never part of a request or a
record. A cache hit costs nothing and is not counted as an API call; a miss calls the backend,
appends the record and counts one call against ``max_calls``. A :class:`CachedCompleter` without
a backend (``backend=None``) serves hits only and raises :class:`CacheMiss` on a miss, which is
how a published result is re-scored without credentials.
"""

from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .models import Completer, Completion


class CacheMiss(RuntimeError):
    """A request that is not in the cache, with no backend to make it."""


class CallBudgetExceeded(RuntimeError):
    """The cap on live API calls was reached."""


def request_key(model: str, system: str | None, prompt: str, params: dict[str, Any]) -> str:
    """SHA-256 hex digest of the canonical request."""
    blob = json.dumps(
        {"model": model, "system": system, "prompt": prompt, "params": params},
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CacheStats:
    """Live calls made through this object (hits excluded) and the tokens they used."""

    live_calls: int
    hits: int
    input_tokens: int
    output_tokens: int


def read_cache(path: str | Path) -> list[dict[str, Any]]:
    """All records of a cache file (empty when it does not exist)."""
    p = Path(path)
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def summarize_cache(path: str | Path) -> dict[str, Any]:
    """Totals over a cache file: calls, tokens, returned model ids, time span."""
    records = read_cache(path)
    stamps = sorted(r["timestamp"] for r in records)
    return {
        "calls": len(records),
        "input_tokens": sum(int(r["usage"]["input_tokens"]) for r in records),
        "output_tokens": sum(int(r["usage"]["output_tokens"]) for r in records),
        "models_returned": sorted({r["model_returned"] for r in records}),
        "first": stamps[0] if stamps else None,
        "last": stamps[-1] if stamps else None,
    }


class CachedCompleter:
    """A :class:`~evalkit.models.Completer` that records every call to ``cache_path``.

    ``model_id`` is the requested model (part of the key); with a backend it defaults to the
    backend's. Thread safe: lookups and appends share one lock, the backend call does not.
    """

    def __init__(
        self,
        backend: Completer | None,
        cache_path: str | Path,
        *,
        model_id: str | None = None,
        max_calls: int = 4000,
    ) -> None:
        if model_id is None:
            if backend is None:
                raise ValueError("a cache-only completer needs model_id")
            model_id = backend.model_id
        self.backend = backend
        self.model_id = model_id
        self.path = Path(cache_path)
        self.max_calls = max_calls
        self._lock = threading.Lock()
        self._records: dict[str, Completion] = {}
        self._live = 0
        self._hits = 0
        self._in_tokens = 0
        self._out_tokens = 0
        self._inflight: dict[str, threading.Event] = {}
        for rec in read_cache(self.path):
            self._records[rec["key"]] = Completion(
                text=rec["response"],
                model=rec["model_returned"],
                input_tokens=int(rec["usage"]["input_tokens"]),
                output_tokens=int(rec["usage"]["output_tokens"]),
            )
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def stats(self) -> CacheStats:
        with self._lock:
            return CacheStats(self._live, self._hits, self._in_tokens, self._out_tokens)

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int = 512,
        temperature: float | None = None,
    ) -> Completion:
        params = {"max_tokens": max_tokens, "temperature": temperature}
        key = request_key(self.model_id, system, prompt, params)
        backend = self.backend
        while True:
            with self._lock:
                hit = self._records.get(key)
                if hit is not None:
                    self._hits += 1
                    return hit
                if backend is None:
                    raise CacheMiss(f"not in cache {self.path} (key {key[:12]}); no backend")
                pending = self._inflight.get(key)
                if pending is None:
                    if self._live >= self.max_calls:
                        raise CallBudgetExceeded(f"live call cap of {self.max_calls} reached")
                    self._live += 1  # reserve before the call so concurrent misses respect the cap
                    done = self._inflight[key] = threading.Event()
                    break
            pending.wait()  # an identical request is in flight: wait for it, then hit the cache
        try:
            out = backend.complete(
                prompt, system=system, max_tokens=max_tokens, temperature=temperature
            )
        except BaseException:
            with self._lock:
                self._live -= 1
                del self._inflight[key]
            done.set()
            raise
        record = {
            "key": key,
            "request": {
                "model": self.model_id,
                "system": system,
                "prompt": prompt,
                "params": params,
            },
            "response": out.text,
            "model_returned": out.model,
            "usage": {"input_tokens": out.input_tokens, "output_tokens": out.output_tokens},
            "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
        }
        with self._lock:
            self._records[key] = out
            self._in_tokens += out.input_tokens
            self._out_tokens += out.output_tokens
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            del self._inflight[key]
        done.set()
        return out
