"""
Unit tests cho các giải thuật dung hợp (Phase 4 Group C).
Bao gồm kiểm chứng độc lập với điểm số tính bằng tay (hand-calculated verification).
"""

import math
import pytest
from recommender.hybrid.fusion import (
    reciprocal_rank_fusion,
    weighted_score_fusion,
    normalize_min_max,
    normalize_percentile,
)


def test_01_normalize_min_max_basic():
    """Kiểm tra chuẩn hóa Min-Max tuyến tính."""
    scores = [10.0, 20.0, 30.0]
    norm = normalize_min_max(scores)
    assert norm == [0.0, 0.5, 1.0]

    # Biên: mảng đơn hoặc đồng nhất
    assert normalize_min_max([5.0, 5.0, 5.0]) == [1.0, 1.0, 1.0]
    assert normalize_min_max([]) == []


def test_02_normalize_percentile_basic():
    """Kiểm tra chuẩn hóa thứ hạng theo phân vị."""
    scores = [10.0, 50.0, 20.0]
    norm = normalize_percentile(scores)
    assert norm[0] == 1.0 / 3.0
    assert norm[2] == 2.0 / 3.0
    assert norm[1] == 1.0


def test_03_rrf_hand_calculated_scores():
    """
    Kiểm chứng công thức RRF với các giá trị tính bằng tay chính xác.
    Cho k = 60:
    Item 101: ALS rank 1 -> 1 / (60 + 1) = 1/61 ≈ 0.01639344
              KG rank 3  -> 1 / (60 + 3) = 1/63 ≈ 0.01587302
              Total score = 1/61 + 1/63 = 124 / 3843 ≈ 0.03226646

    Item 103: ALS rank 3 -> 1 / (60 + 3) = 1/63 ≈ 0.01587302
              KG rank 1  -> 1 / (60 + 1) = 1/61 ≈ 0.01639344
              Total score = 1/63 + 1/61 = 124 / 3843 ≈ 0.03226646

    Vì Item 101 và 103 cùng điểm (0.03226646), tie-break bằng movieId ASC:
    Thứ hạng 1: Item 101
    Thứ hạng 2: Item 103
    """
    als = [
        {"movieId": 101, "rank": 1, "raw_score": 5.0},
        {"movieId": 103, "rank": 3, "raw_score": 4.0},
    ]
    kg = [
        {"movieId": 103, "rank": 1, "raw_score": 2.0},
        {"movieId": 101, "rank": 3, "raw_score": 1.0},
    ]

    fused = reciprocal_rank_fusion(candidates_als=als, candidates_kg=kg, rrf_k=60)
    assert len(fused) == 2

    expected_score = (1.0 / 61.0) + (1.0 / 63.0)
    assert math.isclose(fused[0]["hybrid_score"], expected_score, rel_tol=1e-7)
    assert math.isclose(fused[1]["hybrid_score"], expected_score, rel_tol=1e-7)

    # Kiểm tra tie-break: 101 đứng trước 103 vì 101 < 103
    assert fused[0]["movieId"] == 101
    assert fused[0]["rank"] == 1
    assert fused[1]["movieId"] == 103
    assert fused[1]["rank"] == 2


def test_04_weighted_score_fusion_hand_calculated():
    """
    Kiểm chứng Weighted Score Fusion với trọng số w_ALS = 0.6, w_KG = 0.4.
    ALS:
      mid 1: raw 10.0 -> norm = 0.0 (min)
      mid 2: raw 20.0 -> norm = 1.0 (max)
    KG:
      mid 2: raw 5.0 -> norm = 0.0 (min)
      mid 3: raw 15.0 -> norm = 1.0 (max)

    Ứng viên hợp nhất:
    mid 1: norm_als = 0.0, norm_kg = 0.0 (imputed) -> score = 0.6*0.0 + 0.4*0.0 = 0.0
    mid 2: norm_als = 1.0, norm_kg = 0.0 -> score = 0.6*1.0 + 0.4*0.0 = 0.60
    mid 3: norm_als = 0.0 (imputed), norm_kg = 1.0 -> score = 0.6*0.0 + 0.4*1.0 = 0.40

    Thứ tự mong đợi:
    Rank 1: mid 2 (score 0.60)
    Rank 2: mid 3 (score 0.40)
    Rank 3: mid 1 (score 0.00)
    """
    als = [
        {"movieId": 1, "raw_score": 10.0, "rank": 2},
        {"movieId": 2, "raw_score": 20.0, "rank": 1},
    ]
    kg = [
        {"movieId": 2, "raw_score": 5.0, "rank": 2},
        {"movieId": 3, "raw_score": 15.0, "rank": 1},
    ]

    fused = weighted_score_fusion(
        candidates_als=als,
        candidates_kg=kg,
        weight_als=0.6,
        weight_kg=0.4,
        normalize_method="min_max",
    )
    assert len(fused) == 3
    assert fused[0]["movieId"] == 2
    assert math.isclose(fused[0]["hybrid_score"], 0.60, abs_tol=1e-5)
    assert fused[1]["movieId"] == 3
    assert math.isclose(fused[1]["hybrid_score"], 0.40, abs_tol=1e-5)
    assert fused[2]["movieId"] == 1
    assert math.isclose(fused[2]["hybrid_score"], 0.00, abs_tol=1e-5)


def test_05_rrf_empty_inputs():
    """Kiểm tra xử lý danh sách rỗng trong RRF."""
    assert reciprocal_rank_fusion([], []) == []
    single_als = [{"movieId": 1, "rank": 1, "raw_score": 3.0}]
    fused = reciprocal_rank_fusion(single_als, [])
    assert len(fused) == 1
    assert fused[0]["movieId"] == 1
    assert fused[0]["source"] == "ALS"

