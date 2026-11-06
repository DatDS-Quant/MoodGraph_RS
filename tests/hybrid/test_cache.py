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


def test_05_cache_isolation_filter_seen():
    """
    Kiểm chứng ngăn chặn Cache Contamination:
    Yêu cầu filter_seen=True và filter_seen=False cho cùng một người dùng
    bắt buộc phải có Cache Key khác nhau, không được dùng chung kết quả.
    """
    from recommender.hybrid.engine import HybridRecommenderService
    from recommender.hybrid.config import HybridConfig
    from recommender.kg.import_graph import InMemoryGraph

    class ContaminationMockALS:
        def recommend(self, user_id, top_n, stage="production", custom_seen=None):
            # Nếu custom_seen có movie 10 (seen), loại bỏ nó
            pool = [
                {"movieId": 10, "raw_score": 5.0, "rank": 1},
                {"movieId": 20, "raw_score": 4.0, "rank": 2},
            ]
            seen = custom_seen or set()
            return [c for c in pool if c["movieId"] not in seen][:top_n]

        def get_seen_history(self, user_ids, stage="production"):
            return {1: {10}}

    svc = HybridRecommenderService(
        als_service=ContaminationMockALS(),
        kg_graph=InMemoryGraph(),
        config=HybridConfig(cache_enabled=True),
    )

    # 1. Gọi với filter_seen=True (lọc movie 10)
    resp_filtered = svc.recommend(user_id=1, top_n=2, filter_seen=True)
    mids_filtered = [r.movieId for r in resp_filtered.recommendations]
    assert 10 not in mids_filtered
    assert 20 in mids_filtered

    # 2. Gọi với filter_seen=False (không lọc movie 10)
    resp_unfiltered = svc.recommend(user_id=1, top_n=2, filter_seen=False)
    mids_unfiltered = [r.movieId for r in resp_unfiltered.recommendations]
    assert 10 in mids_unfiltered
    assert resp_unfiltered.metadata["cache_hit"] is False  # Không được hit cache của filtered!

    # 3. Gọi lại filter_seen=True -> phải hit cache của filtered
    resp_filtered_again = svc.recommend(user_id=1, top_n=2, filter_seen=True)
    assert resp_filtered_again.metadata["cache_hit"] is True
    assert 10 not in [r.movieId for r in resp_filtered_again.recommendations]


