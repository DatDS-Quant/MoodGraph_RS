"""
Unit tests cho Bảo toàn tính khả giải (Explainability & Evidence Preservation - Group E).
"""

import pytest
from recommender.hybrid.fusion import reciprocal_rank_fusion


def test_01_kg_evidence_preserved_intact(mock_als_candidates, mock_kg_candidates):
    """Xác nhận toàn bộ bằng chứng đường đi P1, P2, P3 từ KG được bảo toàn 100%."""
    fused = reciprocal_rank_fusion(mock_als_candidates, mock_kg_candidates, rrf_k=60)
    item_103 = next(item for item in fused if item["movieId"] == 103)

    path_types = [ev["path_type"] for ev in item_103["evidence"]]
    assert "GENRE" in path_types
    assert "GENOME" in path_types
    assert "ALS_LATENT_FACTOR" in path_types  # Vì là BOTH, nhận thêm ghi nhận từ ALS


def test_02_als_only_honest_attribution(mock_als_candidates, mock_kg_candidates):
    """
    Xác nhận các phim chỉ do ALS gợi ý (không có trong KG) KHÔNG bị ngụy tạo đường đi đồ thị,
    mà được giải thích minh bạch qua đặc trưng tiềm ẩn (ALS_LATENT_FACTOR).
    """
    fused = reciprocal_rank_fusion(mock_als_candidates, mock_kg_candidates, rrf_k=60)
    item_102 = next(item for item in fused if item["movieId"] == 102)

    assert item_102["source"] == "ALS"
    assert len(item_102["evidence"]) == 1
    ev = item_102["evidence"][0]
    assert ev["path_type"] == "ALS_LATENT_FACTOR"
    assert "collaborative" in ev["description"].lower() or "latent" in ev["description"].lower()

    # Tuyệt đối không chứa GENRE/GENOME/COLLABORATIVE giả mạo
    assert ev["path_type"] not in ("GENRE", "GENOME", "COLLABORATIVE")


def test_03_kg_only_has_no_als_latent_factor(mock_als_candidates, mock_kg_candidates):
    """Phim chỉ thuộc KG không chứa evidence ALS_LATENT_FACTOR."""
    fused = reciprocal_rank_fusion(mock_als_candidates, mock_kg_candidates, rrf_k=60)
    item_106 = next(item for item in fused if item["movieId"] == 106)
    assert item_106["source"] == "KG"
    path_types = [ev["path_type"] for ev in item_106["evidence"]]
    assert "ALS_LATENT_FACTOR" not in path_types
    assert "GENOME" in path_types

