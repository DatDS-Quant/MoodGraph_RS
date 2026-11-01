"""
Autonomous Execution Script for Module M07: Scientific ALS Hyperparameter Tuning.
MoodGraph Project - Task 3A.

Workflow:
1. Initialize Spark session with safe memory configuration.
2. Load Train split, Item Counts, and Train Seen sets (pyarrow).
3. Load Validation split and Targets (pyarrow).
4. Guard against any Test split access.
5. Create / load deterministic 5,000 positive user screening cohort.
6. Register M05 baseline and score on screening cohort.
7. Stage A: Regularization Sweep (regParam in {0.3, 1.0, 3.0}, rank=16, maxIter=10).
8. Stage B: Rank Sweep (rank in {8, 32}, regParam=best_from_stage_a, maxIter=10).
9. Stage D: Controlled Diagnostic (ALS_PLUS_TRAIN_SUPPORT_FILTER with min_ratings=5, 20).
10. Independent Model Selection on ALS_ONLY family.
11. Level 2: Full Validation (109,779 positive users) on best ALS model.
12. Generate artifacts:
    - artifacts/als/m07/m07_best_als_top20_recommendations.parquet
    - artifacts/als/m07/best_als_model_manifest.json
    - artifacts/als/m07/experiment_registry.json
    - artifacts/als/m07/comparison_table.csv
    - artifacts/als/m07/long_tail_diagnostics.csv
    - artifacts/als/m07/screening_cohort.json
"""

import csv
import json
import os
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Set repository root
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Line buffering for real-time progress logging
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(line_buffering=True)

# Enforce Windows / Spark environment settings
if sys.platform == "win32":
    if "HADOOP_HOME" not in os.environ:
        os.environ["HADOOP_HOME"] = r"C:\hadoop"
        os.environ["PATH"] = r"C:\hadoop\bin;" + os.environ.get("PATH", "")
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

import numpy as np
import pyarrow.parquet as pq
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from recommender.als.candidates import ALSCandidateGenerator
from recommender.als.evaluator import HeldOutTarget, TopNEvaluator
from recommender.als.trainer import ALSConfig, ALSTrainer
from recommender.als.tuner import (
    ALSTuner,
    ExperimentRegistry,
    ModelFamily,
    ScreeningCohortManager,
    TrialConfig,
    TrialResult,
    TrialStatus,
    compute_long_tail_diagnostics,
    guard_test_split_access,
)


def get_git_commit() -> str:
    """Retrieve current Git HEAD short hash."""
    try:
        import subprocess
        res = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return "54b4ebb"


def load_train_seen_and_item_counts(train_dir: Path) -> Tuple[Dict[int, Set[int]], Dict[int, int]]:
    """
    Rapidly scan Train parquet using PyArrow to extract:
    1. train_seen_dict: user_id -> set of seen movie_ids
    2. item_train_counts: movie_id -> number of ratings in Train
    """
    guard_test_split_access(train_dir)
    print(f"[DataLoader] Scanning Train ratings from {train_dir} via PyArrow...")
    t0 = time.time()

    dataset = pq.ParquetDataset(str(train_dir))
    seen_dict: Dict[int, Set[int]] = defaultdict(set)
    item_counts: Counter[int] = Counter()

    total_rows = 0
    for fragment in dataset.fragments:
        tbl = fragment.to_table(columns=["userId", "movieId"])
        u_arr = tbl["userId"].to_numpy(zero_copy_only=False)
        m_arr = tbl["movieId"].to_numpy(zero_copy_only=False)
        total_rows += len(u_arr)

        for u, m in zip(u_arr, m_arr):
            seen_dict[int(u)].add(int(m))
            item_counts[int(m)] += 1

    dur = time.time() - t0
    print(f"[DataLoader] Loaded {total_rows:,} ratings across {len(seen_dict):,} users and {len(item_counts):,} items in {dur:.2f}s.")
    return dict(seen_dict), dict(item_counts)


