"""
MoodGraph - Task 3A: Spark ALS & Baselines
Module M03: Global Popularity Baseline Recommender

Implements non-personalized popularity baseline recommenders:
1. Rating Count Baseline (POPULARITY_COUNT):
   Ranks movies by total rating count in Train DESC, tie-breaking by avg rating DESC, movieId ASC.
2. Bayesian / Weighted Average Baseline (POPULARITY_WEIGHTED):
   Ranks movies using the Dirichlet/Bayesian prior formula:
       WeightedScore = (v * R + m * C) / (v + m)
   where:
       v: Number of ratings of movie in Train (rating_count)
       R: Average rating of movie in Train (avg_rating)
       C: Global average rating across all ratings in Train (global_mean)
       m: Smoothing parameter (prior pseudo-counts, default: 10.0)
   Tie-breaking: WeightedScore DESC, v DESC, movieId ASC.

Features:
- Pure Python mathematical core for deterministic, reproducible unit testing.
- PySpark distributed aggregation on big data (24.6M ratings).
- History-aware seen-item filtering ensuring exactly K unseen items for any user.
- Full compatibility with M02 TopNEvaluator and Task 3B output contract.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
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

from pyspark.sql import DataFrame
import pyspark.sql.functions as F


@dataclass(frozen=True)
class PopularityMovieRecord:
    """Represents a movie with its popularity metrics and ranking."""
    movie_id: int
    rating_count: int
    avg_rating: float
    weighted_score: float
    rank: int


@dataclass(frozen=True)
class PopularityRecommendation:
    """Represents a single recommendation entry for a user."""
    user_id: int
    movie_id: int
    rank: int
    raw_score: float
    model_name: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "userId": self.user_id,
            "movieId": self.movie_id,
            "rank": self.rank,
            "raw_score": self.raw_score,
            "model_name": self.model_name,
        }


def compute_weighted_score(v: int, r: float, c: float, m: float) -> float:
    """
    Compute Bayesian Weighted Average rating (IMDB / Dirichlet prior formula):
        WeightedScore = (v * R + m * C) / (v + m)
    
    Args:
        v: Movie rating count in Train (>= 0).
        r: Movie average rating in Train.
        c: Global average rating across all ratings in Train.
        m: Prior weight / smoothing parameter (>= 0).
    
    Returns:
        Weighted score as a finite float.
    """
    if v < 0:
        raise ValueError(f"Rating count v must be non-negative, got {v}")
    if m < 0:
        raise ValueError(f"Smoothing parameter m must be non-negative, got {m}")
    if math.isnan(r) or math.isinf(r):
        raise ValueError(f"Movie average rating r must be finite, got {r}")
    if math.isnan(c) or math.isinf(c):
        raise ValueError(f"Global mean c must be finite, got {c}")

    denominator = float(v + m)
    if denominator == 0.0:
        # Edge case: movie has 0 ratings and prior weight is 0
        return float(c)

    score = (float(v) * float(r) + float(m) * float(c)) / denominator
    return score


def rank_movies_by_count(
    movie_stats: Sequence[Tuple[int, int, float]],
) -> List[PopularityMovieRecord]:
    """
    Sort movies deterministically by Rating Count.
    
    Tie-breaking rule:
    1. rating_count DESC (primary)
    2. avg_rating DESC (secondary)
    3. movieId ASC (deterministic tie-break)
    """
    # Sort key: (-rating_count, -avg_rating, movieId)
    sorted_stats = sorted(
        movie_stats,
        key=lambda x: (-x[1], -x[2], x[0]),
    )

    ranked_records: List[PopularityMovieRecord] = []
    for rank_idx, (mid, count, avg_r) in enumerate(sorted_stats, start=1):
        record = PopularityMovieRecord(
            movie_id=mid,
            rating_count=count,
            avg_rating=avg_r,
            weighted_score=float(count),  # raw score is the count
            rank=rank_idx,
        )
        ranked_records.append(record)

    return ranked_records


def rank_movies_by_weighted_average(
    movie_stats: Sequence[Tuple[int, int, float]],
    global_mean: float,
    m: float = 10.0,
) -> List[PopularityMovieRecord]:
    """
    Sort movies deterministically by Bayesian Weighted Average.
    
    Tie-breaking rule:
    1. weighted_score DESC (primary)
    2. rating_count DESC (secondary)
    3. movieId ASC (deterministic tie-break)
    """
    scored_items: List[Tuple[int, int, float, float]] = []
    for mid, count, avg_r in movie_stats:
        ws = compute_weighted_score(v=count, r=avg_r, c=global_mean, m=m)
        scored_items.append((mid, count, avg_r, ws))

    # Sort key: (-weighted_score, -rating_count, movieId)
    sorted_stats = sorted(
        scored_items,
        key=lambda x: (-x[3], -x[1], x[0]),
    )

    ranked_records: List[PopularityMovieRecord] = []
    for rank_idx, (mid, count, avg_r, ws) in enumerate(sorted_stats, start=1):
        record = PopularityMovieRecord(
            movie_id=mid,
            rating_count=count,
            avg_rating=avg_r,
            weighted_score=ws,
            rank=rank_idx,
        )
        ranked_records.append(record)

    return ranked_records


def generate_user_top_k(
    user_id: int,
    ranked_movie_ids: Sequence[int],
    scores_map: Dict[int, float],
    seen_movies: Set[int],
    k: int = 10,
    model_name: str = "POPULARITY",
) -> List[PopularityRecommendation]:
    """
    Generate Top-K recommendations for a single user by filtering seen items.
    
    Scans the globally ranked movie list and skips movies in seen_movies until
    exactly K unseen movies are collected (or candidate pool is exhausted).
    """
    if k <= 0:
        raise ValueError(f"Cutoff k must be strictly positive, got: {k}")

    recs: List[PopularityRecommendation] = []
    rank_counter = 1

    for mid in ranked_movie_ids:
        if mid not in seen_movies:
            score = scores_map.get(mid, 0.0)
            rec = PopularityRecommendation(
                user_id=user_id,
                movie_id=mid,
                rank=rank_counter,
                raw_score=score,
                model_name=model_name,
            )
            recs.append(rec)
            rank_counter += 1
            if len(recs) == k:
                break

    return recs


def generate_batch_top_k(
    user_histories: Dict[int, Set[int]],
    ranked_movie_ids: Sequence[int],
    scores_map: Dict[int, float],
    k: int = 10,
    model_name: str = "POPULARITY",
    target_user_ids: Optional[Iterable[int]] = None,
) -> Dict[int, List[int]]:
    """
    Generate Top-K recommendations for a collection of users.
    Returns mapping of userId -> List of recommended movieIds (ordered by rank).
    """
    eval_uids = target_user_ids if target_user_ids is not None else user_histories.keys()
    results: Dict[int, List[int]] = {}

    for uid in eval_uids:
        seen = user_histories.get(uid, set())
        recs = generate_user_top_k(
            user_id=uid,
            ranked_movie_ids=ranked_movie_ids,
            scores_map=scores_map,
            seen_movies=seen,
            k=k,
            model_name=model_name,
        )
        results[uid] = [r.movie_id for r in recs]

    return results


class PopularityRecommender:
    """
    Full Popularity Recommender supporting both Count and Weighted Average baselines.
    """

    def __init__(self, m: float = 10.0):
        self.m = float(m)
        self.global_mean: float = 0.0
        self.count_ranked_records: List[PopularityMovieRecord] = []
        self.weighted_ranked_records: List[PopularityMovieRecord] = []
        self._count_ranked_ids: List[int] = []
        self._weighted_ranked_ids: List[int] = []
        self._count_scores_map: Dict[int, float] = {}
        self._weighted_scores_map: Dict[int, float] = {}
        self.is_fitted: bool = False

    def fit_from_stats(
        self,
        movie_stats: Sequence[Tuple[int, int, float]],
        global_mean: float,
        m: Optional[float] = None,
    ) -> PopularityRecommender:
        """
        Fit popularity models from pre-aggregated movie statistics.
        Useful for unit testing and lightweight deployment.
        """
        if m is not None:
            self.m = float(m)
        self.global_mean = float(global_mean)

        self.count_ranked_records = rank_movies_by_count(movie_stats)
        self.weighted_ranked_records = rank_movies_by_weighted_average(
            movie_stats, self.global_mean, self.m
        )

        self._count_ranked_ids = [r.movie_id for r in self.count_ranked_records]
        self._weighted_ranked_ids = [r.movie_id for r in self.weighted_ranked_records]

        self._count_scores_map = {r.movie_id: float(r.rating_count) for r in self.count_ranked_records}
        self._weighted_scores_map = {r.movie_id: r.weighted_score for r in self.weighted_ranked_records}

        self.is_fitted = True
        return self

    def fit_from_spark(
        self,
        train_df: DataFrame,
        m: Optional[float] = None,
    ) -> PopularityRecommender:
        """
        Fit popularity models directly from PySpark Train DataFrame.
        Aggregates rating count and average rating per movieId.
        """
        if m is not None:
            self.m = float(m)

        # 1. Compute global mean rating
        global_mean_val = (
            train_df.select(F.avg("rating").alias("mean_r")).first()["mean_r"]
        )
        self.global_mean = float(global_mean_val)

        # 2. Compute movie-level counts and averages
        movie_agg_df = train_df.groupBy("movieId").agg(
            F.count("userId").alias("rating_count"),
            F.avg("rating").alias("avg_rating"),
        )

        # Collect compact table (58,932 rows, ~2-3 MB)
        rows = movie_agg_df.collect()
        movie_stats = [
            (int(row["movieId"]), int(row["rating_count"]), float(row["avg_rating"]))
            for row in rows
        ]

        return self.fit_from_stats(movie_stats, self.global_mean, self.m)

    def recommend(
        self,
        user_id: int,
        seen_movies: Set[int],
        k: int = 10,
        variant: str = "count",
    ) -> List[PopularityRecommendation]:
        """
        Generate Top-K recommendations for a single user.
        variant: 'count' or 'weighted'.
        """
        if not self.is_fitted:
            raise RuntimeError("Model has not been fitted. Call fit_from_stats or fit_from_spark first.")

        var_lower = variant.lower()
        if var_lower == "count":
            ranked_ids = self._count_ranked_ids
            scores_map = self._count_scores_map
            model_name = "POPULARITY_COUNT"
        elif var_lower in ("weighted", "bayesian"):
            ranked_ids = self._weighted_ranked_ids
            scores_map = self._weighted_scores_map
            model_name = "POPULARITY_WEIGHTED"
        else:
            raise ValueError(f"Unknown popularity variant: {variant}. Expected 'count' or 'weighted'.")

        return generate_user_top_k(
            user_id=user_id,
            ranked_movie_ids=ranked_ids,
            scores_map=scores_map,
            seen_movies=seen_movies,
            k=k,
            model_name=model_name,
        )

    def recommend_for_users(
        self,
        user_histories: Dict[int, Set[int]],
        k: int = 10,
        variant: str = "count",
        target_user_ids: Optional[Iterable[int]] = None,
    ) -> Dict[int, List[int]]:
        """
        Generate Top-K recommendation dictionary for multiple users.
        """
        if not self.is_fitted:
            raise RuntimeError("Model has not been fitted.")

        var_lower = variant.lower()
        if var_lower == "count":
            ranked_ids = self._count_ranked_ids
            scores_map = self._count_scores_map
            model_name = "POPULARITY_COUNT"
        elif var_lower in ("weighted", "bayesian"):
            ranked_ids = self._weighted_ranked_ids
            scores_map = self._weighted_scores_map
            model_name = "POPULARITY_WEIGHTED"
        else:
            raise ValueError(f"Unknown popularity variant: {variant}")

        return generate_batch_top_k(
            user_histories=user_histories,
            ranked_movie_ids=ranked_ids,
            scores_map=scores_map,
            k=k,
            model_name=model_name,
            target_user_ids=target_user_ids,
        )

    def export_ranking_table(self, variant: str = "count", top_n: Optional[int] = None) -> List[Dict[str, Any]]:
        """Export ranked movie table as list of dicts."""
        if not self.is_fitted:
            raise RuntimeError("Model has not been fitted.")

        var_lower = variant.lower()
        if var_lower == "count":
            records = self.count_ranked_records
        else:
            records = self.weighted_ranked_records

        if top_n is not None:
            records = records[:top_n]

        return [asdict(r) for r in records]
