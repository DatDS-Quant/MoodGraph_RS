"""
MoodGraph - Task 3A: Spark ALS
Module M01: Data & Input Audit Engine

This module executes rigorous data validation, sparsity analysis,
long-tail popularity binning, and cold-start diagnostics for ALS.
Optimized with single-pass distributed aggregations.
"""

import time
from pathlib import Path
from typing import Any, Dict, Optional

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from .data_loader import load_als_datasets


def validate_train_input_constraints(
    train_df: DataFrame,
    movies_df: DataFrame,
) -> Dict[str, Any]:
    """
    Validate ALS input constraints on Train split:
    - Non-null and positive IDs
    - Rating bounds [0.5, 5.0] with step 0.5
    - Non-null timestamps
    - Zero duplicate (userId, movieId) pairs
    - Referential integrity: all train movieIds must exist in movies catalog
    - No artificial zero-ratings
    Uses single-pass aggregation for maximum efficiency.
    """
    # 1. Single-pass aggregation for all row-level constraint checks
    agg_row = train_df.select(
        F.count(F.lit(1)).alias("total_train_rows"),
        F.count(F.when(F.col("userId").isNull() | (F.col("userId") <= 0), 1)).alias("null_userId_count"),
        F.count(F.when(F.col("movieId").isNull() | (F.col("movieId") <= 0), 1)).alias("null_movieId_count"),
        F.count(F.when(F.col("rating").isNull(), 1)).alias("null_rating_count"),
        F.count(F.when(F.col("timestamp").isNull() | (F.col("timestamp") <= 0), 1)).alias("null_timestamp_count"),
        F.count(F.when((F.col("rating") < 0.5) | (F.col("rating") > 5.0), 1)).alias("range_violation_count"),
        F.count(F.when(F.col("rating") == 0.0, 1)).alias("zero_rating_count"),
        F.count(F.when((F.col("rating") * 2.0) != F.floor(F.col("rating") * 2.0), 1)).alias("step_violation_count"),
    ).first()

    total_rows = agg_row["total_train_rows"] if agg_row else 0
    null_user_cnt = agg_row["null_userId_count"] if agg_row else 0
    null_movie_cnt = agg_row["null_movieId_count"] if agg_row else 0
    null_rating_cnt = agg_row["null_rating_count"] if agg_row else 0
    null_ts_cnt = agg_row["null_timestamp_count"] if agg_row else 0
    range_violation_cnt = agg_row["range_violation_count"] if agg_row else 0
    zero_rating_cnt = agg_row["zero_rating_count"] if agg_row else 0
    step_violation_cnt = agg_row["step_violation_count"] if agg_row else 0

    # 2. Duplicate (userId, movieId) check
    if total_rows > 0:
        distinct_pairs = train_df.select("userId", "movieId").distinct().count()
        duplicate_pair_cnt = total_rows - distinct_pairs
    else:
        duplicate_pair_cnt = 0

    # 3. Referential integrity: train movieId in catalog movies
    if total_rows > 0:
        train_movie_ids = train_df.select("movieId").distinct()
        catalog_movie_ids = movies_df.select("movieId").distinct()
        dangling_movies_cnt = train_movie_ids.join(
            catalog_movie_ids, on="movieId", how="left_anti"
        ).count()
    else:
        dangling_movies_cnt = 0

    passed = (
        null_user_cnt == 0
        and null_movie_cnt == 0
        and null_rating_cnt == 0
        and null_ts_cnt == 0
        and range_violation_cnt == 0
        and zero_rating_cnt == 0
        and step_violation_cnt == 0
        and duplicate_pair_cnt == 0
        and dangling_movies_cnt == 0
    )

    return {
        "passed": passed,
        "total_train_rows": total_rows,
        "null_userId_count": null_user_cnt,
        "null_movieId_count": null_movie_cnt,
        "null_rating_count": null_rating_cnt,
        "null_timestamp_count": null_ts_cnt,
        "range_violation_count": range_violation_cnt,
        "zero_rating_count": zero_rating_cnt,
        "step_violation_count": step_violation_cnt,
        "duplicate_pair_count": duplicate_pair_cnt,
        "dangling_movies_count": dangling_movies_cnt,
    }


