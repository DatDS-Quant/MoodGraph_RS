"""
Cấu hình tập trung cho Khối 4 Hybrid Recommender và Serving API.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class HybridConfig:
    """Cấu hình các tham số dung hợp và phục vụ của Hybrid Recommender."""
    default_fusion_strategy: str = "rrf"
    rrf_k: int = 60
    weight_als: float = 0.5
    weight_kg: float = 0.5
    top_k_candidates_als: int = 50
    top_k_candidates_kg: int = 50
    default_top_n: int = 10
    normalize_method: str = "min_max"
    imputation_strategy: str = "zero"
    cross_score_als: bool = False
    cache_enabled: bool = True
    cache_max_size: int = 10000
    cache_ttl_seconds: int = 3600
    min_liked_rating: float = 3.5

    def __post_init__(self) -> None:
        if self.rrf_k <= 0:
            raise ValueError(f"rrf_k must be > 0, got {self.rrf_k}")
        if self.default_top_n <= 0:
            raise ValueError(f"default_top_n must be > 0, got {self.default_top_n}")
        if self.top_k_candidates_als <= 0:
            raise ValueError(f"top_k_candidates_als must be > 0, got {self.top_k_candidates_als}")
        if self.top_k_candidates_kg <= 0:
            raise ValueError(f"top_k_candidates_kg must be > 0, got {self.top_k_candidates_kg}")


def load_hybrid_config() -> HybridConfig:
    """Tải cấu hình Hybrid từ biến môi trường hoặc giá trị mặc định."""
    try:
        from dotenv import load_dotenv
        env_path = Path(".env")
        if env_path.exists():
            load_dotenv(dotenv_path=env_path)
    except ImportError:
        pass

    fusion_strategy = os.getenv("HYBRID_DEFAULT_FUSION", "rrf").lower()
    rrf_k = int(os.getenv("HYBRID_RRF_K", "60"))
    w_als = float(os.getenv("HYBRID_WEIGHT_ALS", "0.5"))
    w_kg = float(os.getenv("HYBRID_WEIGHT_KG", "0.5"))
    cand_als = int(os.getenv("HYBRID_TOP_K_ALS", "50"))
    cand_kg = int(os.getenv("HYBRID_TOP_K_KG", "50"))
    top_n = int(os.getenv("HYBRID_DEFAULT_TOP_N", "10"))
    norm_method = os.getenv("HYBRID_NORMALIZE_METHOD", "min_max").lower()
    impute = os.getenv("HYBRID_IMPUTATION_STRATEGY", "zero").lower()
    cross_score = os.getenv("HYBRID_CROSS_SCORE_ALS", "false").lower() in ("true", "1", "yes")
    cache_enabled = os.getenv("HYBRID_CACHE_ENABLED", "true").lower() in ("true", "1", "yes")
    cache_max = int(os.getenv("HYBRID_CACHE_MAX_SIZE", "10000"))
    cache_ttl = int(os.getenv("HYBRID_CACHE_TTL_SECONDS", "3600"))

    # Đảm bảo tổng trọng số bằng 1 nếu chạy weighted
    total_w = w_als + w_kg
    if total_w > 0 and abs(total_w - 1.0) > 1e-4:
        w_als = w_als / total_w
        w_kg = w_kg / total_w

    return HybridConfig(
        default_fusion_strategy=fusion_strategy,
        rrf_k=rrf_k,
        weight_als=w_als,
        weight_kg=w_kg,
        top_k_candidates_als=cand_als,
        top_k_candidates_kg=cand_kg,
        default_top_n=top_n,
        normalize_method=norm_method,
        imputation_strategy=impute,
        cross_score_als=cross_score,
        cache_enabled=cache_enabled,
        cache_max_size=cache_max,
        cache_ttl_seconds=cache_ttl,
    )

