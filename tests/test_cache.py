import time

from akeyless_foundry.cache import TtlCache


class TestTtlCache:
    def test_set_and_get(self):
        cache: TtlCache[str] = TtlCache()
        now = time.monotonic()
        cache.set("key", "value", ttl_seconds=60, now=now)
        assert cache.get("key", now=now) == "value"

    def test_expired_entry_returns_none(self):
        cache: TtlCache[str] = TtlCache()
        now = time.monotonic()
        cache.set("key", "value", ttl_seconds=1, now=now)
        assert cache.get("key", now=now + 2) is None

    def test_clear(self):
        cache: TtlCache[str] = TtlCache()
        cache.set("key", "value", ttl_seconds=60)
        cache.clear()
        assert cache.get("key") is None