def audit_als_input_distribution(
    train_df: DataFrame,
    movies_df: DataFrame,
) -> Dict[str, Any]:
    """
    Compute ALS input statistics on Train:
    - Distinct users & distinct train movies
    - Ratings per user: min, median (p50), p95, max
    - Ratings per movie: min, median (p50), p95, max
    - Long-tail popularity buckets: 1-5, 6-10, >10 ratings
    - Matrix density & sparsity for both Train-known and Full-Catalog universes
    """
    total_ratings = train_df.count()
    distinct_users = train_df.select("userId").distinct().count()
    distinct_train_movies = train_df.select("movieId").distinct().count()
    catalog_movie_count = movies_df.select("movieId").distinct().count()

    if total_ratings > 0:
        # User activity distribution
        user_counts_df = train_df.groupBy("userId").agg(F.count("movieId").alias("user_ratings"))
        user_stats = user_counts_df.select(
            F.min("user_ratings").alias("min_val"),
            F.max("user_ratings").alias("max_val"),
        ).first()
        user_quantiles = user_counts_df.approxQuantile("user_ratings", [0.50, 0.95], 0.001)

        user_distribution = {
            "min": int(user_stats["min_val"]) if user_stats else 0,
            "median": float(user_quantiles[0]) if user_quantiles else 0.0,
            "p95": float(user_quantiles[1]) if user_quantiles else 0.0,
            "max": int(user_stats["max_val"]) if user_stats else 0,
        }

        # Movie popularity distribution
        movie_counts_df = train_df.groupBy("movieId").agg(F.count("userId").alias("movie_ratings"))
        movie_stats = movie_counts_df.select(
            F.min("movie_ratings").alias("min_val"),
            F.max("movie_ratings").alias("max_val"),
        ).first()
        movie_quantiles = movie_counts_df.approxQuantile("movie_ratings", [0.50, 0.95], 0.001)

        movie_distribution = {
            "min": int(movie_stats["min_val"]) if movie_stats else 0,
            "median": float(movie_quantiles[0]) if movie_quantiles else 0.0,
            "p95": float(movie_quantiles[1]) if movie_quantiles else 0.0,
            "max": int(movie_stats["max_val"]) if movie_stats else 0,
        }

        # Long-tail popularity buckets among train-known movies in a single pass
        bucket_row = movie_counts_df.select(
            F.count(F.when(F.col("movie_ratings").between(1, 5), 1)).alias("b_1_5"),
            F.count(F.when(F.col("movie_ratings").between(6, 10), 1)).alias("b_6_10"),
            F.count(F.when(F.col("movie_ratings") > 10, 1)).alias("b_gt_10"),
        ).first()

        movies_1_to_5 = bucket_row["b_1_5"] if bucket_row else 0
        movies_6_to_10 = bucket_row["b_6_10"] if bucket_row else 0
        movies_gt_10 = bucket_row["b_gt_10"] if bucket_row else 0
    else:
        user_distribution = {"min": 0, "median": 0.0, "p95": 0.0, "max": 0}
        movie_distribution = {"min": 0, "median": 0.0, "p95": 0.0, "max": 0}
        movies_1_to_5 = 0
        movies_6_to_10 = 0
        movies_gt_10 = 0

    # Movies with 0 train ratings
    catalog_zero_train_ratings = catalog_movie_count - distinct_train_movies

    # Density & Sparsity calculations
    # 1. Train-known movie universe
    known_cells = float(distinct_users) * float(distinct_train_movies)
    density_known = float(total_ratings) / known_cells if known_cells > 0 else 0.0
    sparsity_known = 1.0 - density_known

    # 2. Full catalog universe
    catalog_cells = float(distinct_users) * float(catalog_movie_count)
    density_catalog = float(total_ratings) / catalog_cells if catalog_cells > 0 else 0.0
    sparsity_catalog = 1.0 - density_catalog

    return {
        "total_ratings": total_ratings,
        "distinct_users": distinct_users,
        "distinct_train_movies": distinct_train_movies,
        "catalog_movie_count": catalog_movie_count,
        "catalog_zero_train_ratings": catalog_zero_train_ratings,
        "user_ratings_distribution": user_distribution,
        "movie_ratings_distribution": movie_distribution,
        "movie_popularity_buckets": {
            "ratings_1_to_5": movies_1_to_5,
            "ratings_6_to_10": movies_6_to_10,
            "ratings_gt_10": movies_gt_10,
            "zero_train_ratings": catalog_zero_train_ratings,
        },
        "train_known_universe": {
            "num_users": distinct_users,
            "num_movies": distinct_train_movies,
            "total_cells": known_cells,
            "density": density_known,
            "density_percent": density_known * 100.0,
            "sparsity": sparsity_known,
            "sparsity_percent": sparsity_known * 100.0,
        },
        "full_catalog_universe": {
            "num_users": distinct_users,
            "num_movies": catalog_movie_count,
            "total_cells": catalog_cells,
            "density": density_catalog,
            "density_percent": density_catalog * 100.0,
            "sparsity": sparsity_catalog,
            "sparsity_percent": sparsity_catalog * 100.0,
        },
    }


