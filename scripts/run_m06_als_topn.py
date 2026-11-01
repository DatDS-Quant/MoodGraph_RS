"""
MoodGraph - Task 3A: Full Experiment Runner for Module M06
Module: M06 - Exact ALS Top-N Recommendation & Validation Evaluation

Executes end-to-end:
1. Loads M05 Spark ALS model factors (rank=16).
2. Audits scorable vs unscoreable catalog items and validation cold-start impact.
3. Extracts Train-seen interactions for all 162,541 users.
4. Executes benchmark gates (single user, heavy user, small batch, medium batch).
5. Generates exact Top-20 recommendations for all 162,541 Validation users.
6. Evaluates using Module M02 TopNEvaluator across K=5, 10, 20 on the 109,779 positive cohort.
7. Performs scientific comparison against Module M03 Popularity Count Baseline.
8. Serializes artifacts to artifacts/als/m06/.
"""

from __future__ import annotations

import json
import math
import os
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

# Ensure UTF-8 console output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import numpy as np
import pyarrow.parquet as pq

from recommender.als.candidates import (
    ALSCandidateConfig,
    ALSCandidateGenerator,
)
from recommender.als.evaluator import HeldOutTarget, TopNEvaluator


def run_m06_als_experiment() -> Dict[str, Any]:
    print("=" * 80, flush=True)
    print("MOODGRAPH TASK 3A - MODULE M06: EXACT ALS TOP-N EXPERIMENT & EVALUATION", flush=True)
    print("=" * 80, flush=True)

    t_pipeline_start = time.time()
    artifacts_dir = root_dir / "artifacts" / "als" / "m06"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    model_dir = root_dir / "artifacts" / "models" / "als" / "m05_spark_als_rank16"
    manifest_path = model_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"M05 model manifest not found at: {manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        model_manifest = json.load(f)

    manifest_cfg = model_manifest.get("config", {})
    manifest_meta = model_manifest.get("custom_metadata", {})

    print(f"Loaded M05 Model Manifest: {model_manifest.get('model_version')}", flush=True)
    print(f"  Base Training Commit: {manifest_meta.get('git_commit')}", flush=True)
    print(
        f"  Hyperparameters: rank={manifest_cfg.get('rank')}, "
        f"regParam={manifest_cfg.get('reg_param')}, "
        f"maxIter={manifest_cfg.get('max_iter')}",
        flush=True,
    )

    # 1. Load Validation Targets
    val_parquet_path = root_dir / "data" / "processed" / "splits" / "validation"
    print("\n[Step 1/7] Loading Validation Targets from Parquet...", flush=True)
    t0_val = time.time()
    tbl_val = pq.read_table(val_parquet_path)
    df_val = tbl_val.to_pandas()
    targets: Dict[int, HeldOutTarget] = {
        int(row["userId"]): HeldOutTarget(
            movie_id=int(row["movieId"]),
            rating=float(row["rating"]),
        )
        for _, row in df_val.iterrows()
    }
    pos_targets_count = sum(1 for t in targets.values() if t.rating >= 3.5)
    non_pos_count = len(targets) - pos_targets_count
    t_val = time.time() - t0_val
    print(f"  Total Validation users: {len(targets):,}", flush=True)
    print(f"  Positive cohort users (rating >= 3.5): {pos_targets_count:,}", flush=True)
    print(f"  Non-positive cohort users (rating < 3.5): {non_pos_count:,}", flush=True)
    print(f"  Target extraction completed in {t_val:.2f}s", flush=True)

    # 2. Extract User Seen History from Train Split
    train_parquet_path = root_dir / "data" / "processed" / "splits" / "train"
    print("\n[Step 2/7] Extracting User Train History (Seen Items) from Parquet...", flush=True)
    t0_hist = time.time()
    tbl_train = pq.read_table(train_parquet_path, columns=["userId", "movieId"])
    u_arr = tbl_train.column("userId").to_numpy()
    m_arr = tbl_train.column("movieId").to_numpy()
    user_histories: Dict[int, Set[int]] = defaultdict(set)
    for u, m in zip(u_arr, m_arr):
        user_histories[int(u)].add(int(m))

    t_hist = time.time() - t0_hist
    max_user_ratings = max(len(s) for s in user_histories.values())
    heavy_user_id = max(user_histories.keys(), key=lambda u: len(user_histories[u]))
    print(f"  Loaded {len(u_arr):,} Train interactions for {len(user_histories):,} users in {t_hist:.2f}s.", flush=True)
    print(f"  Heaviest user ID: {heavy_user_id} with {max_user_ratings:,} Train ratings.", flush=True)

    # 3. Load ALS Model Factors into Candidate Generator
    movies_parquet_path = root_dir / "data" / "processed" / "core" / "movies"
    print("\n[Step 3/7] Loading M05 ALS Factors into ALSCandidateGenerator...", flush=True)
    t0_gen = time.time()
    generator = ALSCandidateGenerator(
        config=ALSCandidateConfig(
            k_list=(5, 10, 20),
            batch_size=2500,
            model_version="m05_spark_als_rank16",
            candidate_source="ALS",
        )
    )
    generator.load_catalog_and_factors(
        model_dir=model_dir,
        movies_parquet_path=movies_parquet_path,
    )
    t_gen_load = time.time() - t0_gen
    print(f"  Factors loaded in {t_gen_load:.2f}s.", flush=True)

    # Catalog Audit
    catalog_audit = generator.audit_catalog()
    print("  Catalog Audit:", flush=True)
    print(f"    - Full Catalog: {catalog_audit['full_catalog_size']:,} movies", flush=True)
    print(f"    - ALS-Scoreable Catalog: {catalog_audit['scorable_catalog_size']:,} movies "
          f"({catalog_audit['scorable_coverage_percent']:.2f}%)", flush=True)
    print(f"    - Unscoreable Catalog: {catalog_audit['unscoreable_catalog_size']:,} movies", flush=True)

    # Audit Validation Positive Targets in Unscoreable Catalog
    scorable_movie_ids = generator.catalog.scorable_movie_ids
    pos_unscoreable_targets = [
        uid for uid, t in targets.items()
        if t.rating >= 3.5 and t.movie_id not in scorable_movie_ids
    ]
    max_achievable_hr = (pos_targets_count - len(pos_unscoreable_targets)) / float(pos_targets_count)
    print(f"    - Positive Validation Targets in Unscoreable Catalog: {len(pos_unscoreable_targets):,} users", flush=True)
    print(f"    - Theoretical Maximum Achievable HitRate: {max_achievable_hr * 100:.4f}%", flush=True)

    # 4. Performance Benchmark Gates
    print("\n[Step 4/7] Running Performance Benchmark Gates...", flush=True)
    benchmarks: Dict[str, Any] = {}

    # Gate A: 1 Regular user (user 1)
    t0_b1 = time.perf_counter()
    recs_user1 = generator.recommend_user(1, user_histories.get(1, set()), k=20)
    t_b1 = (time.perf_counter() - t0_b1) * 1000.0
    benchmarks["single_regular_user_ms"] = t_b1
    print(f"  [Gate A] Single regular user (user 1, {len(user_histories.get(1, set()))} seen): {t_b1:.2f} ms", flush=True)

    # Gate B: 1 Heavy user (32,200 seen items)
    t0_b2 = time.perf_counter()
    recs_heavy = generator.recommend_user(heavy_user_id, user_histories[heavy_user_id], k=20)
    t_b2 = (time.perf_counter() - t0_b2) * 1000.0
    benchmarks["single_heavy_user_ms"] = t_b2
    print(f"  [Gate B] Heavy user ({heavy_user_id}, {max_user_ratings:,} seen): {t_b2:.2f} ms", flush=True)

    # Gate C: Small batch (100 users)
    sample_100_uids = list(targets.keys())[:100]
    t0_b3 = time.perf_counter()
    recs_100 = generator.recommend_batch(sample_100_uids, user_histories, k=20)
    t_b3 = (time.perf_counter() - t0_b3) * 1000.0
    benchmarks["batch_100_users_ms"] = t_b3
    benchmarks["batch_100_throughput_users_sec"] = 100.0 / (t_b3 / 1000.0)
    print(f"  [Gate C] Small batch (100 users): {t_b3:.2f} ms ({benchmarks['batch_100_throughput_users_sec']:.1f} users/s)", flush=True)

    # Gate D: Medium batch (2,500 users)
    sample_2500_uids = list(targets.keys())[:2500]
    t0_b4 = time.perf_counter()
    recs_2500 = generator.recommend_batch(sample_2500_uids, user_histories, k=20)
    t_b4 = (time.perf_counter() - t0_b4) * 1000.0
    benchmarks["batch_2500_users_ms"] = t_b4
    benchmarks["batch_2500_throughput_users_sec"] = 2500.0 / (t_b4 / 1000.0)
    print(f"  [Gate D] Medium batch (2,500 users): {t_b4:.2f} ms ({benchmarks['batch_2500_throughput_users_sec']:.1f} users/s)", flush=True)

    # 5. Generate Full Top-20 for All 162,541 Validation Users
    print("\n[Step 5/7] Generating Exact Top-20 Recommendations for All 162,541 Users...", flush=True)
    t0_full = time.time()
    all_recommendations = generator.generate_recommendations(
        target_user_ids=targets.keys(),
        user_histories=user_histories,
        k=20,
        batch_size=2500,
        show_progress=True,
    )
    t_full_gen = time.time() - t0_full
    full_throughput = len(all_recommendations) / t_full_gen if t_full_gen > 0 else 0.0
    print(f"  Full generation finished in {t_full_gen:.2f}s ({full_throughput:.1f} users/s).", flush=True)
    print(f"  Total users with recommendations: {len(all_recommendations):,}", flush=True)

    # 6. Evaluate with TopNEvaluator (M02)
    print("\n[Step 6/7] Evaluating with TopNEvaluator across K=5, 10, 20...", flush=True)
    evaluator = TopNEvaluator(
        k_list=[5, 10, 20],
        relevance_threshold=3.5,
        catalog_size=catalog_audit["full_catalog_size"],
        scorable_catalog_size=catalog_audit["scorable_catalog_size"],
    )

    t0_eval = time.time()
    eval_recs = {
        uid: [mid for mid, _ in rec_list]
        for uid, rec_list in all_recommendations.items()
    }
    evaluation_summaries = evaluator.evaluate(eval_recs, targets)
    t_eval = time.time() - t0_eval
    print(f"  Evaluation completed in {t_eval:.2f}s.", flush=True)

    # Print Summary Table
    print("\n" + "=" * 90, flush=True)
    print("KET QUA DANH GIA CHINH THUC TREN TAP VALIDATION (MODULE M06 - ALS RANK 16)", flush=True)
    print("=" * 90, flush=True)
    print(f"{'Metric':<25} | {'K = 5':<18} | {'K = 10':<18} | {'K = 20':<18}", flush=True)
    print("-" * 90, flush=True)

    s5 = evaluation_summaries[5]
    s10 = evaluation_summaries[10]
    s20 = evaluation_summaries[20]

    print(f"{'HitRate@K':<25} | {s5.hit_rate:<18.5f} | {s10.hit_rate:<18.5f} | {s20.hit_rate:<18.5f}", flush=True)
    print(f"{'NDCG@K':<25} | {s5.ndcg:<18.5f} | {s10.ndcg:<18.5f} | {s20.ndcg:<18.5f}", flush=True)
    print(f"{'MRR@K':<25} | {s5.mrr:<18.5f} | {s10.mrr:<18.5f} | {s20.mrr:<18.5f}", flush=True)
    print(f"{'Precision@K':<25} | {s5.precision:<18.5f} | {s10.precision:<18.5f} | {s20.precision:<18.5f}", flush=True)
    print(f"{'Recall@K':<25} | {s5.recall:<18.5f} | {s10.recall:<18.5f} | {s20.recall:<18.5f}", flush=True)
    print(f"{'Catalog Coverage (Full)':<25} | {s5.catalog_coverage_full * 100:<17.2f}% | "
          f"{s10.catalog_coverage_full * 100:<17.2f}% | {s20.catalog_coverage_full * 100:<17.2f}%", flush=True)
    print(f"{'Catalog Cov (Scorable)':<25} | {s5.catalog_coverage_scorable * 100:<17.2f}% | "
          f"{s10.catalog_coverage_scorable * 100:<17.2f}% | {s20.catalog_coverage_scorable * 100:<17.2f}%", flush=True)
    print(f"{'Distinct Movies Rec':<25} | {s5.num_unique_recommended_movies:<18,d} | "
          f"{s10.num_unique_recommended_movies:<18,d} | {s20.num_unique_recommended_movies:<18,d}", flush=True)
    print(f"{'Total Positive Hits':<25} | {s5.hit_count:<18,d} | {s10.hit_count:<18,d} | {s20.hit_count:<18,d}", flush=True)
    print(f"{'Positive Cohort Size':<25} | {s10.positive_cohort_size:<18,d} | "
          f"{s10.positive_cohort_size:<18,d} | {s10.positive_cohort_size:<18,d}", flush=True)
    print("=" * 90, flush=True)

    # 7. Comparison with M03 Popularity Count Baseline
    pop_count_k10 = {
        "hit_rate": 0.05519,
        "ndcg": 0.02789,
        "mrr": 0.01970,
        "precision": 0.00552,
        "recall": 0.05519,
        "coverage_full": 0.00497,  # 0.50%
        "distinct_movies": 310,
    }

    print("\n" + "=" * 90, flush=True)
    print("DOI CHUNG THUC NGHIEM: SPARK ALS RANK 16 VS POPULARITY COUNT BASELINE (K = 10)", flush=True)
    print("=" * 90, flush=True)
    print(f"{'Chi so (Metric)':<28} | {'Popularity Count (M03)':<25} | {'ALS rank16 (M06)':<25} | {'Ty le (ALS / Pop)'}", flush=True)
    print("-" * 90, flush=True)
    print(f"{'HitRate@10':<28} | {pop_count_k10['hit_rate']:<25.5f} | {s10.hit_rate:<25.5f} | "
          f"{s10.hit_rate / pop_count_k10['hit_rate']:.2f}x", flush=True)
    print(f"{'NDCG@10':<28} | {pop_count_k10['ndcg']:<25.5f} | {s10.ndcg:<25.5f} | "
          f"{s10.ndcg / pop_count_k10['ndcg']:.2f}x", flush=True)
    print(f"{'MRR@10':<28} | {pop_count_k10['mrr']:<25.5f} | {s10.mrr:<25.5f} | "
          f"{s10.mrr / pop_count_k10['mrr']:.2f}x", flush=True)
    print(f"{'Precision@10':<28} | {pop_count_k10['precision']:<25.5f} | {s10.precision:<25.5f} | "
          f"{s10.precision / pop_count_k10['precision']:.2f}x", flush=True)
    print(f"{'Catalog Coverage (Full)':<28} | {pop_count_k10['coverage_full'] * 100:<24.2f}% | "
          f"{s10.catalog_coverage_full * 100:<24.2f}% | "
          f"{s10.catalog_coverage_full / pop_count_k10['coverage_full']:.1f}x", flush=True)
    print(f"{'Distinct Movies Rec':<28} | {pop_count_k10['distinct_movies']:<25,d} | "
          f"{s10.num_unique_recommended_movies:<25,d} | "
          f"{s10.num_unique_recommended_movies / pop_count_k10['distinct_movies']:.1f}x", flush=True)
    print("=" * 90, flush=True)

    # Save Output Artifacts
    print("\nSaving Output Artifacts...", flush=True)
    parquet_out = artifacts_dir / "m06_als_top20_recommendations.parquet"
    print(f"  Saving Parquet to: {parquet_out}", flush=True)
    generator.save_recommendations_parquet(all_recommendations, parquet_out)
    parquet_size_mb = parquet_out.stat().st_size / (1024.0 * 1024.0)
    print(f"  Parquet saved successfully ({parquet_size_mb:.2f} MB, {len(all_recommendations) * 20:,} rows).", flush=True)

    # Save Metrics JSON
    results_json_path = artifacts_dir / "m06_als_evaluation_results.json"
    t_total_pipeline = time.time() - t_pipeline_start
    experiment_results = {
        "metadata": {
            "module": "M06",
            "model_version": "m05_spark_als_rank16",
            "git_commit_base_training": manifest_meta.get("git_commit"),
            "execution_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "environment": {
                "os": "win32",
                "python": sys.version,
                "cpu": "AMD Ryzen 5 7530U",
                "ram_gb": 16,
            },
            "timings_seconds": {
                "target_extraction": t_val,
                "seen_history_extraction": t_hist,
                "factors_loading": t_gen_load,
                "recommendation_generation": t_full_gen,
                "top_n_evaluation": t_eval,
                "total_pipeline": t_total_pipeline,
            },
            "benchmarks": benchmarks,
            "catalog_audit": catalog_audit,
            "unscoreable_targets_audit": {
                "num_positive_unscoreable_targets": len(pos_unscoreable_targets),
                "theoretical_max_hit_rate": max_achievable_hr,
            },
            "cohort_sizes": {
                "total_validation_users": len(targets),
                "positive_cohort_size": pos_targets_count,
                "non_positive_cohort_size": non_pos_count,
            },
        },
        "metrics": {
            k: summary.to_dict()
            for k, summary in evaluation_summaries.items()
        },
        "baseline_comparison_k10": {
            "popularity_count": pop_count_k10,
            "als_rank16": {
                "hit_rate": s10.hit_rate,
                "ndcg": s10.ndcg,
                "mrr": s10.mrr,
                "precision": s10.precision,
                "recall": s10.recall,
                "coverage_full": s10.catalog_coverage_full,
                "distinct_movies": s10.num_unique_recommended_movies,
            },
            "ratios": {
                "hit_rate_ratio": s10.hit_rate / pop_count_k10["hit_rate"],
                "ndcg_ratio": s10.ndcg / pop_count_k10["ndcg"],
                "mrr_ratio": s10.mrr / pop_count_k10["mrr"],
                "coverage_ratio": s10.catalog_coverage_full / pop_count_k10["coverage_full"],
                "distinct_movies_ratio": s10.num_unique_recommended_movies / pop_count_k10["distinct_movies"],
            },
        },
    }

    with open(results_json_path, "w", encoding="utf-8") as f:
        json.dump(experiment_results, f, indent=2)
    print(f"  Evaluation results JSON saved to: {results_json_path}", flush=True)

    # Build Sample Demonstrations (with movie titles)
    print("\nBuilding Sample Demonstrations for Defense...", flush=True)
    movies_title_map: Dict[int, str] = {}
    tbl_movies = pq.read_table(movies_parquet_path)
    df_m = tbl_movies.to_pandas()
    for _, r in df_m.iterrows():
        movies_title_map[int(r["movieId"])] = str(r["title"])

    demo_uids = [1, 10, 100, heavy_user_id]
    demo_samples = []
    for uid in demo_uids:
        user_recs = all_recommendations.get(uid, [])
        target = targets.get(uid)
        demo_samples.append({
            "userId": uid,
            "train_seen_count": len(user_histories.get(uid, set())),
            "validation_target": {
                "movieId": target.movie_id if target else None,
                "title": movies_title_map.get(target.movie_id, "Unknown") if target else None,
                "rating": target.rating if target else None,
            },
            "top_10_recommendations": [
                {
                    "rank": idx + 1,
                    "movieId": mid,
                    "title": movies_title_map.get(mid, "Unknown"),
                    "als_score": round(score, 4),
                }
                for idx, (mid, score) in enumerate(user_recs[:10])
            ],
        })

    demo_json_path = artifacts_dir / "m06_sample_user_recommendations.json"
    with open(demo_json_path, "w", encoding="utf-8") as f:
        json.dump(demo_samples, f, indent=2)
    print(f"  Demo samples saved to: {demo_json_path}", flush=True)

    print(f"\n=== M06 Pipeline Completed Successfully in {t_total_pipeline:.2f}s ===", flush=True)
    return experiment_results


if __name__ == "__main__":
    run_m06_als_experiment()
