"""
MoodGraph - Task 3A: Module M01 Real Data Audit Runner
(Kịch bản thực thi kiểm toán dữ liệu MovieLens 25M Parquet thực tế).

Thực thi run_full_m01_audit trên dữ liệu phân vùng Train, Validation và danh mục phim.
In tóm tắt kết quả ra màn hình và lưu báo cáo chi tiết vào artifacts/als/m01_audit_result.json.
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

from recommender.als.data_loader import get_spark_session
from recommender.als.data_audit import run_full_m01_audit

def main():
    root = Path(__file__).resolve().parent.parent
    artifacts_dir = root / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    out_json = artifacts_dir / "m01_audit_result.json"

    print("=== MoodGraph Task 3A: Starting Real Parquet Audit ===")
    spark = get_spark_session("MoodGraph_3A_M01_Real_Audit")
    t0 = time.time()
    
    result = run_full_m01_audit(spark)
    elapsed = time.time() - t0
    result["total_runner_duration_seconds"] = elapsed

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"=== Audit Completed in {elapsed:.2f}s ===")
    print(f"Status: {result['status']}")
    print(f"Train row count: {result['constraints']['total_train_rows']:,}")
    print(f"Distinct users: {result['distribution']['train_known_universe']['num_users']:,}")
    print(f"Distinct train movies: {result['distribution']['train_known_universe']['num_movies']:,}")
    print(f"Catalog movies: {result['distribution']['full_catalog_universe']['num_movies']:,}")
    print(f"Unseen movies in Train: {result['cold_start']['train_unseen_movie_count']:,} ({result['cold_start']['train_unseen_percentage']:.2f}%)")
    print(f"Validation target coverage: {result['cold_start']['validation_all_targets']['coverage_percentage']:.4f}%")
    print(f"Saved full JSON to: {out_json}")

    spark.stop()

if __name__ == "__main__":
    main()
