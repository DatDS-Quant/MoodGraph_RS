"""
Unit tests cho Bộ nhớ đệm phục vụ suy luận (Cache & Performance - Group H).
"""

import time
import concurrent.futures
import pytest
from recommender.hybrid.cache import HybridRecommendationCache


def test_01_cache_basic_put_get():
    """Kiểm tra lưu trữ và truy xuất cơ bản."""
    cache = HybridRecommendationCache(max_size=10, ttl_seconds=60)
    key = (1, 10, "rrf", 0.5, 0.5, 60, "production")
    cache.put(key, "result_1")
    assert cache.get(key) == "result_1"

    stats = cache.stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 0
    assert stats["size"] == 1


def test_02_cache_lru_eviction():
    """Kiểm tra chính sách đào thải LRU khi vượt quá max_size."""
    cache = HybridRecommendationCache(max_size=2, ttl_seconds=60)
    cache.put(("key1",), "val1")
    cache.put(("key2",), "val2")
    # key1 được truy cập -> trở thành recently used
    _ = cache.get(("key1",))

    # Chèn key3 -> key2 (least recently used) bị đào thải
    cache.put(("key3",), "val3")

    assert cache.get(("key1",)) == "val1"
    assert cache.get(("key2",)) is None  # Đã bị đào thải
    assert cache.get(("key3",)) == "val3"

    stats = cache.stats()
    assert stats["evictions"] == 1


def test_03_cache_ttl_expiration():
    """Kiểm tra tự động hết hạn theo TTL."""
    cache = HybridRecommendationCache(max_size=10, ttl_seconds=1)
    cache.put(("key_temp",), "val_temp")
    assert cache.get(("key_temp",)) == "val_temp"

    # Đợi 1.1s để hết hạn
    time.sleep(1.1)
    assert cache.get(("key_temp",)) is None


def test_04_cache_concurrency_thread_safety():
    """Kiểm tra an toàn đa luồng khi ghi và đọc đồng thời."""
    cache = HybridRecommendationCache(max_size=500, ttl_seconds=60)

    def worker(worker_id: int):
        for i in range(100):
            k = (worker_id % 10, i % 20)
            cache.put(k, f"data_{worker_id}_{i}")
            _ = cache.get(k)

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(worker, w) for w in range(8)]
        for f in concurrent.futures.as_completed(futures):
            f.result()

    stats = cache.stats()
    assert stats["size"] <= 500
    assert stats["hits"] > 0
