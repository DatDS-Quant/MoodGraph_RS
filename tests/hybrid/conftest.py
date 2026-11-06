"""
Fixtures dùng chung cho bộ kiểm thử Hybrid Recommender (Phase 4).
"""

import pytest
from typing import Dict, Any, List

from recommender.hybrid.contracts import (
    HybridRecommendationItem,
    HybridRecommendationResponse,
    CandidateSource,
    FusionStrategy,
)
from recommender.hybrid.config import HybridConfig
from recommender.hybrid.cache import HybridRecommendationCache
from recommender.kg.import_graph import InMemoryGraph, import_synthetic_data


@pytest.fixture
def mock_als_candidates() -> List[Dict[str, Any]]:
    """Tập ứng viên ALS giả lập với điểm raw_score giảm dần."""
    return [
        {"userId": 1, "movieId": 101, "raw_score": 4.8, "rank": 1, "title": "Inception"},
        {"userId": 1, "movieId": 102, "raw_score": 4.5, "rank": 2, "title": "The Dark Knight"},
        {"userId": 1, "movieId": 103, "raw_score": 4.2, "rank": 3, "title": "Interstellar"},
        {"userId": 1, "movieId": 104, "raw_score": 3.9, "rank": 4, "title": "Memento"},
        {"userId": 1, "movieId": 105, "raw_score": 3.5, "rank": 5, "title": "The Prestige"},
    ]


@pytest.fixture
def mock_kg_candidates() -> List[Dict[str, Any]]:
    """Tập ứng viên KG giả lập với điểm và bằng chứng truy vết."""
    return [
        {
            "userId": 1,
            "movieId": 103,  # Trùng với ALS rank 3
            "raw_score": 1.25,
            "rank": 1,
            "title": "Interstellar",
            "evidence": [
                {"path_type": "GENRE", "sourceMovieTitle": "Inception", "contribution": 0.45},
                {"path_type": "GENOME", "sourceMovieTitle": "Inception", "contribution": 0.80},
            ],
        },
        {
            "userId": 1,
            "movieId": 106,  # Chỉ có trong KG
            "raw_score": 0.95,
            "rank": 2,
            "title": "Arrival",
            "evidence": [
                {"path_type": "GENOME", "sourceMovieTitle": "Interstellar", "contribution": 0.95},
            ],
        },
        {
            "userId": 1,
            "movieId": 101,  # Trùng với ALS rank 1
            "raw_score": 0.85,
            "rank": 3,
            "title": "Inception",
            "evidence": [
                {"path_type": "GENRE", "sourceMovieTitle": "Memento", "contribution": 0.85},
            ],
        },
        {
            "userId": 1,
            "movieId": 107,  # Chỉ có trong KG
            "raw_score": 0.60,
            "rank": 4,
            "title": "Blade Runner 2049",
            "evidence": [
                {"path_type": "COLLABORATIVE", "neighborUserId": 42, "contribution": 0.60},
            ],
        },
    ]


@pytest.fixture
def synthetic_graph() -> InMemoryGraph:
    """Đồ thị InMemoryGraph với synthetic fixture cho testing."""
    g = InMemoryGraph()
    import_synthetic_data(g)
    return g


@pytest.fixture
def test_hybrid_config() -> HybridConfig:
    """Cấu hình tối ưu cho unit tests."""
    return HybridConfig(
        default_fusion_strategy="rrf",
        rrf_k=60,
        weight_als=0.5,
        weight_kg=0.5,
        top_k_candidates_als=10,
        top_k_candidates_kg=10,
        default_top_n=5,
        cache_enabled=True,
        cache_max_size=100,
        cache_ttl_seconds=60,
    )
