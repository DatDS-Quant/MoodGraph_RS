"""
Unit tests cho Hợp nhất ứng viên (Candidate Union & Deduplication - Group B).
"""

import pytest
from recommender.hybrid.fusion import reciprocal_rank_fusion, weighted_score_fusion


def test_01_candidate_union_cardinality(mock_als_candidates, mock_kg_candidates):
    """
    Kiểm tra lực lượng tập hợp (cardinality) khi hợp nhất C_ALS(u) và C_KG(u).
    ALS có: {101, 102, 103, 104, 105} (5 items)
    KG có: {101, 103, 106, 107} (4 items)
    Tập hợp hợp nhất: {101, 102, 103, 104, 105, 106, 107} -> chính xác 7 items duy nhất (không trùng lặp).
    """
    fused = reciprocal_rank_fusion(mock_als_candidates, mock_kg_candidates, rrf_k=60)
    mids = [item["movieId"] for item in fused]
    assert len(mids) == 7
    assert len(set(mids)) == 7  # Không có phần tử trùng
    assert set(mids) == {101, 102, 103, 104, 105, 106, 107}


def test_02_source_attribution_integrity(mock_als_candidates, mock_kg_candidates):
    """
    Kiểm tra gán nhãn nguồn gốc (source attribution):
    - 101, 103: BOTH
    - 102, 104, 105: ALS
    - 106, 107: KG
    """
    fused = reciprocal_rank_fusion(mock_als_candidates, mock_kg_candidates, rrf_k=60)
    source_map = {item["movieId"]: item["source"] for item in fused}
    assert source_map[101] == "BOTH"
    assert source_map[103] == "BOTH"
    assert source_map[102] == "ALS"
    assert source_map[104] == "ALS"
    assert source_map[105] == "ALS"
    assert source_map[106] == "KG"
    assert source_map[107] == "KG"


def test_03_disjoint_candidate_sets():
    """Kiểm tra khi 2 tập ứng viên hoàn toàn rời nhau (disjoint)."""
    als = [{"movieId": 1, "rank": 1, "raw_score": 10.0}]
    kg = [{"movieId": 2, "rank": 1, "raw_score": 5.0}]
    fused = reciprocal_rank_fusion(als, kg, rrf_k=60)
    assert len(fused) == 2
    assert {f["movieId"] for f in fused} == {1, 2}
    assert all(f["source"] in ("ALS", "KG") for f in fused)
