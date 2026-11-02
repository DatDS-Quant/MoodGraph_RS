"""
MoodGraph - Task 3A: Module M05 Spark ALS Training Pipeline Runner
(Kịch bản thực thi huấn luyện mô hình Spark ALS trên toàn bộ MovieLens 25M).

Quy trình thực thi:
1. Kiểm toán môi trường thực thi và tài nguyên phần cứng.
2. Nạp 24.675.013 tương tác Train từ Parquet.
3. Xác thực hợp đồng lược đồ dữ liệu PySpark.
4. Huấn luyện mô hình PySpark ALS (rank=16, maxIter=10, regParam=0.1, seed=42).
5. Kiểm toán kích thước và độ hợp lệ của userFactors (162.541) và itemFactors (58.932).
6. Kiểm chứng toán học độc lập: So khớp tích vô hướng thủ công với Spark transform.
7. Tính toán chẩn đoán kỹ thuật nội bộ (diagnostic RMSE/MAE).
8. Lưu trữ mô hình và manifest vào artifacts/models/als/m05_spark_als_rank16/.
9. Nạp lại mô hình để kiểm chứng tính toàn vẹn của tệp lưu trữ.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

if sys.platform.startswith("win"):
    if os.path.exists(r"C:\hadoop"):
        os.environ["HADOOP_HOME"] = r"C:\hadoop"
        os.environ["PATH"] = r"C:\hadoop\bin;" + os.environ.get("PATH", "")
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

import psutil
from pyspark.sql import SparkSession

from recommender.als.data_loader import (
    get_repo_root,
    get_spark_session,
    load_train_data,
)
from recommender.als.trainer import (
    ALSConfig,
    ALSTrainer,
)


def get_git_commit() -> str:
    """Retrieve current Git commit SHA safely."""
    try:
        import subprocess
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        return "38c5c4f"


def run_m05_training_pipeline() -> Dict[str, Any]:
    print("=" * 80)
    print("MOODGRAPH TASK 3A - MODULE M05: FULL SPARK ALS TRAINING ON MOVIELENS 25M")
    print("=" * 80)

    pipeline_start = time.time()
    git_commit = get_git_commit()

    # Pre-flight system telemetry
    vmem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    print(f"\n[Telemetry] Git Commit:      {git_commit}")
    print(f"[Telemetry] Physical RAM:    Total={vmem.total/(1024**3):.2f} GB, Avail={vmem.available/(1024**3):.2f} GB")
    print(f"[Telemetry] Virtual Swap:    Total={swap.total/(1024**3):.2f} GB, Free={swap.free/(1024**3):.2f} GB")
    print(f"[Telemetry] CPU Logical:     {psutil.cpu_count(logical=True)} cores")

    # 1. Initialize SparkSession
    print("\n--- [Step 1] Initializing Production SparkSession ---")
    spark = get_spark_session(
        app_name="MoodGraph_M05_Full_Train",
        master="local[4]",
        driver_memory="6g",
        shuffle_partitions=16,
    )
    sc = spark.sparkContext
    checkpoint_dir = get_repo_root() / "tmp" / "spark_checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    sc.setCheckpointDir(str(checkpoint_dir))
    print(f"  Spark Master:           {sc.master}")
    print(f"  Spark App Name:         {sc.appName}")
    print(f"  Spark Version:          {spark.version}")
    print(f"  Checkpoint Directory:   {checkpoint_dir.resolve()}")

    try:
        # 2. Load Train Dataset
        print("\n--- [Step 2] Loading MovieLens 25M Train Split (Parquet) ---")
        t_load_start = time.time()
        train_df = load_train_data(spark)
        # Note: Do not collect or cache unnecessarily to preserve memory
        total_train_rows = train_df.count()
        t_load = time.time() - t_load_start
        print(f"  Loaded Train Rows:      {total_train_rows:,} in {t_load:.2f}s")
        if total_train_rows != 24675013:
            raise ValueError(f"Expected 24,675,013 rows, but observed {total_train_rows}")

        # 3. Configure ALS Trainer
        print("\n--- [Step 3] Configuring Production ALS Parameters ---")
        config = ALSConfig(
            rank=16,
            max_iter=10,
            reg_param=0.1,
            implicit_prefs=False,
            cold_start_strategy="nan",
            seed=42,
            user_col="userId",
            item_col="movieId",
            rating_col="rating",
            intermediate_storage_level="MEMORY_AND_DISK",
            final_storage_level="MEMORY_AND_DISK",
            checkpoint_interval=10,
        )
        config.validate()
        print(f"  Rank:                   {config.rank}")
        print(f"  Max Iterations:         {config.max_iter}")
        print(f"  Reg Param (lambda):     {config.reg_param}")
        print(f"  Implicit Prefs:         {config.implicit_prefs} (Explicit Feedback Mode)")
        print(f"  Cold Start Strategy:    '{config.cold_start_strategy}' (Preserves Denominator)")
        print(f"  Random Seed:            {config.seed} (Deterministic Reproducibility)")

        # 4. Fit ALS Model
        print("\n--- [Step 4] Fitting Spark ALS on 24,675,013 Ratings ---")
        trainer = ALSTrainer(config)
        t_fit_start = time.time()
        model = trainer.fit(train_df)
        t_fit = time.time() - t_fit_start
        print(f"  Spark ALS fit completed in {t_fit:.2f}s ({t_fit/60:.2f} minutes).")

        # 5. Factor Matrices Audit
        print("\n--- [Step 5] Auditing Learned Factor Matrices ---")
        t_audit_start = time.time()
        user_audit, item_audit = trainer.audit_factors(model)
        t_audit = time.time() - t_audit_start
        print(f"  userFactors: {user_audit.count:,} distinct users | rank={user_audit.rank} | "
              f"NaN={user_audit.has_nan} | Inf={user_audit.has_inf} | "
              f"Norm mean={user_audit.norm_mean:.4f} (min={user_audit.norm_min:.4f}, max={user_audit.norm_max:.4f})")
        print(f"  itemFactors: {item_audit.count:,} distinct movies | rank={item_audit.rank} | "
              f"NaN={item_audit.has_nan} | Inf={item_audit.has_inf} | "
              f"Norm mean={item_audit.norm_mean:.4f} (min={item_audit.norm_min:.4f}, max={item_audit.norm_max:.4f})")

        if user_audit.count != 162541:
            raise ValueError(f"Expected 162,541 user factors, got {user_audit.count}")
        if item_audit.count != 58932:
            raise ValueError(f"Expected 58,932 item factors, got {item_audit.count}")
        if not user_audit.is_valid or not item_audit.is_valid:
            raise ValueError("Factor matrix validation failed (NaNs, Infs, or rank mismatch detected)")
        print(f"  Factor audit passed in {t_audit:.2f}s.")

        # 6. Independent Mathematical Verification: Manual Dot vs Spark Transform
        print("\n--- [Step 6] Independent Dot Product Verification on Random Sample ---")
        sample_df = train_df.sample(withReplacement=False, fraction=0.001, seed=42).limit(30)
        math_audit = trainer.verify_manual_dot_product(model, sample_df, tolerance=1e-4)
        print(f"  Sample Pairs Evaluated: {math_audit['num_samples']}")
        print(f"  Max Absolute Difference:{math_audit['max_abs_diff']:.8f}")
        print(f"  Mean Absolute Diff:     {math_audit['mean_abs_diff']:.8f}")
        print(f"  All Matched (<=1e-4):   {math_audit['all_matched']}")
        if not math_audit["all_matched"]:
            raise ValueError(f"Manual dot product verification failed! Max diff: {math_audit['max_abs_diff']}")

        print("\n  Sample Verification Details (first 5 pairs):")
        print("  " + "-" * 74)
        print("   User     Movie  TrueRating  SparkPred  ManualDot   AbsDiff  Status")
        print("  " + "-" * 74)
        for rec in math_audit["sample_records"][:5]:
            status = "MATCH" if rec["matched"] else "FAIL"
            print(
                f"  {rec['userId']:7d} {rec['movieId']:8d} {rec['true_rating']:11.1f} "
                f"{rec['spark_prediction']:10.4f} {rec['manual_dot']:10.4f} "
                f"{rec['abs_diff']:9.7f}  {status}"
            )
        print("  " + "-" * 74)

        # 7. Diagnostic Training Error (Diagnostic Only)
        print("\n--- [Step 7] Calculating Diagnostic Training Error (Sample: 50,000) ---")
        diag_sample_df = train_df.sample(withReplacement=False, fraction=0.01, seed=42).limit(50000)
        diag = trainer.compute_train_diagnostics(model, diag_sample_df)
        print(f"  Diagnostic Sample Size: {int(diag['sample_count']):,}")
        print(f"  Diagnostic Train RMSE:  {diag['diagnostic_rmse']:.4f}")
        print(f"  Diagnostic Train MAE:   {diag['diagnostic_mae']:.4f}")
        print("  [CAUTION] Train RMSE/MAE is an internal diagnostic check only;")
        print("  it MUST NOT be used to conclude Top-N recommendation superiority.")

        # 8. Model Persistence
        print("\n--- [Step 8] Persisting Model Artifacts ---")
        model_output_dir = get_repo_root() / "artifacts" / "models" / "als" / "m05_spark_als_rank16"
        t_save_start = time.time()
        saved_path = trainer.save_model(
            model=model,
            output_dir=model_output_dir,
            metadata={
                "git_commit": git_commit,
                "dataset_split": "data/processed/splits/train",
                "train_row_count": total_train_rows,
                "user_factor_count": user_audit.count,
                "item_factor_count": item_audit.count,
                "fit_runtime_seconds": t_fit,
                "diagnostic_rmse": diag["diagnostic_rmse"],
                "diagnostic_mae": diag["diagnostic_mae"],
            },
            overwrite=True,
        )
        t_save = time.time() - t_save_start
        print(f"  Model saved to:         {saved_path.resolve()} in {t_save:.2f}s")

        # 9. Model Reload and Prediction Equivalence Verification
        print("\n--- [Step 9] Reloading Model & Verifying Prediction Equivalence ---")
        t_load_model_start = time.time()
        reloaded_model, manifest = ALSTrainer.load_model(saved_path)
        t_load_model = time.time() - t_load_model_start
        print(f"  Reloaded Model in:      {t_load_model:.2f}s | Rank: {reloaded_model.rank}")

        reload_check = trainer.verify_reloaded_model(
            original_model=model,
            reloaded_model=reloaded_model,
            test_df=sample_df,
        )
        print(f"  Reload Check Status:    {'MATCH' if reload_check['matched'] else 'FAIL'}")
        print(f"  Max Prediction Diff:    {reload_check['max_absolute_prediction_diff']:.8f}")
        if not reload_check["matched"]:
            raise ValueError(f"Reloaded model verification failed: {reload_check}")

        # 10. Summary Artifact Export
        pipeline_elapsed = time.time() - pipeline_start
        print(f"\n--- [Step 10] Exporting Execution Results Artifact ---")
        summary = {
            "module": "M05",
            "git_commit": git_commit,
            "status": "M05_ENGINEERING_PASS",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "system_info": {
                "cpu_cores": psutil.cpu_count(logical=True),
                "ram_total_gb": round(vmem.total / (1024**3), 2),
                "python_version": sys.version.split()[0],
                "spark_version": spark.version,
            },
            "timings_seconds": {
                "load_train_split": t_load,
                "als_fit": t_fit,
                "factors_audit": t_audit,
                "model_save": t_save,
                "model_reload": t_load_model,
                "total_pipeline": pipeline_elapsed,
            },
            "dataset_counts": {
                "train_ratings": total_train_rows,
                "distinct_train_users": user_audit.count,
                "distinct_train_movies": item_audit.count,
            },
            "als_configuration": config.to_dict(),
            "factors_audit": {
                "user_factors": user_audit.to_dict(),
                "item_factors": item_audit.to_dict(),
            },
            "mathematical_verification": {
                "samples_verified": math_audit["num_samples"],
                "max_abs_diff": math_audit["max_abs_diff"],
                "mean_abs_diff": math_audit["mean_abs_diff"],
                "tolerance": math_audit["tolerance"],
                "all_matched": math_audit["all_matched"],
            },
            "train_diagnostics": diag,
            "persistence_verification": {
                "model_save_path": str(saved_path.resolve()),
                "reloaded_matched": reload_check["matched"],
                "reloaded_max_diff": reload_check["max_absolute_prediction_diff"],
            },
            "downstream_contract_for_m06": {
                "model_artifact_path": str(saved_path.resolve()),
                "rank": config.rank,
                "user_col": config.user_col,
                "item_col": config.item_col,
                "user_factor_count": user_audit.count,
                "item_factor_count": item_audit.count,
            },
        }

        artifacts_dir = get_repo_root() / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        summary_path = artifacts_dir / "m05_training_results.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"  Summary saved to:       {summary_path.resolve()}")

        print("\n" + "=" * 80)
        print("PIPELINE RESULT: M05_ENGINEERING_PASS")
        print(f"Total Execution Time: {pipeline_elapsed:.2f}s ({pipeline_elapsed/60:.2f} minutes)")
        print("=" * 80)

        return summary

    finally:
        spark.stop()


if __name__ == "__main__":
    run_m05_training_pipeline()
