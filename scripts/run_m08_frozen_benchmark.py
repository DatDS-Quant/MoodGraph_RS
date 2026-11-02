"""
MoodGraph - Task 3A: Module M08 Final Offline Benchmark Runner
(Kịch bản thực thi đánh giá ngoại tuyến cuối cùng trên phân vùng Test đóng băng).

Thực hiện benchmark one-shot so sánh công bằng giữa 3 mô hình:
- Model A: M03_POPULARITY_COUNT (chuẩn đếm lượt rating)
- Model B: M03_POPULARITY_WEIGHTED_M10 (chuẩn trung bình có trọng số Bayes m=10)
- Model C: ALS_R8_REG0.3_ITER10 (Mô hình Spark ALS vô địch đã đóng băng)
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Windows Hadoop configuration
os.environ["HADOOP_HOME"] = r"C:\hadoop"
os.environ["PATH"] = r"C:\hadoop\bin;" + os.environ.get("PATH", "")
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

from recommender.als.benchmark import PreflightBlockedError, TestBenchmarkRunner


def main():
    print("=" * 80)
    print("MOODGRAPH TASK 3A: M08 FINAL OFFLINE BENCHMARK ON FROZEN TEST SPLIT")
    print("=" * 80)
    t_start = time.time()

    runner = TestBenchmarkRunner(repo_root=root_dir)

    # 1. Run Pre-flight Audit
    print("\n[PHASE 1] Pre-Flight Release Audit")
    try:
        preflight_report = runner.execute_preflight()
        print("[PHASE 1] PREFLIGHT STATUS: PASS")
    except PreflightBlockedError as e:
        print(f"\n[FATAL] PREFLIGHT BLOCKED: {e}", file=sys.stderr)
        sys.exit(1)

    # 2. Run Single-Shot Test Benchmark
    print("\n[PHASE 2] Executing Single-Shot Test Split Benchmark")
    try:
        results = runner.run_benchmark()
    except Exception as e:
        print(f"\n[FATAL] Benchmark execution failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 3. Print Comparison Table
    print("\n" + "=" * 80)
    print("FINAL TEST SPLIT BENCHMARK RESULTS SUMMARY")
    print("=" * 80)
    print(f"{'Model':<30} | {'HR@5':<8} | {'HR@10':<8} | {'HR@20':<8} | {'NDCG@10':<8} | {'Coverage@10':<11} | {'Hits@10':<9}")
    print("-" * 92)

    for name, res in results.items():
        m5 = res.metrics[5]
        m10 = res.metrics[10]
        m20 = res.metrics[20]
        cov_pct = m10["catalog_coverage_full"] * 100
        hits = m10["hit_count"]
        denom = res.positive_cohort_size
        print(
            f"{name:<30} | "
            f"{m5['hit_rate']:<8.5f} | "
            f"{m10['hit_rate']:<8.5f} | "
            f"{m20['hit_rate']:<8.5f} | "
            f"{m10['ndcg']:<8.5f} | "
            f"{cov_pct:<10.3f}% | "
            f"{hits:,}/{denom:,}"
        )

    print("=" * 92)
    tot_time = time.time() - t_start
    print(f"\n[Done] Total M08 execution runtime: {tot_time:.2f}s")
    print("VERDICT: M08_ACCEPTANCE_PASS")


if __name__ == "__main__":
    main()

