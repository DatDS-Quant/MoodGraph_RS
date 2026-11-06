"""
Khối 4: Hybrid Recommendation Engine & Serving API (MoodGraph Phase 4).
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

