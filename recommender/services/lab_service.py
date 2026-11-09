"""
MoodGraph Phase 5: Recommendation Lab Application Service.
Provides multi-model comparison, overlap analysis (Jaccard, rank correlation),
model registry, and verified benchmark evaluation serving for Mode B.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple

from recommender.storage import (
    MovieCatalogRepository,
    ResearchMetricsRepository,
    SQLiteStateRepository,
    get_catalog_repository,
    get_research_metrics_repository,
    get_sqlite_state_repository,
)

logger = logging.getLogger("recommender.services.lab_service")


class LabService:
    """Service orchestrating Mode B Recommendation Lab experiments and comparisons."""

    def __init__(
        self,
        hybrid_engine: Optional[Any] = None,
        metrics_repo: Optional[ResearchMetricsRepository] = None,
        catalog_repo: Optional[MovieCatalogRepository] = None,
        sqlite_repo: Optional[SQLiteStateRepository] = None,
    ):
        self.hybrid_engine = hybrid_engine
        self.metrics_repo = metrics_repo or get_research_metrics_repository()
        self.catalog_repo = catalog_repo or get_catalog_repository()
        self.sqlite_repo = sqlite_repo or get_sqlite_state_repository()

    def get_registered_models(self) -> Dict[str, Any]:
        """Returns catalog of models registered in the Recommendation Lab."""
        models = self.metrics_repo.get_registered_models()
        return {
            "models": models,
            "fusion_strategies": ["rrf", "weighted", "borda_count", "cascade"],
        }

    def get_benchmark_metrics(self, split: str = "validation", metric_group: str = "all") -> Dict[str, Any]:
        """Returns verified experimental offline evaluation metrics from Phase 4."""
        return self.metrics_repo.get_metrics_comparison(split=split, metric_group=metric_group)

    def get_system_metadata(self) -> Dict[str, Any]:
        """Returns end-to-end dataset size, split provenance, model dims, and system info."""
        return self.metrics_repo.get_system_metadata()

    def compare_models(
        self,
        user_id: int,
        models: List[str],
        top_n: int = 10,
        filter_seen: bool = True,
        rrf_k: int = 60,
        weight_als: float = 0.5,
        weight_kg: float = 0.5,
    ) -> Dict[str, Any]:
        """
        Runs multiple recommendation models in parallel/sequence for user_id,
        records latency, and computes cross-model alignment metrics (Jaccard, Rank correlation).
        """
        results: Dict[str, Dict[str, Any]] = {}

        for model_id in models:
            t0 = time.perf_counter()
            recs_items: List[Dict[str, Any]] = []

            try:
                if self.hybrid_engine is not None:
                    if model_id == "als":
                        resp = self.hybrid_engine.recommend(
                            user_id=user_id,
                            top_n=top_n,
                            fusion_strategy="als_only",
                            filter_seen=filter_seen,
                            use_cache=False,
                        )
                        recs_items = [
                            {
                                "movieId": it.movieId,
                                "title": it.title,
                                "score": round(it.hybrid_score, 4),
                                "rank": it.rank,
                                "source": it.source,
                            }
                            for it in resp.recommendations
                        ]
                    elif model_id == "kg":
                        resp = self.hybrid_engine.recommend(
                            user_id=user_id,
                            top_n=top_n,
                            fusion_strategy="kg_only",
                            filter_seen=filter_seen,
                            use_cache=False,
                        )
                        recs_items = [
                            {
                                "movieId": it.movieId,
                                "title": it.title,
                                "score": round(it.hybrid_score, 4),
                                "rank": it.rank,
                                "source": it.source,
                            }
                            for it in resp.recommendations
                        ]
                    elif model_id in ("hybrid_rrf", "rrf"):
                        resp = self.hybrid_engine.recommend(
                            user_id=user_id,
                            top_n=top_n,
                            fusion_strategy="rrf",
                            rrf_k=rrf_k,
                            filter_seen=filter_seen,
                            use_cache=False,
                        )
                        recs_items = [
                            {
                                "movieId": it.movieId,
                                "title": it.title,
                                "score": round(it.hybrid_score, 4),
                                "rank": it.rank,
                                "source": it.source,
                            }
                            for it in resp.recommendations
                        ]
                    elif model_id in ("hybrid_weighted", "weighted"):
                        resp = self.hybrid_engine.recommend(
                            user_id=user_id,
                            top_n=top_n,
                            fusion_strategy="weighted",
                            weight_als=weight_als,
                            weight_kg=weight_kg,
                            filter_seen=filter_seen,
                            use_cache=False,
                        )
                        recs_items = [
                            {
                                "movieId": it.movieId,
                                "title": it.title,
                                "score": round(it.hybrid_score, 4),
                                "rank": it.rank,
                                "source": it.source,
                            }
                            for it in resp.recommendations
                        ]
                    elif model_id == "popularity":
                        # Return top popular movies from catalog
                        recs_items = [
                            {
                                "movieId": mid,
                                "title": (self.catalog_repo.get_movie_by_id(mid) or {}).get("title", f"Movie {mid}"),
                                "score": round(1.0 / (idx + 1), 4),
                                "rank": idx + 1,
                                "source": "POPULARITY",
                            }
                            for idx, mid in enumerate([318, 296, 356, 593, 260, 480, 2571, 110, 589, 527][:top_n])
                        ]
                else:
                    # Fallback if engine is not pre-warmed
                    recs_items = []
            except Exception as e:
                logger.error(f"Error executing model {model_id} for user {user_id}: {e}")
                recs_items = []

            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            results[model_id] = {
                "model_id": model_id,
                "execution_time_ms": round(elapsed_ms, 3),
                "recommendations_count": len(recs_items),
                "recommendations": recs_items,
            }

        # Compute Pairwise Overlap Metrics
        pairwise_overlaps: List[Dict[str, Any]] = []
        model_keys = list(results.keys())
        for i in range(len(model_keys)):
            for j in range(i + 1, len(model_keys)):
                m_a = model_keys[i]
                m_b = model_keys[j]

                list_a = results[m_a]["recommendations"]
                list_b = results[m_b]["recommendations"]

                # Deduplicate candidates while preserving first occurrence and rank order
                seen_a: Set[int] = set()
                ordered_a: List[Dict[str, Any]] = []
                for it in list_a:
                    mid = it.get("movieId")
                    if mid is not None and mid not in seen_a:
                        seen_a.add(mid)
                        ordered_a.append(it)

                seen_b: Set[int] = set()
                ordered_b: List[Dict[str, Any]] = []
                for it in list_b:
                    mid = it.get("movieId")
                    if mid is not None and mid not in seen_b:
                        seen_b.add(mid)
                        ordered_b.append(it)

                set_a = seen_a
                set_b = seen_b

                intersection = set_a & set_b
                union = set_a | set_b
                jaccard = len(intersection) / float(len(union)) if union else 0.0

                # Compute Spearman rank correlation strictly on relative order of common items
                # Semantics:
                # - For k < 2 (0 or 1 common movie): rank correlation is undefined (return None).
                # - For k >= 2: we extract the common movies in their relative rank order in Model A and Model B.
                #   Assigning relative ranks 1..k ensures rho is mathematically well-defined and strictly in [-1.0, 1.0].
                spearman_corr = None
                k = len(intersection)
                if k >= 2:
                    # Filter items in intersection preserving order in list A and list B
                    common_in_a = [it["movieId"] for it in ordered_a if it["movieId"] in intersection]
                    common_in_b = [it["movieId"] for it in ordered_b if it["movieId"] in intersection]

                    rel_rank_a = {mid: idx + 1 for idx, mid in enumerate(common_in_a)}
                    rel_rank_b = {mid: idx + 1 for idx, mid in enumerate(common_in_b)}

                    diff_sq_sum = sum((rel_rank_a[mid] - rel_rank_b[mid]) ** 2 for mid in intersection)
                    raw_spearman = 1.0 - (6.0 * diff_sq_sum) / float(k * (k ** 2 - 1))
                    spearman_corr = max(-1.0, min(1.0, raw_spearman))

                pairwise_overlaps.append({
                    "model_a": m_a,
                    "model_b": m_b,
                    "jaccard_similarity": round(jaccard, 4),
                    "rank_correlation_spearman": round(spearman_corr, 4) if spearman_corr is not None else None,
                    "common_movies_count": len(intersection),
                })

        # Save session to SQLite if available
        session_id = f"lab_exp_{user_id}_{int(time.time() * 1000)}_{uuid.uuid4().hex[:6]}"
        try:
            self.sqlite_repo.log_experiment_session(
                session_id=session_id,
                user_id=str(user_id),
                model_a=models[0] if models else "none",
                model_b=models[1] if len(models) > 1 else "none",
                params={"top_n": top_n, "rrf_k": rrf_k, "w_als": weight_als, "w_kg": weight_kg},
                metrics={"overlap_pairs": len(pairwise_overlaps)},
            )
        except Exception as e:
            logger.warning(f"Failed to log experiment session: {e}")

        return {
            "session_id": session_id,
            "user_id": user_id,
            "top_n": top_n,
            "results": results,
            "pairwise_overlaps": pairwise_overlaps,
            "summary": {
                "models_evaluated": len(models),
                "total_comparisons": len(pairwise_overlaps),
            },
        }


_global_lab_service: Optional[LabService] = None


def get_lab_service(
    hybrid_engine: Optional[Any] = None,
    metrics_repo: Optional[ResearchMetricsRepository] = None,
    catalog_repo: Optional[MovieCatalogRepository] = None,
    sqlite_repo: Optional[SQLiteStateRepository] = None,
) -> LabService:
    """Singleton getter for LabService."""
    global _global_lab_service
    if _global_lab_service is None or hybrid_engine is not None:
        _global_lab_service = LabService(hybrid_engine, metrics_repo, catalog_repo, sqlite_repo)
    return _global_lab_service
