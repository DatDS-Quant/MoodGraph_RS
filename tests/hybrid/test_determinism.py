"""
Unit tests cho Tính tất định và Phá vỡ hòa điểm (Determinism & Tie-Breaking - Group F).
"""

import pytest
from recommender.hybrid.fusion import reciprocal_rank_fusion, weighted_score_fusion


def test_01_identical_score_tie_break_by_movie_id_asc():
    """
    Khi nhiều ứng viên có cùng hybrid_score, hệ thống bắt buộc sắp xếp
    theo movieId tăng dần (movieId ASC) để đảm bảo tính tất định.
    """
    # 4 items với cùng rank 1 trong KG (cùng điểm RRF)
    als = []
    kg = [
        {"movieId": 999, "rank": 1, "raw_score": 1.0},
        {"movieId": 105, "rank": 1, "raw_score": 1.0},
        {"movieId": 500, "rank": 1, "raw_score": 1.0},
        {"movieId": 42, "rank": 1, "raw_score": 1.0},
    ]

    fused = reciprocal_rank_fusion(candidates_als=als, candidates_kg=kg, rrf_k=60)
    ordered_mids = [f["movieId"] for f in fused]
    # Phải được xếp theo thứ tự: 42, 105, 500, 999
    assert ordered_mids == [42, 105, 500, 999]


def test_02_deterministic_repeatability():
    """Chạy lặp 20 lần cho ra kết quả đồng nhất 100%."""
    als = [
        {"movieId": 2, "rank": 2, "raw_score": 3.0},
        {"movieId": 1, "rank": 1, "raw_score": 4.0},
        {"movieId": 3, "rank": 3, "raw_score": 2.0},
    ]
    kg = [
        {"movieId": 3, "rank": 1, "raw_score": 5.0},
        {"movieId": 2, "rank": 2, "raw_score": 4.0},
    ]

    base = reciprocal_rank_fusion(als, kg, rrf_k=60)
    base_order = [(item["movieId"], item["hybrid_score"], item["rank"]) for item in base]

    for _ in range(20):
        run = reciprocal_rank_fusion(als, kg, rrf_k=60)
        run_order = [(item["movieId"], item["hybrid_score"], item["rank"]) for item in run]
        assert run_order == base_order