def audit_movie_cold_start(
    train_df: DataFrame,
    val_df: DataFrame,
    movies_df: DataFrame,
) -> Dict[str, Any]:
    """
    Audit Movie Cold-Start and Validation Target Coverage:
    - Train-known vs Train-unseen catalog movies
    - Validation targets scorable by ALS (item factor exists in Train)
    - Positive Validation targets scorable by ALS (rating >= 3.5)
    """
    catalog_count = movies_df.select("movieId").distinct().count()
    train_movie_ids = train_df.select("movieId").distinct()
    train_known_count = train_movie_ids.count()

    train_unseen_count = catalog_count - train_known_count
    unseen_ratio = (float(train_unseen_count) / float(catalog_count)) * 100.0 if catalog_count > 0 else 0.0

    # Count movies with exactly 1 rating in train
    if train_df.count() > 0:
        single_rating_movies_count = (
            train_df.groupBy("movieId")
            .agg(F.count("userId").alias("cnt"))
            .filter(F.col("cnt") == 1)
            .count()
        )
    else:
        single_rating_movies_count = 0

    # 1. Overall Validation Coverage
    val_total = val_df.count()
    val_scoreable = val_df.join(train_movie_ids, on="movieId", how="left_semi").count() if val_total > 0 else 0
    val_unscorable = val_total - val_scoreable
    val_coverage_rate = (float(val_scoreable) / float(val_total)) * 100.0 if val_total > 0 else 0.0

    # 2. Positive-Target Validation Cohort (rating >= 3.5)
    val_pos_df = val_df.filter(F.col("rating") >= 3.5)
    val_pos_total = val_pos_df.count()
    val_pos_scoreable = (
        val_pos_df.join(train_movie_ids, on="movieId", how="left_semi").count()
        if val_pos_total > 0
        else 0
    )
    val_pos_unscorable = val_pos_total - val_pos_scoreable
    val_pos_coverage_rate = (
        (float(val_pos_scoreable) / float(val_pos_total)) * 100.0 if val_pos_total > 0 else 0.0
    )

    return {
        "catalog_movie_count": catalog_count,
        "train_known_movie_count": train_known_count,
        "train_unseen_movie_count": train_unseen_count,
        "train_unseen_percentage": unseen_ratio,
        "single_rating_movies_count": single_rating_movies_count,
        "validation_all_targets": {
            "total": val_total,
            "scoreable_by_als": val_scoreable,
            "unscorable_by_als": val_unscorable,
            "coverage_percentage": val_coverage_rate,
        },
        "validation_positive_targets": {
            "threshold": "rating >= 3.5",
            "total": val_pos_total,
            "scoreable_by_als": val_pos_scoreable,
            "unscorable_by_als": val_pos_unscorable,
            "coverage_percentage": val_pos_coverage_rate,
        },
    }


def run_full_m01_audit(
    spark: SparkSession,
    base_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Execute complete end-to-end M01 audit on real data.
    Measures duration and returns all audit sections.
    """
    t_start = time.time()
    train_df, val_df, movies_df = load_als_datasets(spark, base_dir)

    constraints_result = validate_train_input_constraints(train_df, movies_df)
    distribution_result = audit_als_input_distribution(train_df, movies_df)
    cold_start_result = audit_movie_cold_start(train_df, val_df, movies_df)
    duration_seconds = time.time() - t_start

    return {
        "status": "PASS" if constraints_result["passed"] else "FAIL",
        "duration_seconds": duration_seconds,
        "constraints": constraints_result,
        "distribution": distribution_result,
        "cold_start": cold_start_result,
    }
