"""
MoodGraph - Task 3A: Spark ALS
Module M04: Toy ALS Experiment Runner & Verification

This script executes the complete M04 experiment pipeline:
1. Golden Example mathematical derivation & step-by-step verification.
2. Reference ALS solver execution and convergence tracking.
3. PySpark ALS model fitting, factor extraction, and manual dot product audit.
4. Cold-start strategy audit ('nan' vs 'drop').
5. Latent space geometric counterexample (Euclidean vs Dot Product).
6. Export structured JSON artifact to artifacts/m04_toy_als_results.json.
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

if sys.platform.startswith("win"):
    if os.path.exists(r"C:\hadoop"):
        os.environ["HADOOP_HOME"] = r"C:\hadoop"
        os.environ["PATH"] = r"C:\hadoop\bin;" + os.environ.get("PATH", "")
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

from pyspark.sql.types import DoubleType, IntegerType, StructField, StructType

from recommender.als.data_loader import get_repo_root, get_spark_session
from recommender.als.toy_als import (
    TOY_MOVIES,
    TOY_TRAIN_RATINGS,
    TOY_USERS,
    compute_dot_product,
    create_toy_spark_dataframe,
    demonstrate_cold_start_difference,
    extract_factors,
    fit_spark_toy_als,
    run_toy_als_reference,
    verify_euclidean_vs_dot_product_counterexample,
    verify_golden_example_step,
    verify_spark_vs_manual_dot,
)


def run_m04_pipeline() -> Dict[str, Any]:
    print("=" * 80)
    print("MOODGRAPH TASK 3A - MODULE M04: TOY ALS & LATENT FACTOR INSPECTION")
    print("=" * 80)

    start_time = time.time()
    results: Dict[str, Any] = {
        "module": "M04",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    # --------------------------------------------------------------------------
    # 1. Golden Example Step-by-Step Verification
    # --------------------------------------------------------------------------
    print("\n--- [Step 1] Golden Example Step-by-Step Verification ---")
    golden_res = verify_golden_example_step()
    print(f"  User An (u1) factor:    p_An        = {golden_res['p_An']:.4f} (Expected: 2.0000)")
    print(f"  User Binh (u2) factor:  p_Binh      = {golden_res['p_Binh']:.4f} (Expected: 1.0000)")
    print(f"  Movie C (m103) updated: q_C_updated = {golden_res['q_C_updated']:.4f} (Expected: 1.5000)")
    print(f"  Predicted An on C:      r_hat_An_C  = {golden_res['pred_An_on_C']:.4f} (Expected: 3.0000)")
    results["golden_example"] = golden_res

    # --------------------------------------------------------------------------
    # 2. Pure Python Reference ALS Solver Convergence
    # --------------------------------------------------------------------------
    print("\n--- [Step 2] Pure Python Reference ALS Solver (Rank=2, reg=0.01) ---")
    ref_u_factors, ref_i_factors, loss_history = run_toy_als_reference(
        ratings=TOY_TRAIN_RATINGS,
        rank=2,
        max_iter=15,
        reg_param=0.01,
        seed=42,
    )
    print(f"  Initial Loss: {loss_history[0]:.6f}")
    print(f"  Iter 1  Loss: {loss_history[1]:.6f}")
    print(f"  Iter 5  Loss: {loss_history[5]:.6f}")
    print(f"  Iter 10 Loss: {loss_history[10]:.6f}")
    print(f"  Iter 15 Loss: {loss_history[-1]:.6f}")
    print(f"  Loss reduction: {((loss_history[0] - loss_history[-1]) / loss_history[0]) * 100:.2f}%")
    results["reference_solver"] = {
        "initial_loss": loss_history[0],
        "final_loss": loss_history[-1],
        "loss_history": loss_history,
    }

    # --------------------------------------------------------------------------
    # 3. PySpark ALS Fit & Manual Dot Product Audit
    # --------------------------------------------------------------------------
    print("\n--- [Step 3] PySpark ALS Fit & Manual Dot Product Audit ---")
    spark = get_spark_session(
        app_name="MoodGraph_M04_ToyALS",
        master="local[2]",
        driver_memory="2g",
        shuffle_partitions=2,
    )

    try:
        spark_df = create_toy_spark_dataframe(spark, TOY_TRAIN_RATINGS)
        rank = 2
        reg_param = 0.05
        max_iter = 15
        seed = 42

        model = fit_spark_toy_als(
            spark_df=spark_df,
            rank=rank,
            max_iter=max_iter,
            reg_param=reg_param,
            seed=seed,
            cold_start_strategy="nan",
        )

        user_factors, item_factors = extract_factors(model)
        print(f"\n  Extracted {len(user_factors)} User Factors (rank={rank}):")
        for u_id, vec in sorted(user_factors.items()):
            name = TOY_USERS.get(u_id, {}).get("name", "Unknown")
            vec_str = ", ".join(f"{v:+.4f}" for v in vec)
            print(f"    User {u_id:2d} ({name:10s}): [{vec_str}]")

        print(f"\n  Extracted {len(item_factors)} Item Factors (rank={rank}):")
        for m_id, vec in sorted(item_factors.items()):
            title = TOY_MOVIES.get(m_id, {}).get("title", "Unknown")
            vec_str = ", ".join(f"{v:+.4f}" for v in vec)
            print(f"    Movie {m_id:3d} ({title:10s}): [{vec_str}]")

        # Detailed verification table
        audit_res = verify_spark_vs_manual_dot(model, spark_df, tolerance=1e-4)
        print(f"\n  PySpark transform vs Manual Dot Product Audit:")
        print(f"    Samples checked:     {audit_res['num_samples']}")
        print(f"    Max Absolute Diff:   {audit_res['max_abs_diff']:.8f}")
        print(f"    Mean Absolute Diff:  {audit_res['mean_abs_diff']:.8f}")
        print(f"    All Matched (<=1e-4):{audit_res['all_matched']}")

        print("\n  Sample Prediction Comparison (first 8 ratings):")
        print("  " + "-" * 72)
        print("  User Movie TrueRating SparkPred ManualDot  AbsDiff  Status")
        print("  " + "-" * 72)
        for d in audit_res["details"][:8]:
            status = "MATCH" if d["matched"] else "FAIL"
            print(
                f"  {d['userId']:4d} {d['movieId']:5d} {d['true_rating']:10.1f} "
                f"{d['spark_prediction']:9.4f} {d['manual_dot']:9.4f} "
                f"{d['abs_diff']:8.6f}  {status}"
            )
        print("  " + "-" * 72)

        results["spark_audit"] = {
            "rank": rank,
            "reg_param": reg_param,
            "max_iter": max_iter,
            "seed": seed,
            "num_user_factors": len(user_factors),
            "num_item_factors": len(item_factors),
            "max_abs_diff": audit_res["max_abs_diff"],
            "mean_abs_diff": audit_res["mean_abs_diff"],
            "all_matched": audit_res["all_matched"],
            "user_factors": {str(k): v.tolist() for k, v in user_factors.items()},
            "item_factors": {str(k): v.tolist() for k, v in item_factors.items()},
            "prediction_comparison": audit_res["details"],
        }

        # ----------------------------------------------------------------------
        # 4. Cold-Start Audit: 'nan' vs 'drop'
        # ----------------------------------------------------------------------
        print("\n--- [Step 4] Cold-Start Strategy Audit: 'nan' vs 'drop' ---")
        model_drop = fit_spark_toy_als(
            spark_df=spark_df,
            rank=rank,
            max_iter=max_iter,
            reg_param=reg_param,
            seed=seed,
            cold_start_strategy="drop",
        )

        cold_schema = StructType([
            StructField("userId", IntegerType(), nullable=False),
            StructField("movieId", IntegerType(), nullable=False),
            StructField("rating", DoubleType(), nullable=False),
        ])
        cold_test_rows = [
            (1, 101, 2.0),   # warm / warm
            (999, 101, 4.0), # cold user (999) / warm movie
            (1, 999, 3.5),   # warm user / cold movie (999)
            (999, 999, 5.0), # cold user / cold movie
        ]
        cold_df = spark.createDataFrame(cold_test_rows, schema=cold_schema)
        cold_audit = demonstrate_cold_start_difference(model, model_drop, cold_df)

        print(f"  Input Test Rows:             {cold_audit['input_row_count']}")
        print(f"  Rows preserved under 'nan':  {cold_audit['nan_strategy_output_count']}")
        print(f"  Unscorable count under 'nan':{cold_audit['nan_strategy_unscorable_count']}")
        print(f"  Rows preserved under 'drop': {cold_audit['drop_strategy_output_count']}")
        print(f"  Silent dropped count:        {cold_audit['dropped_rows_count']}")
        print(f"\n  CRITICAL EVALUATION FINDING:\n  {cold_audit['evaluation_implication']}")
        results["cold_start_audit"] = cold_audit

        # ----------------------------------------------------------------------
        # 5. Latent Space Geometric Counterexample
        # ----------------------------------------------------------------------
        print("\n--- [Step 5] Latent Factor Geometry: Euclidean vs Dot Product ---")
        geo_proof = verify_euclidean_vs_dot_product_counterexample()
        print(f"  User vector p_u:  {geo_proof['p_u']}")
        print(f"  Item 1 vector q_1: {geo_proof['q_1']}")
        print(f"  Item 2 vector q_2: {geo_proof['q_2']}")
        print(f"  Euclidean distance to Item 1: {geo_proof['euclidean_dist_item1']:.4f}")
        print(f"  Euclidean distance to Item 2: {geo_proof['euclidean_dist_item2']:.4f}")
        print(f"  Dot product with Item 1:      {geo_proof['dot_product_item1']:.4f}")
        print(f"  Dot product with Item 2:      {geo_proof['dot_product_item2']:.4f}")
        print(f"  Proof Valid:                  {geo_proof['is_counterexample_valid']}")
        print(f"\n  GEOMETRIC INSIGHT:\n  {geo_proof['explanation']}")
        results["geometric_counterexample"] = geo_proof

    finally:
        spark.stop()

    elapsed = time.time() - start_time
    results["elapsed_seconds"] = elapsed
    print(f"\nPipeline completed in {elapsed:.2f} seconds.")

    # --------------------------------------------------------------------------
    # 6. Save Artifact
    # --------------------------------------------------------------------------
    artifacts_dir = get_repo_root() / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifacts_dir / "m04_toy_als_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Results saved to: {out_path.resolve()}")

    return results


if __name__ == "__main__":
    run_m04_pipeline()
