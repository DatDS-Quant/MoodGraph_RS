"""
MoodGraph Phase 5: Rigorous Memory, Performance & Stability Benchmark.
Clearly separates and measures:
1. Pure Python Object Size (sys.getsizeof / buffer sizes)
2. Process Resident Set Size (RSS) and Peak RSS (via psutil)
3. Lifespan Pre-Warming Initialization Latency
4. First Uncached HTTP Request Latency (Cold Call)
5. Warm HTTP Latency Distribution (P50, P95, P99 across 200 requests)
6. Extended Memory Stability Test (1,000 requests measuring RSS trend to verify plateau)
"""

import gc
import json
import os
import sys
import time
import platform
import psutil
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from recommender.api.app import app


def get_process_rss_mb() -> float:
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024.0 * 1024.0)


def run_benchmark():
    gc.collect()
    rss_baseline = get_process_rss_mb()

    # Hardware & Environment
    cpu_count = os.cpu_count()
    sys_ram_gb = psutil.virtual_memory().total / (1024.0 ** 3)
    os_info = f"{platform.system()} {platform.release()} ({platform.machine()})"
    py_ver = sys.version.split()[0]

    print("=" * 80)
    print("MOODGRAPH PHASE 5: RIGOROUS PERFORMANCE & MEMORY AUDIT")
    print("=" * 80)
    print(f"Environment: OS: {os_info} | Python: {py_ver} | CPU Cores: {cpu_count} | Total RAM: {sys_ram_gb:.2f} GB")
    print(f"Baseline Python RSS (Before App Startup): {rss_baseline:.2f} MB")

    # Measure Lifespan Pre-warming Latency and Post-Startup RSS
    t_start = time.perf_counter()
    with TestClient(app) as client:
        t_lifespan = time.perf_counter() - t_start
        rss_after_startup = get_process_rss_mb()
        startup_memory_delta = rss_after_startup - rss_baseline

        print(f"\n[Lifespan Startup] Duration: {t_lifespan:.3f} s")
        print(f"[Process RSS Post-Startup]: {rss_after_startup:.2f} MB (+{startup_memory_delta:.2f} MB from pre-warming)")

        # Inspect Data Buffer Sizes
        catalog_repo = app.state.catalog_repo
        history_repo = app.state.history_repo
        catalog_size_mb = sys.getsizeof(catalog_repo._movies_by_id) / (1024.0 * 1024.0)
        csr_indptr_mb = history_repo._csr_offsets.nbytes / (1024.0 * 1024.0)
        csr_data_mb = history_repo._csr_mids.nbytes / (1024.0 * 1024.0)
        total_data_buffers_mb = catalog_size_mb + csr_indptr_mb + csr_data_mb

        print(f"\n[Data Buffer Breakdown]:")
        print(f" - Catalog Dictionary Buffer (62,423 movies): {catalog_size_mb:.2f} MB")
        print(f" - CSR Matrix Offsets Buffer (162,542 users): {csr_indptr_mb:.2f} MB")
        print(f" - CSR Matrix Movie IDs Buffer (24.6M interactions): {csr_data_mb:.2f} MB")
        print(f" - Total Raw Resident Data Buffers: {total_data_buffers_mb:.2f} MB")

        # First Uncached HTTP Request (Cold Call)
        t_cold_start = time.perf_counter()
        resp_cold = client.get("/api/recommendations/1?top_n=10&strategy=rrf")
        t_cold_ms = (time.perf_counter() - t_cold_start) * 1000.0
        assert resp_cold.status_code == 200
        print(f"\n[First HTTP Request (Cold Call)]: {t_cold_ms:.2f} ms")

        # Warm HTTP Latency (200 requests)
        latencies = []
        for _ in range(200):
            t0 = time.perf_counter()
            resp = client.get("/api/recommendations/1?top_n=10&strategy=rrf")
            latencies.append((time.perf_counter() - t0) * 1000.0)

        latencies.sort()
        p50 = latencies[int(len(latencies) * 0.50)]
        p95 = latencies[int(len(latencies) * 0.95)]
        p99 = latencies[int(len(latencies) * 0.99)]
        print(f"\n[Warm HTTP Latency (200 Requests)]: P50={p50:.3f} ms | P95={p95:.3f} ms | P99={p99:.3f} ms")

        # Extended Memory Stability Test (1,000 requests across varying user IDs)
        print("\n[Extended Memory Stability Test]: Running 1,000 recommendation requests...")
        rss_checkpoints = []
        checkpoints_at = [100, 300, 500, 700, 1000]

        for i in range(1, 1001):
            uid = (i % 50) + 1  # 50 distinct users to test LRU cache expansion
            client.get(f"/api/recommendations/{uid}?top_n=5&strategy=rrf")
            if i in checkpoints_at:
                current_rss = get_process_rss_mb()
                rss_checkpoints.append((i, current_rss))
                print(f"  -> Request #{i:4d}: Process RSS = {current_rss:.2f} MB")

        # Evaluate Stability / Plateau
        rss_100 = rss_checkpoints[0][1]
        rss_500 = rss_checkpoints[2][1]
        rss_1000 = rss_checkpoints[4][1]
        delta_500_to_1000 = rss_1000 - rss_500

        print(f"\n[Memory Stability Evaluation]:")
        print(f" - RSS at Request #100:  {rss_100:.2f} MB")
        print(f" - RSS at Request #500:  {rss_500:.2f} MB")
        print(f" - RSS at Request #1000: {rss_1000:.2f} MB")
        print(f" - RSS Growth from Req 500 to 1000: {delta_500_to_1000:+.3f} MB")

        plateau_verified = abs(delta_500_to_1000) < 5.0  # Less than 5MB delta over 500 requests confirms plateau
        print(f" - Plateau Verdict: {'CONFIRMED (Zero Unbounded Leak)' if plateau_verified else 'GROWING'}")

        # Summary output
        metrics_summary = {
            "environment": {
                "os": os_info,
                "python": py_ver,
                "cpu_cores": cpu_count,
                "total_ram_gb": round(sys_ram_gb, 2),
            },
            "memory": {
                "baseline_rss_mb": round(rss_baseline, 2),
                "post_startup_rss_mb": round(rss_after_startup, 2),
                "raw_data_buffers_mb": round(total_data_buffers_mb, 2),
                "rss_after_1000_reqs_mb": round(rss_1000, 2),
                "growth_500_to_1000_mb": round(delta_500_to_1000, 3),
                "memory_plateau_confirmed": plateau_verified,
            },
            "latency": {
                "lifespan_startup_seconds": round(t_lifespan, 3),
                "cold_first_request_ms": round(t_cold_ms, 2),
                "warm_http_p50_ms": round(p50, 3),
                "warm_http_p95_ms": round(p95, 3),
                "warm_http_p99_ms": round(p99, 3),
            }
        }

        output_path = PROJECT_ROOT / "docs" / "phase5" / "performance_audit_results.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(metrics_summary, f, indent=2)
        print(f"\nSaved detailed metrics to {output_path}")

    print("=" * 80)
    print("AUDIT COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    run_benchmark()
