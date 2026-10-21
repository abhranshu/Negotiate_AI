"""
In-process caches for the NegotiateAI backend.

Why process-local is correct here: the deploy runs a single uvicorn worker
(settings.UVICORN_WORKERS = 1, and the VM cannot afford more), so there is
exactly one copy of every cache and nothing has to be coordinated across
workers. If that ever changes, these caches need a shared backing store.

Two kinds of entry live here, and they are *not* interchangeable:

1. Expensive, immutable artifacts (loaded ML models, tokenizers, pickled
   sklearn/LightGBM estimators). Built once, then shared read-only. These use
   `ttl=None` — a wall-clock TTL would only cause pointless reloads. Invalidate
   them by changing the cache *key* (e.g. include a fingerprint of the files
   they were built from) so a re-trained model is picked up automatically.

2. Mutable rows that are read far more often than they are written (the
   authenticated user). These carry a short TTL to bound staleness, plus an
   explicit `invalidate()` at every write site.

`get_or_create` holds a *per-key* lock rather than one global lock, so a slow
model load on a cold key doesn't block unrelated cache keys (or an auth lookup
that just wants a user row).
"""

import threading
import time
from typing import Any, Callable, Dict, Optional, Tuple

from api.config import settings

_MISS = object()


class TTLCache:
    """Small thread-safe key/value cache with optional per-entry expiry.

    Safe to hit from FastAPI's threadpool: sync endpoints run concurrently in
    worker threads, so every read/write is done under a lock.
    """

    def __init__(self, name: str, max_size: int = 128):
        self.name = name
        self.max_size = max_size
        self._entries: Dict[Any, Tuple[Optional[float], Any]] = {}  # key -> (expires_at, value)
        self._key_locks: Dict[Any, threading.Lock] = {}
        self._lock = threading.RLock()
        self.hits = 0
        self.misses = 0

    # ── reads ─────────────────────────────────────────────────────────────────

    def get(self, key: Any, default: Any = None) -> Any:
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                self.misses += 1
                return default
            expires_at, value = entry
            if expires_at is not None and expires_at <= time.monotonic():
                del self._entries[key]
                self.misses += 1
                return default
            self.hits += 1
            return value

    # ── writes ────────────────────────────────────────────────────────────────

    def set(self, key: Any, value: Any, ttl: Optional[float] = None) -> None:
        """Store `value` under `key`. ttl=None means "never expires"."""
        expires_at = None if ttl is None else time.monotonic() + ttl
        with self._lock:
            if key not in self._entries:
                self._make_room_locked()
            self._entries[key] = (expires_at, value)

    def get_or_create(self, key: Any, factory: Callable[[], Any],
                      ttl: Optional[float] = None) -> Any:
        """Return the cached value for `key`, building it with `factory` once.

        The factory runs at most once per key even under concurrent requests:
        without the per-key lock a cold key would have every racing request pay
        the full build cost (e.g. loading a DistilBERT model per uploaded file).
        """
        cached = self.get(key, _MISS)
        if cached is not _MISS:
            return cached

        with self._lock:
            key_lock = self._key_locks.get(key)
            if key_lock is None:
                key_lock = self._key_locks[key] = threading.Lock()

        with key_lock:
            # Another thread may have populated the key while we waited.
            cached = self.get(key, _MISS)
            if cached is not _MISS:
                return cached
            value = factory()
            self.set(key, value, ttl)
            return value

    # ── invalidation ──────────────────────────────────────────────────────────

    def invalidate(self, key: Any) -> None:
        with self._lock:
            self._entries.pop(key, None)
            self._key_locks.pop(key, None)

    def invalidate_where(self, predicate: Callable[[Any], bool]) -> int:
        """Drop every entry whose key matches `predicate`. Returns the count."""
        with self._lock:
            doomed = [k for k in self._entries if predicate(k)]
            for key in doomed:
                self.invalidate(key)
            return len(doomed)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()
            self._key_locks.clear()

    def stats(self) -> dict:
        with self._lock:
            return {
                "name": self.name,
                "size": len(self._entries),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
            }

    # ── internals ─────────────────────────────────────────────────────────────

    def _make_room_locked(self) -> None:
        """Evict to stay under max_size. Caller must hold self._lock."""
        if len(self._entries) < self.max_size:
            return
        now = time.monotonic()
        # Prefer dropping entries that have already expired.
        for key, (expires_at, _) in list(self._entries.items()):
            if expires_at is not None and expires_at <= now:
                self._entries.pop(key, None)
                self._key_locks.pop(key, None)
        # Still full: drop oldest-inserted (dicts preserve insertion order).
        while len(self._entries) >= self.max_size:
            key = next(iter(self._entries), None)
            if key is None:
                return
            self._entries.pop(key, None)
            self._key_locks.pop(key, None)


# ── Shared cache instances ────────────────────────────────────────────────────
# Built artifacts (models, tokenizers, pickled estimators). Never expire while
# the process lives; the key carries a fingerprint of what it was built from.
ML_MODEL_CACHE = TTLCache("ml-models", max_size=16)

# Authenticated user rows, keyed by user id. Short TTL because this is
# user-specific data: a deleted or edited user must not be honoured for long.
AUTH_USER_CACHE = TTLCache("auth-users", max_size=settings.AUTH_USER_CACHE_MAX)


def cache_stats() -> dict:
    """Snapshot of every cache — handy for a debug/health endpoint."""
    return {
        "ml_models": ML_MODEL_CACHE.stats(),
        "auth_users": AUTH_USER_CACHE.stats(),
    }
