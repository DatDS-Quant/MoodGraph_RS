"""
MoodGraph - Task 3A: Evaluation Engine for Top-N Recommender Systems
Module: M02 - Top-N Evaluation Engine

Provides mathematically rigorous, reproducible offline evaluation for Top-N recommendation
under the User-wise Leave-1-Last protocol (MovieLens 25M).

Supported Metrics:
- HitRate@K (HR@K)
- NDCG@K
- MRR@K
- Precision@K
- Recall@K
- Catalog Coverage@K (Full-Catalog and Scorable-Catalog)

Primary Protocol:
- Target is considered positive if rating >= relevance_threshold (default: 3.5).
- Evaluated strictly on Positive-Target Cohort.
- Users with non-positive targets (rating < 3.5) are excluded from the positive cohort denominator
  and tracked in non-positive diagnostics.
- Missing predictions or unranked items are evaluated as 0.0 (miss), never silently dropped.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)


@dataclass(frozen=True)
class HeldOutTarget:
    """Represents a single held-out target interaction for a user."""
    movie_id: int
    rating: float
    timestamp: Optional[int] = None


@dataclass(frozen=True)
class SingleUserMetricResult:
    """Individual evaluation result for one user at a specific K cutoff."""
    user_id: int
    k: int
    hit: float
    recall: float
    precision: float
    ndcg: float
    mrr: float
    rank: Optional[int]
    is_positive_target: bool


@dataclass
class EvaluationSummary:
    """Aggregated evaluation metrics for a specific K cutoff."""
    k: int
    hit_rate: float
    recall: float
    precision: float
    ndcg: float
    mrr: float
    catalog_coverage_full: Optional[float]
    catalog_coverage_scorable: Optional[float]
    num_unique_recommended_movies: int
    positive_cohort_size: int
    non_positive_cohort_size: int
    total_target_users: int
    users_with_recommendations: int
    users_missing_recommendations: int
    hit_count: int
    diagnostic_all_users: Optional[Dict[str, float]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert summary to dictionary for reporting and serialization."""
        return {
            "k": self.k,
            "hit_rate": self.hit_rate,
            "recall": self.recall,
            "precision": self.precision,
            "ndcg": self.ndcg,
            "mrr": self.mrr,
            "catalog_coverage_full": self.catalog_coverage_full,
            "catalog_coverage_scorable": self.catalog_coverage_scorable,
            "num_unique_recommended_movies": self.num_unique_recommended_movies,
            "positive_cohort_size": self.positive_cohort_size,
            "non_positive_cohort_size": self.non_positive_cohort_size,
            "total_target_users": self.total_target_users,
            "users_with_recommendations": self.users_with_recommendations,
            "users_missing_recommendations": self.users_missing_recommendations,
            "hit_count": self.hit_count,
            "diagnostic_all_users": self.diagnostic_all_users,
        }


def validate_k(k: int) -> None:
    """Ensure K is a strictly positive integer."""
    if not isinstance(k, int) or k <= 0:
        raise ValueError(f"Cutoff K must be a strictly positive integer, got: {k}")


def validate_raw_score(score: float, movie_id: int) -> None:
    """Ensure raw_score is a valid finite float."""
    if not isinstance(score, (int, float)):
        raise ValueError(f"Score for movie {movie_id} must be numeric, got: {type(score).__name__}")
    if math.isnan(score) or math.isinf(score):
        raise ValueError(f"Score for movie {movie_id} must be finite (got {score})")


def sort_and_rank_candidates(
    scored_items: Iterable[Tuple[int, float]],
    k: Optional[int] = None,
) -> List[int]:
    """
    Sort scored candidate items deterministically and return ranked movieIds.
    
    Tie-breaking rule:
    1. raw_score DESC
    2. movieId ASC (stable deterministic tie-break)
    
    Validates finite scores and detects duplicate movie IDs.
    """
    items_list = list(scored_items)
    seen_ids: Set[int] = set()
    for mid, score in items_list:
        validate_raw_score(score, mid)
        if mid in seen_ids:
            raise ValueError(f"Duplicate movieId detected in scored candidates: {mid}")
        seen_ids.add(mid)

    # Sort: raw_score descending (-score), movieId ascending (+mid)
    sorted_items = sorted(items_list, key=lambda x: (-x[1], x[0]))

    if k is not None:
        validate_k(k)
        sorted_items = sorted_items[:k]

    return [mid for mid, _ in sorted_items]