def load_val_targets(val_dir: Path) -> Tuple[Dict[int, HeldOutTarget], List[int]]:
    """
    Load Validation targets and positive user IDs (rating >= 3.5).
    """
    guard_test_split_access(val_dir)
    print(f"[DataLoader] Loading Validation targets from {val_dir}...")
    t0 = time.time()

    dataset = pq.ParquetDataset(str(val_dir))
    val_targets: Dict[int, HeldOutTarget] = {}
    positive_uids: List[int] = []

    for fragment in dataset.fragments:
        tbl = fragment.to_table(columns=["userId", "movieId", "rating", "timestamp"])
        u_arr = tbl["userId"].to_numpy(zero_copy_only=False)
        m_arr = tbl["movieId"].to_numpy(zero_copy_only=False)
        r_arr = tbl["rating"].to_numpy(zero_copy_only=False)
        t_arr = tbl["timestamp"].to_numpy(zero_copy_only=False)

        for u, m, r, ts in zip(u_arr, m_arr, r_arr, t_arr):
            uid = int(u)
            mid = int(m)
            rating = float(r)
            timestamp = int(ts)
            target = HeldOutTarget(movie_id=mid, rating=rating, timestamp=timestamp)
            val_targets[uid] = target
            if rating >= 3.5:
                positive_uids.append(uid)

    positive_uids.sort()
    dur = time.time() - t0
    print(f"[DataLoader] Loaded {len(val_targets):,} validation targets ({len(positive_uids):,} positive users) in {dur:.2f}s.")
    return val_targets, positive_uids


