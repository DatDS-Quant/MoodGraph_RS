"""
Hợp đồng dữ liệu và schema chuẩn hóa cho Hybrid Recommender (Phase 4).

Cung cấp:
- Enums cho nguồn ứng viên và chiến lược dung hợp (CandidateSource, FusionStrategy).
- Cấu trúc dữ liệu chi tiết cho từng gợi ý (HybridRecommendationItem).
- Cấu trúc phản hồi tổng thể kèm metadata đo lường (HybridRecommendationResponse).
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence


class CandidateSource(str, Enum):
    """Nguồn sinh ứng viên gợi ý."""
    ALS = "ALS"
    KG = "KG"
    BOTH = "BOTH"
    POPULARITY = "POPULARITY"


class FusionStrategy(str, Enum):
    """Chiến lược dung hợp điểm/hạng."""
    RRF = "rrf"
    WEIGHTED = "weighted"
    ALS_ONLY = "als_only"
    KG_ONLY = "kg_only"
    POPULARITY_ONLY = "popularity_only"


@dataclass(frozen=True)
class HybridRecommendationItem:
    """
    Bản ghi dữ liệu chuẩn hóa cho một phim được gợi ý bởi Hybrid Engine.
    Lưu giữ đầy đủ điểm số thành phần, thứ hạng thành phần và bằng chứng giải thích.
    """
    userId: int
    movieId: int
    hybrid_score: float
    rank: int
    source: str
    fusion_method: str
    title: Optional[str] = None
    als_raw_score: Optional[float] = None
    als_normalized_score: Optional[float] = None
    als_rank: Optional[int] = None
    kg_raw_score: Optional[float] = None
    kg_normalized_score: Optional[float] = None
    kg_rank: Optional[int] = None
    evidence: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not isinstance(self.userId, int):
            raise TypeError(f"userId must be int, got {type(self.userId)}")
        if not isinstance(self.movieId, int):
            raise TypeError(f"movieId must be int, got {type(self.movieId)}")
        if not math.isfinite(self.hybrid_score):
            raise ValueError(f"hybrid_score must be a finite float, got {self.hybrid_score}")
        if self.rank < 1:
            raise ValueError(f"rank must be >= 1, got {self.rank}")

    def to_dict(self) -> Dict[str, Any]:
        """Chuyển đổi sang dictionary chuẩn phục vụ JSON serialization/API response."""
        return {
            "userId": int(self.userId),
            "movieId": int(self.movieId),
            "title": self.title,
            "hybrid_score": float(self.hybrid_score),
            "rank": int(self.rank),
            "source": str(self.source),
            "fusion_method": str(self.fusion_method),
            "als_raw_score": float(self.als_raw_score) if self.als_raw_score is not None else None,
            "als_normalized_score": float(self.als_normalized_score) if self.als_normalized_score is not None else None,
            "als_rank": int(self.als_rank) if self.als_rank is not None else None,
            "kg_raw_score": float(self.kg_raw_score) if self.kg_raw_score is not None else None,
            "kg_normalized_score": float(self.kg_normalized_score) if self.kg_normalized_score is not None else None,
            "kg_rank": int(self.kg_rank) if self.kg_rank is not None else None,
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True)
class HybridRecommendationResponse:
    """
    Phản hồi phục vụ suy luận toàn diện từ Hybrid Engine.
    Bao gồm danh sách các gợi ý và metadata truy vết thời gian thực.
    """
    userId: int
    recommendations: List[HybridRecommendationItem]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "userId": int(self.userId),
            "recommendations": [item.to_dict() for item in self.recommendations],
            "metadata": dict(self.metadata),
        }

