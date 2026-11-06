"""
Dịch vụ gợi ý lai ghép chính (Hybrid Recommendation Engine Service) - Phase 4.

Nhiệm vụ:
1. Kết hợp ứng viên từ 2 họ mô hình: ALS (CF latent factor) và KG (Path-based semantic graph).
2. Hợp nhất tập ứng viên: C_hybrid(u) = C_ALS(u) ∪ C_KG(u).
3. Lọc lịch sử đã xem nhiều lớp (Defense-in-depth Seen Filtering).
4. Áp dụng thuật toán dung hợp (RRF k=60 hoặc Weighted Score Fusion).
5. Bảo toàn tính khả giải (Explainability): giữ nguyên bằng chứng đồ thị và bổ sung giải thích ALS.
6. Đảm bảo tính tất định (Deterministic Tie-breaking: score DESC, movieId ASC).
7. Bộ nhớ đệm tốc độ cao (In-memory LRU Cache) đạt P95 < 200ms cho warm serving.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Sequence, Set, Union
from pathlib import Path

from recommender.hybrid.contracts import (
    CandidateSource,
    FusionStrategy,
    HybridRecommendationItem,
    HybridRecommendationResponse,
)
from recommender.hybrid.config import HybridConfig, load_hybrid_config
from recommender.hybrid.fusion import reciprocal_rank_fusion, weighted_score_fusion
from recommender.hybrid.cache import HybridRecommendationCache


class HybridRecommenderService:
    """
    Dịch vụ điều phối gợi ý lai ghép hợp nhất ALS và Knowledge Graph.
    """

    def __init__(
        self,
        als_service: Optional[Any] = None,
        kg_graph: Optional[Any] = None,
        config: Optional[HybridConfig] = None,
        cache: Optional[HybridRecommendationCache] = None,
    ) -> None:
        self.config = config or load_hybrid_config()
        self._als_service = als_service
        self._kg_graph = kg_graph

        if cache is not None:
            self.cache = cache
        elif self.config.cache_enabled:
            self.cache = HybridRecommendationCache(
                max_size=self.config.cache_max_size,
                ttl_seconds=self.config.cache_ttl_seconds,
            )
        else:
            self.cache = None

    @property
    def als_service(self) -> Any:
        """Khởi tạo lười ALS service nếu chưa được inject."""
        if self._als_service is None:
            from recommender.als.delivery import get_delivery_service
            self._als_service = get_delivery_service()
        return self._als_service

    @property
    def kg_graph(self) -> Any:
        """Khởi tạo lười KG graph nếu chưa được inject."""
        if self._kg_graph is None:
            from recommender.kg.recommend import get_default_graph
            self._kg_graph = get_default_graph()
        return self._kg_graph

    def recommend(
        self,
        user_id: int,
        top_n: Optional[int] = None,
        fusion_strategy: Optional[str] = None,
        weight_als: Optional[float] = None,
        weight_kg: Optional[float] = None,
        rrf_k: Optional[int] = None,
        filter_seen: bool = True,
        stage: str = "production",
        custom_seen: Optional[Set[int]] = None,
        use_cache: Optional[bool] = None,
        cross_score_als: Optional[bool] = None,
    ) -> HybridRecommendationResponse:
        """
        Sinh gợi ý lai ghép cho một người dùng với kiểm tra bộ nhớ đệm và đo đạc độ trễ thời gian thực.
        """
        start_time = time.perf_counter()
        effective_top_n = top_n if top_n is not None and top_n > 0 else self.config.default_top_n
        effective_strategy = (fusion_strategy or self.config.default_fusion_strategy).lower()
        effective_w_als = weight_als if weight_als is not None else self.config.weight_als
        effective_w_kg = weight_kg if weight_kg is not None else self.config.weight_kg
        effective_rrf_k = rrf_k if rrf_k is not None else self.config.rrf_k
        effective_cross_score = cross_score_als if cross_score_als is not None else self.config.cross_score_als

        # Kiểm tra Cache Key bao hàm đầy đủ các chiều phụ thuộc (tránh Cache Contamination)
        should_cache = (use_cache is not False) and (self.cache is not None) and (custom_seen is None)
        cache_key = (
            user_id,
            effective_top_n,
            effective_strategy,
            effective_w_als,
            effective_w_kg,
            effective_rrf_k,
            stage,
            filter_seen,
            self.config.top_k_candidates_als,
            self.config.top_k_candidates_kg,
            self.config.normalize_method,
            self.config.imputation_strategy,
            bool(effective_cross_score),
        )

        if should_cache and self.cache is not None:
            cached_resp = self.cache.get(cache_key)
            if cached_resp is not None:
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                # Cập nhật latency_ms cho cache hit
                meta = dict(cached_resp.metadata)
                meta["latency_ms"] = round(elapsed_ms, 3)
                meta["cache_hit"] = True
                return HybridRecommendationResponse(
                    userId=user_id,
                    recommendations=cached_resp.recommendations,
                    metadata=meta,
                )

        # 1. Thu thập danh sách phim đã xem để lọc (Seen Filtering)
        seen_movies: Set[int] = set()
        if custom_seen is not None:
            seen_movies.update(custom_seen)
        elif filter_seen:
            try:
                histories = self.als_service.get_seen_history(
                    user_ids=[user_id], stage=stage
                )
                seen_movies.update(histories.get(user_id, set()))
            except Exception:
                pass

        # 2. Sinh ứng viên từ ALS
        cand_count_als = self.config.top_k_candidates_als
        cand_als: List[Dict[str, Any]] = []
        is_cold_als = False
        try:
            cand_als = self.als_service.recommend(
                user_id=user_id,
                top_n=cand_count_als,
                stage=stage,
                custom_seen=seen_movies if filter_seen else set(),
            )
            if not cand_als:
                if hasattr(self.als_service, "generator") and hasattr(self.als_service.generator, "user_factors"):
                    if user_id not in self.als_service.generator.user_factors.user_to_idx:
                        is_cold_als = True
                else:
                    is_cold_als = True
        except Exception:
            is_cold_als = True

        # 3. Sinh ứng viên từ KG
        cand_count_kg = self.config.top_k_candidates_kg
        cand_kg: List[Dict[str, Any]] = []
        is_cold_kg = False
        try:
            from recommender.kg.recommend import recommend_kg
            cand_kg = recommend_kg(
                user_id=user_id,
                top_n=cand_count_kg,
                exclude_movie_ids=seen_movies if filter_seen else set(),
                graph=self.kg_graph,
            )
            if not cand_kg:
                is_cold_kg = True
        except Exception:
            is_cold_kg = True

        # 3.5. ALS Cross-scoring cho các ứng viên KG (nếu được kích hoạt)
        if effective_cross_score and cand_kg and not is_cold_als:
            try:
                gen = getattr(self.als_service, "generator", None)
                if gen and hasattr(gen, "user_factors") and hasattr(gen, "catalog"):
                    u_factors = gen.user_factors
                    catalog = gen.catalog
                    if user_id in u_factors.user_to_idx:
                        u_idx = u_factors.user_to_idx[user_id]
                        u_vec = u_factors.factors[u_idx]
                        existing_als_mids = {int(c["movieId"]) for c in cand_als}
                        import numpy as np
                        for k_item in cand_kg:
                            mid = int(k_item["movieId"])
                            if mid not in existing_als_mids and mid in catalog.movie_to_idx:
                                m_idx = catalog.movie_to_idx[mid]
                                raw_als = float(np.dot(u_vec, catalog.factors[m_idx]))
                                cand_als.append({
                                    "userId": user_id,
                                    "movieId": mid,
                                    "raw_score": raw_als,
                                    "rank": None,
                                    "model_name": "ALS_CROSS_SCORE",
                                    "model_version": getattr(self.als_service, "model_version", "ALS_R8_REG0.3_ITER10"),
                                    "title": k_item.get("title"),
                                })
            except Exception:
                pass

        # 4. Kiểm tra Cold-Start cả 2 hệ thống
        if is_cold_als and is_cold_kg and not cand_als and not cand_kg:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return HybridRecommendationResponse(
                userId=user_id,
                recommendations=[],
                metadata={
                    "latency_ms": round(elapsed_ms, 3),
                    "cache_hit": False,
                    "fusion_strategy": effective_strategy,
                    "is_cold_start": True,
                    "candidate_count_als": 0,
                    "candidate_count_kg": 0,
                    "candidate_count_union": 0,
                },
            )

        # 5. Defense-in-depth Seen Filtering trên cả 2 tập
        if filter_seen and seen_movies:
            cand_als = [c for c in cand_als if int(c["movieId"]) not in seen_movies]
            cand_kg = [c for c in cand_kg if int(c["movieId"]) not in seen_movies]

        # 6. Dung hợp (Fusion)
        fused_raw: List[Dict[str, Any]] = []
        if effective_strategy == "als_only":
            fused_raw = cand_als[:effective_top_n]
            # Chuẩn hóa format
            fused_raw = [
                {
                    "movieId": int(c["movieId"]),
                    "title": c.get("title"),
                    "hybrid_score": float(c.get("raw_score", 0.0)),
                    "rank": idx + 1,
                    "source": "ALS",
                    "fusion_method": "als_only",
                    "als_raw_score": float(c.get("raw_score", 0.0)),
                    "als_normalized_score": 1.0,
                    "als_rank": idx + 1,
                    "kg_raw_score": None,
                    "kg_normalized_score": None,
                    "kg_rank": None,
                    "evidence": [{
                        "path_type": "ALS_LATENT_FACTOR",
                        "model_version": c.get("model_version", "ALS_R8_REG0.3_ITER10"),
                        "raw_score": float(c.get("raw_score", 0.0)),
                        "description": "Collaborative matrix factorization latent representation",
                    }],
                }
                for idx, c in enumerate(fused_raw)
            ]
        elif effective_strategy == "kg_only":
            fused_raw = cand_kg[:effective_top_n]
            fused_raw = [
                {
                    "movieId": int(c["movieId"]),
                    "title": c.get("title"),
                    "hybrid_score": float(c.get("raw_score", 0.0)),
                    "rank": idx + 1,
                    "source": "KG",
                    "fusion_method": "kg_only",
                    "als_raw_score": None,
                    "als_normalized_score": None,
                    "als_rank": None,
                    "kg_raw_score": float(c.get("raw_score", 0.0)),
                    "kg_normalized_score": 1.0,
                    "kg_rank": idx + 1,
                    "evidence": c.get("evidence", []),
                }
                for idx, c in enumerate(fused_raw)
            ]
        elif effective_strategy == "weighted":
            fused_raw = weighted_score_fusion(
                candidates_als=cand_als,
                candidates_kg=cand_kg,
                weight_als=effective_w_als,
                weight_kg=effective_w_kg,
                normalize_method=self.config.normalize_method,
                imputation_strategy=self.config.imputation_strategy,
                top_n=effective_top_n,
            )
        else:  # Mặc định RRF
            fused_raw = reciprocal_rank_fusion(
                candidates_als=cand_als,
                candidates_kg=cand_kg,
                rrf_k=effective_rrf_k,
                top_n=effective_top_n,
            )

        # 7. Đóng gói thành HybridRecommendationItem và bổ sung title từ catalog đồ thị nếu thiếu
        movie_titles = getattr(self.kg_graph, "movies", {})
        recs: List[HybridRecommendationItem] = []
        for item in fused_raw:
            mid = int(item["movieId"])
            title = item.get("title")
            if not title and isinstance(movie_titles, dict) and mid in movie_titles:
                title = movie_titles[mid].get("title")

            rec_item = HybridRecommendationItem(
                userId=user_id,
                movieId=mid,
                hybrid_score=float(item["hybrid_score"]),
                rank=int(item["rank"]),
                source=str(item["source"]),
                fusion_method=str(item["fusion_method"]),
                title=title,
                als_raw_score=item.get("als_raw_score"),
                als_normalized_score=item.get("als_normalized_score"),
                als_rank=item.get("als_rank"),
                kg_raw_score=item.get("kg_raw_score"),
                kg_normalized_score=item.get("kg_normalized_score"),
                kg_rank=item.get("kg_rank"),
                evidence=item.get("evidence", []),
            )
            recs.append(rec_item)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        union_count = len(set(int(c["movieId"]) for c in cand_als) | set(int(c["movieId"]) for c in cand_kg))

        response = HybridRecommendationResponse(
            userId=user_id,
            recommendations=recs,
            metadata={
                "latency_ms": round(elapsed_ms, 3),
                "cache_hit": False,
                "fusion_strategy": effective_strategy,
                "is_cold_start": False,
                "cross_score_als": bool(effective_cross_score),
                "candidate_count_als": len(cand_als),
                "candidate_count_kg": len(cand_kg),
                "candidate_count_union": union_count,
            },
        )

        if should_cache and self.cache is not None:
            self.cache.put(cache_key, response)

        return response


# Singleton instance
_HYBRID_SERVICE_INSTANCE: Optional[HybridRecommenderService] = None


def get_hybrid_service() -> HybridRecommenderService:
    """Lấy hoặc khởi tạo thể hiện singleton của HybridRecommenderService."""
    global _HYBRID_SERVICE_INSTANCE
    if _HYBRID_SERVICE_INSTANCE is None:
        _HYBRID_SERVICE_INSTANCE = HybridRecommenderService()
    return _HYBRID_SERVICE_INSTANCE
