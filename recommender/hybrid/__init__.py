"""
Khối 4: Động cơ Gợi ý Lai kết hợp (Hybrid Recommendation Engine) và Serving API cho MoodGraph.
Kết hợp kết quả gợi ý từ mô hình Phân rã Ma trận ALS (Task 3A) và Đồ thị Tri thức KG (Task 3B),
áp dụng các chiến lược hợp nhất RRF / Weighted Score Fusion, xử lý Cold-start và phục vụ REST API.
"""

from recommender.hybrid.contracts import (
    CandidateSource,
    FusionStrategy,
    HybridRecommendationItem,
    HybridRecommendationResponse,
)
from recommender.hybrid.config import HybridConfig, load_hybrid_config
from recommender.hybrid.fusion import (
    reciprocal_rank_fusion,
    weighted_score_fusion,
    normalize_min_max,
    normalize_percentile,
)
from recommender.hybrid.cache import HybridRecommendationCache
from recommender.hybrid.engine import HybridRecommenderService, get_hybrid_service

__all__ = [
    "CandidateSource",
    "FusionStrategy",
    "HybridRecommendationItem",
    "HybridRecommendationResponse",
    "HybridConfig",
    "load_hybrid_config",
    "reciprocal_rank_fusion",
    "weighted_score_fusion",
    "normalize_min_max",
    "normalize_percentile",
    "HybridRecommendationCache",
    "HybridRecommenderService",
    "get_hybrid_service",
]

