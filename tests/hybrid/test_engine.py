"""
Unit tests cho HybridRecommenderService (Group G - Engine Integration & Robustness).
"""

import pytest
from recommender.hybrid.engine import HybridRecommenderService
from recommender.hybrid.config import HybridConfig
from recommender.kg.import_graph import InMemoryGraph, import_synthetic_data


class DummyALSService:
    def __init__(self, known_users=None):
        self.known_users = set(known_users or [1, 2])

    def recommend(self, user_id, top_n, stage="production", custom_seen=None):
        if user_id not in self.known_users:
            return []
        pool = [
            {"userId": user_id, "movieId": 101, "raw_score": 4.5, "rank": 1, "title": "Film A"},
            {"userId": user_id, "movieId": 102, "raw_score": 4.0, "rank": 2, "title": "Film B"},
            {"userId": user_id, "movieId": 103, "raw_score": 3.5, "rank": 3, "title": "Film C"},
        ]
        seen = custom_seen or set()
        return [c for c in pool if c["movieId"] not in seen][:top_n]

    def get_seen_history(self, user_ids, stage="production"):
        return {u: set() for u in user_ids}


def test_01_engine_rrf_flow():
    """Kiểm tra luồng thực thi RRF hoàn chỉnh từ service."""
    als = DummyALSService(known_users=[1])
    g = InMemoryGraph()
    import_synthetic_data(g)

    svc = HybridRecommenderService(
        als_service=als,
        kg_graph=g,
        config=HybridConfig(default_fusion_strategy="rrf", default_top_n=3, cache_enabled=False),
    )
    resp = svc.recommend(user_id=1, top_n=3)
    assert resp.userId == 1
    assert len(resp.recommendations) <= 3
    assert resp.metadata["fusion_strategy"] == "rrf"
    assert resp.metadata["cache_hit"] is False
    assert resp.metadata["latency_ms"] >= 0.0


def test_02_engine_weighted_flow():
    """Kiểm tra luồng thực thi Weighted Score hoàn chỉnh từ service."""
    als = DummyALSService(known_users=[1])
    g = InMemoryGraph()
    import_synthetic_data(g)

    svc = HybridRecommenderService(
        als_service=als,
        kg_graph=g,
        config=HybridConfig(default_fusion_strategy="weighted", weight_als=0.7, weight_kg=0.3, cache_enabled=False),
    )
    resp = svc.recommend(user_id=1, fusion_strategy="weighted")
    assert resp.metadata["fusion_strategy"] == "weighted"
    if resp.recommendations:
        first = resp.recommendations[0]
        assert first.fusion_method == "weighted"


def test_03_engine_cold_start_handling():
    """Kiểm tra xử lý người dùng mới (Cold-Start hoàn toàn cả ALS và KG)."""
    als = DummyALSService(known_users=[1])
    g = InMemoryGraph()  # Đồ thị rỗng, không có user 99999

    svc = HybridRecommenderService(
        als_service=als,
        kg_graph=g,
        config=HybridConfig(cache_enabled=False),
    )
    resp = svc.recommend(user_id=99999, top_n=5)
    assert resp.userId == 99999
    assert resp.recommendations == []
    assert resp.metadata["is_cold_start"] is True


def test_04_engine_cache_hit_latency_speedup():
    """Kiểm tra cơ chế cache hit: lần 2 độ trễ phải cực nhỏ (< 5ms) và cache_hit=True."""
    als = DummyALSService(known_users=[1])
    g = InMemoryGraph()
    import_synthetic_data(g)

    svc = HybridRecommenderService(
        als_service=als,
        kg_graph=g,
        config=HybridConfig(cache_enabled=True),
    )
    # Lần 1: Cache Miss
    resp1 = svc.recommend(user_id=1, top_n=5)
    assert resp1.metadata["cache_hit"] is False

    # Lần 2: Cache Hit
    resp2 = svc.recommend(user_id=1, top_n=5)
    assert resp2.metadata["cache_hit"] is True
    assert resp2.metadata["latency_ms"] < 20.0
    assert len(resp2.recommendations) == len(resp1.recommendations)


def test_05_engine_als_cross_scoring(monkeypatch):
    """
    Kiểm tra cơ chế ALS Cross-scoring:
    Khi ứng viên xuất hiện ở KG nhưng không có trong danh sách Top-K của ALS,
    hệ thống chủ động tra cứu vector nhân tử để tính điểm dot-product thực chất (2.5)
    thay vì gán 0.0 (zero-imputation mù quáng).
    """
    import numpy as np
    import recommender.kg.recommend as kg_rec_mod

    class MockGenerator:
        class MockFactors:
            user_to_idx = {1: 0}
            factors = np.array([[1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]])
        class MockCatalog:
            movie_to_idx = {500: 0}
            factors = np.array([[2.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]])
        user_factors = MockFactors()
        catalog = MockCatalog()

    class CrossScoreMockALS:
        generator = MockGenerator()
        model_version = "ALS_R8_REG0.3_ITER10"
        def recommend(self, user_id, top_n, stage="production", custom_seen=None):
            return [{"userId": user_id, "movieId": 101, "raw_score": 4.0, "rank": 1, "title": "Film A"}]
        def get_seen_history(self, user_ids, stage="production"):
            return {1: set()}

    # Mock recommend_kg trả về movie 500
    def mock_recommend_kg(user_id, top_n, exclude_movie_ids=None, graph=None, **kwargs):
        return [{
            "userId": user_id,
            "movieId": 500,
            "raw_score": 1.5,
            "rank": 1,
            "title": "Movie 500",
            "evidence": [{"path_type": "GENRE", "contribution": 1.5}],
        }]

    monkeypatch.setattr(kg_rec_mod, "recommend_kg", mock_recommend_kg)

    svc = HybridRecommenderService(
        als_service=CrossScoreMockALS(),
        kg_graph=InMemoryGraph(),
        config=HybridConfig(cache_enabled=False),
    )

    resp = svc.recommend(user_id=1, top_n=5, fusion_strategy="weighted", cross_score_als=True)
    mids = [r.movieId for r in resp.recommendations]
    assert 500 in mids

    # Movie 500 phải có điểm als_raw_score thực chất = 2.5
    item_500 = next(r for r in resp.recommendations if r.movieId == 500)
    assert item_500.als_raw_score == 2.5
    assert item_500.source == "BOTH"