def compute_single_user_metrics(
    recommended_movie_ids: Sequence[int],
    target_movie_id: int,
    k: int,
) -> Dict[str, Union[float, Optional[int]]]:
    """
    Compute Top-N evaluation metrics for a single user with ONE target movie.
    
    Under the Leave-1-Last protocol:
    If target is found at rank j (1 <= j <= k):
        - HitRate@K = 1.0
        - Recall@K = 1.0 (1 observed target retrieved / 1 observed target total)
        - Precision@K = 1.0 / k (1 observed target retrieved / k recommended slots)
        - NDCG@K = 1.0 / log2(j + 1) (IDCG = 1.0, DCG = 1.0 / log2(j + 1))
        - MRR@K = 1.0 / j
        - rank = j
    If target is not found in Top-K (or recommended list is empty):
        - HitRate@K = 0.0
        - Recall@K = 0.0
        - Precision@K = 0.0
        - NDCG@K = 0.0
        - MRR@K = 0.0
        - rank = None
    """
    validate_k(k)

    # Validate no duplicate IDs in recommendations
    top_k = list(recommended_movie_ids[:k])
    seen: Set[int] = set()
    for mid in top_k:
        if mid in seen:
            raise ValueError(f"Duplicate movieId {mid} detected in recommendation list")
        seen.add(mid)

    # Search for target in top_k
    rank_found: Optional[int] = None
    for idx, mid in enumerate(top_k, start=1):
        if mid == target_movie_id:
            rank_found = idx
            break

    if rank_found is not None:
        hit = 1.0
        recall = 1.0
        precision = 1.0 / float(k)
        ndcg = 1.0 / math.log2(float(rank_found) + 1.0)
        mrr = 1.0 / float(rank_found)
    else:
        hit = 0.0
        recall = 0.0
        precision = 0.0
        ndcg = 0.0
        mrr = 0.0

    return {
        "hit": hit,
        "recall": recall,
        "precision": precision,
        "ndcg": ndcg,
        "mrr": mrr,
        "rank": rank_found,
    }


def filter_seen_items(
    recommendations: Sequence[int],
    seen_movie_ids: Set[int],
) -> List[int]:
    """
    Filter out previously seen items from candidate / recommendation list.
    Preserves original ranking order.
    """
    return [mid for mid in recommendations if mid not in seen_movie_ids]


def validate_candidate_pool(
    recommendations: Sequence[int],
    seen_movie_ids: Set[int],
    catalog_movie_ids: Optional[Set[int]] = None,
    strict: bool = True,
) -> Dict[str, Any]:
    """
    Audit candidate pool adherence:
    - Checks for leak of seen items.
    - Checks for items outside catalog.
    - Checks for duplicate IDs.
    
    If strict=True, raises ValueError on any violation.
    """
    seen_leaks = [mid for mid in recommendations if mid in seen_movie_ids]
    out_of_catalog: List[int] = []
    if catalog_movie_ids is not None:
        out_of_catalog = [mid for mid in recommendations if mid not in catalog_movie_ids]

    seen_ids: Set[int] = set()
    duplicates: List[int] = []
    for mid in recommendations:
        if mid in seen_ids:
            duplicates.append(mid)
        seen_ids.add(mid)

    has_violation = bool(seen_leaks or out_of_catalog or duplicates)
    report = {
        "is_valid": not has_violation,
        "seen_leaks": seen_leaks,
        "seen_leaks_count": len(seen_leaks),
        "out_of_catalog": out_of_catalog,
        "out_of_catalog_count": len(out_of_catalog),
        "duplicates": duplicates,
        "duplicates_count": len(duplicates),
    }

    if strict and has_violation:
        msg = f"Candidate pool validation failed: seen_leaks={len(seen_leaks)}, out_of_catalog={len(out_of_catalog)}, duplicates={len(duplicates)}"
        raise ValueError(msg)

    return report


