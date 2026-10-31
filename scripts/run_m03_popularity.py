"""
MoodGraph Task 3A - Stage 7: Real Parquet Experiment Runner for Module M03
Evaluates Rating Count Baseline vs Bayesian Weighted Average Baseline
on MovieLens 25M Validation split (162,541 total users, 109,779 positive cohort)
using Module M02 TopNEvaluator.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Windows Hadoop & PySpark configuration
os.environ["HADOOP_HOME"] = r"C:\hadoop"
os.environ["PATH"] = r"C:\hadoop\bin;" + os.environ.get("PATH", "")
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

from pyspark.sql import SparkSession
import pyspark.sql.functions as F

from recommender.als.data_loader import (
    get_spark_session,
    load_train_data,
    load_validation_data,
    load_movies_data,
)
from recommender.als.evaluator import HeldOutTarget, TopNEvaluator
from recommender.als.popularity import PopularityRecommender


def main():
    root = root_dir
    artifacts_dir = root / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    out_results_json = artifacts_dir / "m03_popularity_results.json"
    out_rankings_json = artifacts_dir / "m03_popularity_rankings.json"

    print("=== MoodGraph Task 3A: Module M03 Popularity Real Experiment ===")
    spark = get_spark_session("MoodGraph_3A_M03_Popularity_Runner", driver_memory="6g")
    t_start = time.time()

    # 1. Load Data
    print("\n[Step 1/5] Loading Train, Validation, and Catalog Parquet...")
    train_df = load_train_data(spark)
    val_df = load_validation_data(spark)
    movies_df = load_movies_data(spark)

    total_train_rows = train_df.count()
    total_val_rows = val_df.count()
    catalog_size = movies_df.select("movieId").distinct().count()
    print(f"  Train ratings: {total_train_rows:,}")
    print(f"  Validation ratings: {total_val_rows:,}")
    print(f"  Catalog movies: {catalog_size:,}")

    # 2. Fit Popularity Models
    print("\n[Step 2/5] Fitting Popularity Recommenders (Count and Weighted Average)...")
    t0_fit = time.time()
    recommender = PopularityRecommender(m=10.0).fit_from_spark(train_df)
    t_fit = time.time() - t0_fit
    scorable_catalog_size = len(recommender.count_ranked_records)
    print(f"  Fit completed in {t_fit:.2f}s.")
    print(f"  Global mean rating C = {recommender.global_mean:.6f}")
    print(f"  Scored movies (Train-known): {scorable_catalog_size:,} / {catalog_size:,}")

    # 3. Extract Validation Targets
    print("\n[Step 3/5] Extracting Validation Targets...")
    val_rows = val_df.select("userId", "movieId", "rating").collect()
    targets: dict[int, HeldOutTarget] = {
        int(row["userId"]): HeldOutTarget(
            movie_id=int(row["movieId"]),
            rating=float(row["rating"]),
        )
        for row in val_rows
    }
    pos_targets_count = sum(1 for t in targets.values() if t.rating >= 3.5)
    non_pos_count = len(targets) - pos_targets_count
    print(f"  Total Validation users: {len(targets):,}")
    print(f"  Positive cohort users (rating >= 3.5): {pos_targets_count:,}")
    print(f"  Non-positive users (rating < 3.5): {non_pos_count:,}")

    # 4. Extract User Seen History from Train
    print("\n[Step 4/5] Extracting User Train History (Seen Items) for All Users...")
    t0_hist = time.time()
    user_history_df = train_df.groupBy("userId").agg(F.collect_list("movieId").alias("seen"))
    hist_rows = user_history_df.collect()
    user_histories: dict[int, set[int]] = {
        int(row["userId"]): set(row["seen"])
        for row in hist_rows
    }
    t_hist = time.time() - t0_hist
    print(f"  Extracted histories for {len(user_histories):,} users in {t_hist:.2f}s.")

    # 5. Generate Top-K and Evaluate with M02 Evaluator
    print("\n[Step 5/5] Evaluating Top-N (K=5, 10, 20) with M02 Evaluator...")
    evaluator = TopNEvaluator(
        k_list=[5, 10, 20],
        relevance_threshold=3.5,
        catalog_size=catalog_size,
        scorable_catalog_size=scorable_catalog_size,
    )

    experiment_results = {
        "metadata": {
            "total_train_ratings": total_train_rows,
            "total_val_targets": len(targets),
            "positive_cohort_size": pos_targets_count,
            "non_positive_cohort_size": non_pos_count,
            "catalog_size": catalog_size,
            "scorable_catalog_size": scorable_catalog_size,
            "global_train_mean": recommender.global_mean,
            "weighted_prior_m": recommender.m,
        },
        "variants": {},
    }

    # Evaluate Variant A: POPULARITY_COUNT
    print("\n--- Evaluating Variant A: POPULARITY_COUNT ---")
    t0_cnt = time.time()
    recs_count = recommender.recommend_for_users(
        user_histories=user_histories,
        k=20,
        variant="count",
        target_user_ids=targets.keys(),
    )
    t_gen_cnt = time.time() - t0_cnt
    summary_count = evaluator.evaluate(recs_count, targets)
    t_eval_cnt = time.time() - t0_cnt
    print(f"  Generation + Evaluation completed in {t_eval_cnt:.2f}s (gen: {t_gen_cnt:.2f}s).")

    experiment_results["variants"]["POPULARITY_COUNT"] = {
        "timing_seconds": t_eval_cnt,
        "metrics": {k: s.to_dict() for k, s in summary_count.items()},
    }

    for k in [5, 10, 20]:
        s = summary_count[k]
        print(f"  K={k:2d}: HR={s.hit_rate:.4f}, NDCG={s.ndcg:.4f}, MRR={s.mrr:.4f}, P={s.precision:.4f}, Rec={s.recall:.4f}, CovFull={s.catalog_coverage_full * 100:.2f}%, CovScorable={s.catalog_coverage_scorable * 100:.2f}%")

    # Evaluate Variant B: POPULARITY_WEIGHTED
    print("\n--- Evaluating Variant B: POPULARITY_WEIGHTED (m=10.0) ---")
    t0_wt = time.time()
    recs_weighted = recommender.recommend_for_users(
        user_histories=user_histories,
        k=20,
        variant="weighted",
        target_user_ids=targets.keys(),
    )
    t_gen_wt = time.time() - t0_wt
    summary_weighted = evaluator.evaluate(recs_weighted, targets)
    t_eval_wt = time.time() - t0_wt
    print(f"  Generation + Evaluation completed in {t_eval_wt:.2f}s (gen: {t_gen_wt:.2f}s).")

    experiment_results["variants"]["POPULARITY_WEIGHTED"] = {
        "timing_seconds": t_eval_wt,
        "metrics": {k: s.to_dict() for k, s in summary_weighted.items()},
    }

    for k in [5, 10, 20]:
        s = summary_weighted[k]
        print(f"  K={k:2d}: HR={s.hit_rate:.4f}, NDCG={s.ndcg:.4f}, MRR={s.mrr:.4f}, P={s.precision:.4f}, Rec={s.recall:.4f}, CovFull={s.catalog_coverage_full * 100:.2f}%, CovScorable={s.catalog_coverage_scorable * 100:.2f}%")

    # Total elapsed time
    total_elapsed = time.time() - t_start
    experiment_results["total_pipeline_duration_seconds"] = total_elapsed
    print(f"\n=== Entire Experiment Completed in {total_elapsed:.2f}s ===")

    # Save artifacts
    with open(out_results_json, "w", encoding="utf-8") as f:
        json.dump(experiment_results, f, indent=2)

    rankings_payload = {
        "top_50_count": recommender.export_ranking_table(variant="count", top_n=50),
        "top_50_weighted": recommender.export_ranking_table(variant="weighted", top_n=50),
    }
    with open(out_rankings_json, "w", encoding="utf-8") as f:
        json.dump(rankings_payload, f, indent=2)

    print(f"Saved results to: {out_results_json}")
    print(f"Saved rankings to: {out_rankings_json}")

    spark.stop()


if __name__ == "__main__":
    main()