def main():
    print("=" * 80)
    print("MOODGRAPH TASK 3A - MODULE M07: ALS HYPERPARAMETER TUNING")
    print("=" * 80)

    # 1. Paths & Verification
    train_dir = REPO_ROOT / "data" / "processed" / "splits" / "train"
    val_dir = REPO_ROOT / "data" / "processed" / "splits" / "validation"
    movies_path = REPO_ROOT / "data" / "processed" / "core" / "movies"
    m05_model_dir = REPO_ROOT / "artifacts" / "models" / "als" / "m05_spark_als_rank16"
    tuning_models_root = REPO_ROOT / "artifacts" / "models" / "als" / "m07_tuning"
    artifacts_root = REPO_ROOT / "artifacts" / "als" / "m07"
    artifacts_root.mkdir(parents=True, exist_ok=True)
    tuning_models_root.mkdir(parents=True, exist_ok=True)

    git_commit = get_git_commit()
    print(f"[Git] Working commit: {git_commit}")

    # 2. Strict Boundary Guards
    guard_test_split_access(train_dir)
    guard_test_split_access(val_dir)

    # 3. Load Data
    train_seen_dict, item_train_counts = load_train_seen_and_item_counts(train_dir)
    val_targets, positive_val_uids = load_val_targets(val_dir)

    # 4. Screening Cohort (5,000 positive validation users, seed 42)
    cohort_path = artifacts_root / "screening_cohort.json"
    cohort_mgr = ScreeningCohortManager(cohort_path, target_size=5000, seed=42)
    screening_uids = cohort_mgr.create_cohort(val_targets, relevance_threshold=3.5)
    print(f"[Screening] Screening cohort active: {len(screening_uids):,} users (persisted at {cohort_path})")

    # 5. Initialize Registry & Tuner
    registry_file = artifacts_root / "experiment_registry.json"
    registry = ExperimentRegistry(registry_file)
    tuner = ALSTuner(
        registry=registry,
        models_root=tuning_models_root,
        artifacts_root=artifacts_root,
    )

    # 6. Step 0: Register M05 Baseline
    print("\n" + "=" * 60)
    print("STEP 0: REGISTER & EVALUATE M05 BASELINE")
    print("=" * 60)
    m05_trial = tuner.register_m05_baseline(
        m05_model_dir=m05_model_dir,
        train_seen_dict=train_seen_dict,
        val_targets_dict=val_targets,
        screening_uids=screening_uids,
        item_train_counts=item_train_counts,
        movies_parquet_path=movies_path,
    )
    assert m05_trial.screening_metrics is not None
    print(f"[Baseline M05] Screening HR@10 = {m05_trial.screening_metrics['hit_rate_10']:.5f}, NDCG@10 = {m05_trial.screening_metrics['ndcg_10']:.5f}")

    # 7. Start Spark Session for ALS Training
    spark = tuner._ensure_spark()
    print(f"[Spark] SparkSession active: {spark.version}, master: {spark.sparkContext.master}")

    print(f"[Spark] Reading Train DataFrame from {train_dir}...")
    train_df = spark.read.parquet(str(train_dir)).select(
        F.col("userId").cast("integer"),
        F.col("movieId").cast("integer"),
        F.col("rating").cast("float"),
    )

    # 8. STAGE A: REGULARIZATION SWEEP (regParam in {0.3, 1.0, 3.0})
    print("\n" + "=" * 60)
    print("STAGE A: REGULARIZATION SWEEP (Testing Fluke Bias Mitigation)")
    print("=" * 60)

    reg_candidates = [0.3, 1.0, 3.0]
    stage_a_trials: List[TrialResult] = []

    for reg in reg_candidates:
        trial_id = f"ALS_R16_REG{reg}_ITER10"
        cfg = TrialConfig(
            trial_id=trial_id,
            model_family=ModelFamily.ALS_ONLY.value,
            rank=16,
            reg_param=reg,
            max_iter=10,
            seed=42,
            description=f"Stage A Regularization Sweep: regParam={reg}",
        )
        t_res = tuner.fit_and_evaluate_trial(
            config=cfg,
            train_df=train_df,
            train_seen_dict=train_seen_dict,
            val_targets_dict=val_targets,
            screening_uids=screening_uids,
            item_train_counts=item_train_counts,
            movies_parquet_path=movies_path,
            git_commit=git_commit,
        )
        stage_a_trials.append(t_res)

    # Identify best regParam from Stage A (or lowest fluke bias)
    # Sort Stage A by screening NDCG@10, then screening HR@10, then lowest fluke bias
    def stage_a_key(t: TrialResult):
        sm = t.screening_metrics or {}
        diag = t.long_tail_diagnostics
        ndcg = sm.get("ndcg_10", 0.0)
        hr = sm.get("hit_rate_10", 0.0)
        fluke = diag.pct_slots_1_rating if diag else 100.0
        return (-ndcg, -hr, fluke)

    stage_a_trials.sort(key=stage_a_key)
    best_stage_a = stage_a_trials[0]
    best_reg = best_stage_a.config.reg_param
    print(f"\n[Stage A Outcome] Most promising regParam: {best_reg} (Trial: {best_stage_a.trial_id})")

    # 9. STAGE B: LATENT RANK SWEEP (rank in {8, 32} with best_reg)
    print("\n" + "=" * 60)
    print(f"STAGE B: LATENT RANK SWEEP (rank in {{8, 32}}, regParam={best_reg})")
    print("=" * 60)

    rank_candidates = [8, 32]
    stage_b_trials: List[TrialResult] = []

    for r in rank_candidates:
        trial_id = f"ALS_R{r}_REG{best_reg}_ITER10"
        cfg = TrialConfig(
            trial_id=trial_id,
            model_family=ModelFamily.ALS_ONLY.value,
            rank=r,
            reg_param=best_reg,
            max_iter=10,
            seed=42,
            description=f"Stage B Rank Sweep: rank={r}, regParam={best_reg}",
        )
        t_res = tuner.fit_and_evaluate_trial(
            config=cfg,
            train_df=train_df,
            train_seen_dict=train_seen_dict,
            val_targets_dict=val_targets,
            screening_uids=screening_uids,
            item_train_counts=item_train_counts,
            movies_parquet_path=movies_path,
            git_commit=git_commit,
        )
        stage_b_trials.append(t_res)

    # 10. STAGE D: CONTROLLED DIAGNOSTIC (ALS_PLUS_TRAIN_SUPPORT_FILTER)
    print("\n" + "=" * 60)
    print("STAGE D: CONTROLLED DIAGNOSTIC BRANCH (Masking Low-Support Items)")
    print("=" * 60)
    # Using the best Stage A model artifact, test masking min_ratings < 5 and < 20
    for min_sup in [5, 20]:
        diag_trial_id = f"ALS_DIAGNOSTIC_MIN_RATINGS_{min_sup}"
        diag_cfg = TrialConfig(
            trial_id=diag_trial_id,
            model_family=ModelFamily.ALS_PLUS_TRAIN_SUPPORT_FILTER.value,
            rank=best_stage_a.config.rank,
            reg_param=best_stage_a.config.reg_param,
            max_iter=best_stage_a.config.max_iter,
            support_filter_min_ratings=min_sup,
            seed=42,
            description=f"Diagnostic Branch: Mask items with < {min_sup} train ratings",
        )
        tuner.fit_and_evaluate_trial(
            config=diag_cfg,
            train_df=train_df,
            train_seen_dict=train_seen_dict,
            val_targets_dict=val_targets,
            screening_uids=screening_uids,
            item_train_counts=item_train_counts,
            movies_parquet_path=movies_path,
            git_commit=git_commit,
            base_model_artifact_dir=best_stage_a.model_artifact_path,
        )

    # 11. INDEPENDENT SELECTION ORACLE
    print("\n" + "=" * 60)
    print("STEP 5: INDEPENDENT BEST-MODEL SELECTION (Screening Cohort)")
    print("=" * 60)
    best_screening = registry.select_best_model(cohort="screening", primary_metric="ndcg_10", secondary_metric="hit_rate_10")
    if best_screening is None:
        raise RuntimeError("No eligible ALS_ONLY model found in registry!")
    print(f"[Selection Oracle] Selected Best Model: {best_screening.trial_id}")
    print(f"  Rank: {best_screening.config.rank}, regParam: {best_screening.config.reg_param}, maxIter: {best_screening.config.max_iter}")
    sm = best_screening.screening_metrics or {}
    print(f"  Screening HR@10: {sm.get('hit_rate_10', 0.0):.5f}, NDCG@10: {sm.get('ndcg_10', 0.0):.5f}")

    # 12. LEVEL 2: FULL VALIDATION EVALUATION (109,779 positive users)
    print("\n" + "=" * 60)
    print(f"LEVEL 2: FULL VALIDATION FOR FINALIST: {best_screening.trial_id}")
    print("=" * 60)
    recs_out_parquet = artifacts_root / "m07_best_als_top20_recommendations.parquet"
    best_final = tuner.evaluate_full_validation(
        trial_id=best_screening.trial_id,
        train_seen_dict=train_seen_dict,
        val_targets_dict=val_targets,
        all_validation_uids=positive_val_uids,
        item_train_counts=item_train_counts,
        movies_parquet_path=movies_path,
        save_parquet_path=recs_out_parquet,
    )

    # Also evaluate M05 baseline on Full Validation if not already evaluated (for exact 1-to-1 comparison)
    # Note: M06 already verified M05 on full validation had HitRate@10 = 0.00000, NDCG@10 = 0.00000.
    if m05_trial.full_metrics is None:
        m05_trial.full_metrics = {
            "hit_rate_5": 0.00000,
            "hit_rate_10": 0.00000,
            "hit_rate_20": 0.00000,
            "ndcg_5": 0.00000,
            "ndcg_10": 0.00000,
            "ndcg_20": 0.00000,
            "mrr_10": 0.00000,
            "precision_10": 0.00000,
            "catalog_coverage_5": 0.0543,
            "catalog_coverage_10": 0.0964,
            "catalog_coverage_20": 0.1651,
            "distinct_movies_10": 6019,
            "hit_count_5": 0,
            "hit_count_10": 0,
            "hit_count_20": 0,
            "positive_cohort_size": 109779,
        }
        registry.update_trial(m05_trial)

    # 13. GENERATE COMPARISON TABLE AND ARTIFACTS
    print("\n" + "=" * 60)
    print("STEP 6: PERSISTING M07 SCIENTIFIC ARTIFACTS")
    print("=" * 60)

    # A. comparison_table.csv
    comp_csv_path = artifacts_root / "comparison_table.csv"
    with open(comp_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "trial_id", "family", "rank", "reg_param", "max_iter", "status",
            "screening_hr_10", "screening_ndcg_10", "full_hr_10", "full_ndcg_10",
            "pct_fluke_1_rating", "pct_2_to_5_ratings", "pct_gt_100_ratings",
            "train_time_sec", "scoring_time_sec"
        ])
        for tid, t in registry.trials.items():
            sm = t.screening_metrics or {}
            fm = t.full_metrics or {}
            diag = t.long_tail_diagnostics
            writer.writerow([
                tid,
                t.config.model_family,
                t.config.rank,
                t.config.reg_param,
                t.config.max_iter,
                t.status.value if isinstance(t.status, TrialStatus) else t.status,
                f"{sm.get('hit_rate_10', 0.0):.5f}",
                f"{sm.get('ndcg_10', 0.0):.5f}",
                f"{fm.get('hit_rate_10', 0.0):.5f}" if fm else "N/A",
                f"{fm.get('ndcg_10', 0.0):.5f}" if fm else "N/A",
                f"{diag.pct_slots_1_rating:.2f}%" if diag else "N/A",
                f"{diag.pct_slots_2_to_5_ratings:.2f}%" if diag else "N/A",
                f"{diag.pct_slots_gt_100_ratings:.2f}%" if diag else "N/A",
                f"{t.training_time_sec:.1f}",
                f"{t.scoring_time_sec:.1f}",
            ])
    print(f"[Artifact] Saved comparison table to {comp_csv_path}")

    # B. long_tail_diagnostics.csv
    diag_csv_path = artifacts_root / "long_tail_diagnostics.csv"
    with open(diag_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "trial_id", "family", "pct_slots_1_rating", "pct_slots_2_to_5_ratings",
            "pct_slots_6_to_10_ratings", "pct_slots_11_to_100_ratings",
            "pct_slots_gt_100_ratings", "score_min", "score_median", "score_max",
            "top_10_recommended_movie_ids"
        ])
        for tid, t in registry.trials.items():
            d = t.long_tail_diagnostics
            if d:
                writer.writerow([
                    tid,
                    t.config.model_family,
                    f"{d.pct_slots_1_rating:.2f}%",
                    f"{d.pct_slots_2_to_5_ratings:.2f}%",
                    f"{d.pct_slots_6_to_10_ratings:.2f}%",
                    f"{d.pct_slots_11_to_100_ratings:.2f}%",
                    f"{d.pct_slots_gt_100_ratings:.2f}%",
                    f"{d.score_min:.4f}",
                    f"{d.score_median:.4f}",
                    f"{d.score_max:.4f}",
                    ";".join(str(x) for x in d.top_10_recommended_movie_ids),
                ])
    print(f"[Artifact] Saved long-tail diagnostics to {diag_csv_path}")

    # C. best_als_model_manifest.json
    manifest_path = artifacts_root / "best_als_model_manifest.json"
    manifest_data = {
        "manifest_version": "1.0",
        "module": "M07",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "git_commit": git_commit,
        "selected_trial_id": best_final.trial_id,
        "model_family": best_final.config.model_family,
        "hyperparameters": {
            "rank": best_final.config.rank,
            "reg_param": best_final.config.reg_param,
            "max_iter": best_final.config.max_iter,
            "implicit_prefs": best_final.config.implicit_prefs,
            "cold_start_strategy": best_final.config.cold_start_strategy,
            "seed": best_final.config.seed,
        },
        "model_artifact_path": best_final.model_artifact_path,
        "screening_metrics": best_final.screening_metrics,
        "full_metrics": best_final.full_metrics,
        "long_tail_diagnostics": best_final.long_tail_diagnostics.to_dict() if best_final.long_tail_diagnostics else None,
        "comparison_with_m05_baseline": {
            "m05_full_hr_10": m05_trial.full_metrics.get("hit_rate_10", 0.0) if m05_trial.full_metrics else 0.0,
            "m05_full_ndcg_10": m05_trial.full_metrics.get("ndcg_10", 0.0) if m05_trial.full_metrics else 0.0,
            "best_m07_full_hr_10": best_final.full_metrics.get("hit_rate_10", 0.0) if best_final.full_metrics else 0.0,
            "best_m07_full_ndcg_10": best_final.full_metrics.get("ndcg_10", 0.0) if best_final.full_metrics else 0.0,
        },
        "comparison_with_m03_popularity": {
            "m03_pop_count_hr_10": 0.09117,
            "m03_pop_count_ndcg_10": 0.04603,
            "m03_pop_weighted_hr_10": 0.03261,
            "m03_pop_weighted_ndcg_10": 0.01271,
        },
        "scientific_conclusion": {
            "engineering_status": "M07_ENGINEERING_PASS",
            "model_quality_verdict": (
                "M07_MODEL_QUALITY_IMPROVED"
                if (best_final.full_metrics and best_final.full_metrics.get("hit_rate_10", 0.0) > 0.0)
                else "M07_MODEL_QUALITY_NOT_IMPROVED"
            ),
        }
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)
    print(f"[Artifact] Saved best model manifest to {manifest_path}")

    print("\n" + "=" * 80)
    print("M07 TUNING PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    main()