class TopNEvaluator:
    """
    Evaluation Engine for Top-N Recommendations in MoodGraph.
    
    Core design principles:
    1. Protocol adherence: Primary metrics calculated on Positive-Target Cohort (rating >= relevance_threshold).
    2. Denominator preservation: Users with positive targets but missing/empty recommendations are scored 0.0
       and strictly retained in the denominator.
    3. Non-positive diagnostic: Users with target rating < threshold are excluded from the positive cohort
       and counted in non_positive_cohort_size.
    4. Multi-K support: Evaluates across multiple K cutoffs (e.g., K = 5, 10, 20).
    5. Catalog coverage: Reports coverage over full catalog and optionally model-scorable catalog.
    """

    def __init__(
        self,
        k_list: Sequence[int] = (5, 10, 20),
        relevance_threshold: float = 3.5,
        catalog_size: Optional[int] = None,
        scorable_catalog_size: Optional[int] = None,
    ):
        for k in k_list:
            validate_k(k)
        self.k_list = sorted(list(k_list))
        self.relevance_threshold = float(relevance_threshold)
        self.catalog_size = catalog_size
        self.scorable_catalog_size = scorable_catalog_size

    def evaluate(
        self,
        recommendations: Dict[int, Sequence[int]],
        targets: Dict[int, Union[HeldOutTarget, Tuple[int, float], Dict[str, Any]]],
    ) -> Dict[int, EvaluationSummary]:
        """
        Evaluate recommendations against held-out targets.
        
        Args:
            recommendations: Mapping of userId -> ordered sequence of recommended movieIds.
            targets: Mapping of userId -> target info (HeldOutTarget, (movieId, rating), or dict).
        
        Returns:
            Mapping of k -> EvaluationSummary.
        """
        # Normalize targets to HeldOutTarget
        norm_targets: Dict[int, HeldOutTarget] = {}
        for uid, t in targets.items():
            if isinstance(t, HeldOutTarget):
                norm_targets[uid] = t
            elif isinstance(t, (tuple, list)) and len(t) >= 2:
                norm_targets[uid] = HeldOutTarget(movie_id=int(t[0]), rating=float(t[1]))
            elif isinstance(t, dict):
                norm_targets[uid] = HeldOutTarget(
                    movie_id=int(t["movieId"] if "movieId" in t else t["movie_id"]),
                    rating=float(t["rating"]),
                    timestamp=int(t["timestamp"]) if "timestamp" in t else None,
                )
            else:
                raise ValueError(f"Unsupported target format for user {uid}: {t}")

        total_target_users = len(norm_targets)
        positive_users: Dict[int, HeldOutTarget] = {}
        non_positive_users: Dict[int, HeldOutTarget] = {}

        for uid, target in norm_targets.items():
            if target.rating >= self.relevance_threshold:
                positive_users[uid] = target
            else:
                non_positive_users[uid] = target

        pos_cohort_size = len(positive_users)
        non_pos_cohort_size = len(non_positive_users)

        results: Dict[int, EvaluationSummary] = {}

        for k in self.k_list:
            sum_hit = 0.0
            sum_recall = 0.0
            sum_precision = 0.0
            sum_ndcg = 0.0
            sum_mrr = 0.0
            hit_count = 0

            users_with_rec = 0
            users_missing_rec = 0
            unique_recommended_movies: Set[int] = set()

            # Evaluate positive cohort (Primary Evaluation)
            for uid, target in positive_users.items():
                user_rec = recommendations.get(uid, [])
                if len(user_rec) > 0:
                    users_with_rec += 1
                    top_k_items = list(user_rec[:k])
                    unique_recommended_movies.update(top_k_items)
                    m = compute_single_user_metrics(top_k_items, target.movie_id, k)
                else:
                    users_missing_rec += 1
                    m = compute_single_user_metrics([], target.movie_id, k)

                hit = float(m["hit"])
                sum_hit += hit
                sum_recall += float(m["recall"])
                sum_precision += float(m["precision"])
                sum_ndcg += float(m["ndcg"])
                sum_mrr += float(m["mrr"])
                if hit > 0:
                    hit_count += 1

            if pos_cohort_size > 0:
                avg_hit_rate = sum_hit / float(pos_cohort_size)
                avg_recall = sum_recall / float(pos_cohort_size)
                avg_precision = sum_precision / float(pos_cohort_size)
                avg_ndcg = sum_ndcg / float(pos_cohort_size)
                avg_mrr = sum_mrr / float(pos_cohort_size)
            else:
                avg_hit_rate = 0.0
                avg_recall = 0.0
                avg_precision = 0.0
                avg_ndcg = 0.0
                avg_mrr = 0.0

            # Catalog coverage
            num_unique_rec = len(unique_recommended_movies)
            cov_full = (
                num_unique_rec / float(self.catalog_size)
                if self.catalog_size is not None and self.catalog_size > 0
                else None
            )
            cov_scorable = (
                num_unique_rec / float(self.scorable_catalog_size)
                if self.scorable_catalog_size is not None and self.scorable_catalog_size > 0
                else None
            )

            # Diagnostic for all users (if requested)
            diagnostic_all: Optional[Dict[str, float]] = None
            if total_target_users > 0:
                # Under all-users diagnostic, non-positive users get hit=0.0
                diag_hr = sum_hit / float(total_target_users)
                diagnostic_all = {
                    "all_users_hit_rate": diag_hr,
                    "all_users_total_count": total_target_users,
                    "note": "Recall and NDCG are mathematically undefined for users without positive observed targets.",
                }

            results[k] = EvaluationSummary(
                k=k,
                hit_rate=avg_hit_rate,
                recall=avg_recall,
                precision=avg_precision,
                ndcg=avg_ndcg,
                mrr=avg_mrr,
                catalog_coverage_full=cov_full,
                catalog_coverage_scorable=cov_scorable,
                num_unique_recommended_movies=num_unique_rec,
                positive_cohort_size=pos_cohort_size,
                non_positive_cohort_size=non_pos_cohort_size,
                total_target_users=total_target_users,
                users_with_recommendations=users_with_rec,
                users_missing_recommendations=users_missing_rec,
                hit_count=hit_count,
                diagnostic_all_users=diagnostic_all,
            )

        return results
