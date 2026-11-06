"""
Unit tests cho Phòng chống rò rỉ và Lọc lịch sử tương tác (Group D).
"""

import pytest
from recommender.hybrid.engine import HybridRecommenderService
from recommender.hybrid.config import HybridConfig


class MockALSService:
    def recommend(self, user_id, top_n, stage="production", custom_seen=None):
        pool = [
            {"userId": user_id, "movieId": 10, "raw_score": 4.5, "rank": 1},
            {"userId": user_id, "movieId": 20, "raw_score": 4.0, "rank": 2},
            {"userId": user_id, "movieId": 30, "raw_score": 3.5, "rank": 3},
            {"userId": user_id, "movieId": 40, "raw_score": 3.0, "rank": 4},
        ]
        seen = custom_seen or set()
        return [c for c in pool if c["movieId"] not in seen][:top_n]

    def get_seen_history(self, user_ids, stage="production"):
        # Giả định user 1 đã xem movie 10 trong Train
        return {1: {10}}


def test_01_seen_movie_filtered_defense_in_depth():
    """Kiểm tra phim đã xem (movie 10) bị loại trừ tuyệt đối khỏi kết quả gợi ý."""
    mock_als = MockALSService()
    svc = HybridRecommenderService(
        als_service=mock_als,
        kg_graph=None,
        config=HybridConfig(cache_enabled=False),
    )
    # Gợi ý với filter_seen=True
    resp = svc.recommend(user_id=1, top_n=5, filter_seen=True)
    rec_mids = [item.movieId for item in resp.recommendations]
    assert 10 not in rec_mids
    assert 20 in rec_mids or 30 in rec_mids


def test_02_custom_seen_filtering_override():
    """Kiểm tra truyền custom_seen lọc chính xác các phim chỉ định."""
    mock_als = MockALSService()
    svc = HybridRecommenderService(
        als_service=mock_als,
        kg_graph=None,
        config=HybridConfig(cache_enabled=False),
    )
    # Loại trừ thủ công movie 20 và 30
    resp = svc.recommend(user_id=1, top_n=5, filter_seen=True, custom_seen={20, 30})
    rec_mids = [item.movieId for item in resp.recommendations]
    assert 20 not in rec_mids
    assert 30 not in rec_mids
    assert 10 in rec_mids or 40 in rec_mids
