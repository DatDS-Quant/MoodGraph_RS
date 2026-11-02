"""
MoodGraph - Task 3A: Module M02 Verification Script
(Kịch bản kiểm chứng tích hợp động cơ đánh giá TopNEvaluator trên tập Validation).

Kiểm tra các thuộc tính của phân vùng Validation thực tế và tích hợp TopNEvaluator.
"""

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

from recommender.als.data_loader import get_spark_session, load_validation_data, load_movies_data
from recommender.als.evaluator import TopNEvaluator, HeldOutTarget


def main():
    print("=== MoodGraph Task 3A: Verifying Real Validation Split for M02 ===")
    spark = get_spark_session("MoodGraph_3A_M02_Validation_Verify")
    t0 = time.time()

    val_df = load_validation_data(spark)
    movies_df = load_movies_data(spark)

    total_val_targets = val_df.count()
    distinct_val_users = val_df.select("userId").distinct().count()
    pos_targets = val_df.filter(F.col("rating") >= 3.5).count()
    non_pos_targets = val_df.filter(F.col("rating") < 3.5).count()
    catalog_movie_count = movies_df.select("movieId").distinct().count()

    print(f"Total Validation targets: {total_val_targets:,}")
    print(f"Distinct Validation users: {distinct_val_users:,}")
    print(f"Positive targets (rating >= 3.5): {pos_targets:,} ({pos_targets / total_val_targets * 100:.2f}%)")
    print(f"Non-positive targets (rating < 3.5): {non_pos_targets:,} ({non_pos_targets / total_val_targets * 100:.2f}%)")
    print(f"Movie catalog size: {catalog_movie_count:,}")

    # Pilot integration test: Sample 500 positive users and test evaluator data conversion
    print("\n--- Running Pilot Evaluator Integration Check (500 users) ---")
    pilot_rows = val_df.limit(500).collect()
    targets = {
        row["userId"]: HeldOutTarget(movie_id=row["movieId"], rating=float(row["rating"]))
        for row in pilot_rows
    }

    # Simulate hypothetical dummy predictions where 10% hit rank 1, 10% hit rank 3, 80% miss
    dummy_recs = {}
    for idx, (uid, tgt) in enumerate(targets.items()):
        if idx % 10 == 0:
            dummy_recs[uid] = [tgt.movie_id, 999991, 999992, 999993, 999994]
        elif idx % 10 == 1:
            dummy_recs[uid] = [999991, 999992, tgt.movie_id, 999993, 999994]
        else:
            dummy_recs[uid] = [999991, 999992, 999993, 999994, 999995]

    evaluator = TopNEvaluator(k_list=[5, 10, 20], relevance_threshold=3.5, catalog_size=catalog_movie_count)
    summary = evaluator.evaluate(dummy_recs, targets)

    print(f"Pilot evaluation successful across K={list(summary.keys())}")
    for k, s in summary.items():
        print(f"  K={k:2d}: HR={s.hit_rate:.4f}, NDCG={s.ndcg:.4f}, MRR={s.mrr:.4f}, P={s.precision:.4f}, PosCohort={s.positive_cohort_size}")

    elapsed = time.time() - t0
    print(f"\nVerification finished in {elapsed:.2f}s")
    spark.stop()


if __name__ == "__main__":
    main()
