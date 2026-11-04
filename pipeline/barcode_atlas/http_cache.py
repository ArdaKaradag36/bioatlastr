"""Tiny disk cache + rate limiter used by every network call.

Every API response is stored as a file under data/cache/<namespace>/<hash>.json
so re-running a phase never repeats a request.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Callable

import requests

from .paths import CACHE


class RateLimiter:
    """Make sure at least `min_interval` seconds pass between two calls."""

    def __init__(self, min_interval: float):
        self.min_interval = min_interval
        self._last = 0.0

    def wait(self) -> None:
        delta = time.monotonic() - self._last
        if delta < self.min_interval:
            time.sleep(self.min_interval - delta)
        self._last = time.monotonic()


def cache_key(*parts: Any) -> str:
    """Stable short hash of any JSON-serialisable parts."""
    raw = json.dumps(parts, sort_keys=True, default=str)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


class DiskCache:
    """Key/value store: one JSON file per key inside a namespace folder."""

    def __init__(self, namespace: str, root: Path | None = None):
        self.dir = (root or CACHE) / namespace
        self.dir.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        return self.dir / f"{key}.json"

    def get(self, key: str) -> Any | None:
        p = self._path(key)
        if p.exists():
            with open(p, encoding="utf-8") as fh:
                return json.load(fh)
        return None

    def set(self, key: str, value: Any) -> None:
        tmp = self._path(key).with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(value, fh, ensure_ascii=False)
        tmp.replace(self._path(key))  # atomic: never leaves half-written cache files

    def has(self, key: str) -> bool:
        return self._path(key).exists()


class CachedJsonClient:
    """GET JSON with disk cache, rate limit and retry with back-off."""

    def __init__(
        self,
        namespace: str,
        min_interval: float,
        max_retries: int = 6,
        session: requests.Session | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self.cache = DiskCache(namespace)
        self.limiter = RateLimiter(min_interval)
        self.max_retries = max_retries
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": "turkey-plant-barcode-atlas/0.2 (research project; github.com/ArdaKaradag36/bioatlastr)"})
        self._sleep = sleep
        self.network_calls = 0
        self.cache_hits = 0

    def get_json(self, url: str, params: dict[str, Any] | None = None) -> Any:
        key = cache_key(url, params or {})
        hit = self.cache.get(key)
        if hit is not None:
            self.cache_hits += 1
            return hit

        last_error: Exception | None = None
        for attempt in range(self.max_retries):
            self.limiter.wait()
            self.network_calls += 1
            try:
                resp = self.session.get(url, params=params, timeout=60)
                if resp.status_code == 404:
                    # A missing resource is a valid, cacheable answer.
                    self.cache.set(key, {"_not_found": True})
                    return {"_not_found": True}
                if resp.status_code == 200:
                    data = resp.json()
                    self.cache.set(key, data)
                    return data
                last_error = RuntimeError(f"HTTP {resp.status_code} for {resp.url}")
            except (requests.RequestException, ValueError) as exc:
                last_error = exc
            # Exponential back-off: 2, 4, 8, ... seconds (max 60) - the API may be busy.
            wait = min(60, 2 ** (attempt + 1))
            print(f"  ! request failed ({last_error}); retry {attempt + 1}/{self.max_retries} in {wait}s")
            self._sleep(wait)
        raise RuntimeError(f"Giving up after {self.max_retries} attempts: {last_error}")
