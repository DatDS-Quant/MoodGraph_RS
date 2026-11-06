"""
Unit tests cho Data Contracts và Schemas (Phase 4 Group A).
"""

import pytest
from recommender.hybrid.contracts import (
    CandidateSource,
    FusionStrategy,
    HybridRecommendationItem,
    HybridRecommendationResponse,
)


def test_01_hybrid_item_creation_and_fields():
    """Kiểm tra khởi tạo hợp lệ của HybridRecommendationItem."""
    item = HybridRecommendationItem(
        userId=1,
        movieId=101,
        hybrid_score=0.032,
        rank=1,
        source="BOTH",
        fusion_method="rrf",
        title="Inception",
        als_raw_score=4.8,
        als_rank=1,
        kg_raw_score=0.85,
        kg_rank=3,
        evidence=[{"path_type": "GENRE", "contribution": 0.5}],
    )
    assert item.userId == 1
    assert item.movieId == 101
    assert item.hybrid_score == 0.032
    assert item.rank == 1
    assert item.source == "BOTH"
    assert item.title == "Inception"
    assert len(item.evidence) == 1


def test_02_hybrid_item_validation_errors():
    """Kiểm tra các ràng buộc thẩm định giá trị và kiểu dữ liệu."""
    # Sai kiểu userId
    with pytest.raises(TypeError):
        HybridRecommendationItem(
            userId="invalid",  # type: ignore
            movieId=101,
            hybrid_score=1.0,
            rank=1,
            source="ALS",
            fusion_method="rrf",
        )

    # rank < 1
    with pytest.raises(ValueError):
        HybridRecommendationItem(
            userId=1,
            movieId=101,
            hybrid_score=1.0,
            rank=0,
            source="ALS",
            fusion_method="rrf",
        )

    # hybrid_score không hữu hạn (NaN / Inf)
    with pytest.raises(ValueError):
        HybridRecommendationItem(
            userId=1,
            movieId=101,
            hybrid_score=float("nan"),
            rank=1,
            source="ALS",
            fusion_method="rrf",
        )


def test_03_hybrid_item_to_dict_serialization():
    """Kiểm tra tính năng chuyển đổi sang dict chuẩn phục vụ JSON API."""
    item = HybridRecommendationItem(
        userId=42,
        movieId=500,
        hybrid_score=0.875,
        rank=2,
        source="ALS",
        fusion_method="weighted",
        title="The Matrix",
        als_raw_score=3.9,
    )
    d = item.to_dict()
    assert isinstance(d, dict)
    assert d["userId"] == 42
    assert d["movieId"] == 500
    assert d["hybrid_score"] == 0.875
    assert d["rank"] == 2
    assert d["source"] == "ALS"
    assert d["title"] == "The Matrix"
    assert d["kg_raw_score"] is None


def test_04_hybrid_response_to_dict():
    """Kiểm tra đóng gói HybridRecommendationResponse."""
    item = HybridRecommendationItem(
        userId=1,
        movieId=10,
        hybrid_score=0.5,
        rank=1,
        source="KG",
        fusion_method="rrf",
    )
    resp = HybridRecommendationResponse(
        userId=1,
        recommendations=[item],
        metadata={"latency_ms": 12.5, "cache_hit": False},
    )
    d = resp.to_dict()
    assert d["userId"] == 1
    assert len(d["recommendations"]) == 1
    assert d["metadata"]["latency_ms"] == 12.5
