#!/usr/bin/env python3
"""
MoodGraph Task 3B: Gate 3 Pilot Scaling Benchmark & RAM Safety Guard

Đo đạc thực nghiệm các mốc quy mô tăng dần:
100 users -> 500 users -> 1,000 users -> (kiểm tra an toàn RAM trước khi mở rộng tiếp).

Chỉ số thu thập:
- Số train ratings nạp
- Nodes & Edges thật
- Import duration (s)
- Peak RSS RAM (MB)
- Import throughput (records/s)
- Recommendation latency (ms/user)
"""

import sys
import os
import time
import json
import gc
import psutil
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple

# Project root setup
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Windows console UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from recommender.kg.config import load_kg_config
from recommender.kg.data_access import DataAccess
from recommender.kg.import_graph import InMemoryGraph, import_pilot_data
from recommender.kg.recommend import recommend_kg


def get_system_memory_status() -> Dict[str, float]:
    """Lấy thông số bộ nhớ hệ thống và tiến trình hiện tại (MB)."""
    vm = psutil.virtual_memory()
    proc = psutil.Process()
    return {
        "system_total_mb": round(vm.total / (1024 * 1024), 1),
        "system_available_mb": round(vm.available / (1024 * 1024), 1),
        "system_percent_used": vm.percent,
        "process_rss_mb": round(proc.memory_info().rss / (1024 * 1024), 1)
    }


def benchmark_scale_tier(
    num_users: int,
    top_m: int = 20,
    latency_sample_size: int = 10
) -> Dict[str, Any]:
    """Đo đạc toàn diện một mốc quy mô người dùng."""
    config = load_kg_config()
    data_access = DataAccess(config.data_root)
    cohort = set(range(1, num_users + 1))

    # Thu dọn rác trước khi nạp
    gc.collect()
    mem_before = get_system_memory_status()

    t_start = time.time()
    graph = InMemoryGraph()
    counts = import_pilot_data(
        graph=graph,
        data_access=data_access,
        user_cohort=cohort,
        top_m=top_m,
        batch_size=config.batch_size
    )
    import_duration = time.time() - t_start

    mem_after = get_system_memory_status()
    proc_rss_mb = mem_after["process_rss_mb"]

    total_records = (
        counts["users"] + counts["movies"] + counts["genres"] + counts["genome_tags"] +
        counts["rated_edges"] + counts["in_genre_edges"] + counts["has_genome_tag_edges"]
    )
    throughput = round(total_records / import_duration, 1) if import_duration > 0 else 0.0

    # Đo độ trễ gợi ý trung bình trên tập mẫu (ms/user)
    latencies = []
    test_uids = list(cohort)[:latency_sample_size]
    for uid in test_uids:
        t0 = time.time()
        recs = recommend_kg(user_id=uid, top_n=20, graph=graph)
        latencies.append((time.time() - t0) * 1000.0)

    avg_latency_ms = round(sum(latencies) / len(latencies), 1) if latencies else 0.0

    tier_result = {
        "num_users": num_users,
        "top_m": top_m,
        "import_duration_s": round(import_duration, 2),
        "import_throughput_records_s": throughput,
        "process_peak_rss_mb": proc_rss_mb,
        "memory_consumed_mb": round(proc_rss_mb - mem_before["process_rss_mb"], 1),
        "system_available_ram_mb": mem_after["system_available_mb"],
        "system_ram_used_pct": mem_after["system_percent_used"],
        "avg_recommendation_latency_ms": avg_latency_ms,
        "nodes": {
            "users": counts["users"],
            "movies": counts["movies"],
            "genres": counts["genres"],
            "genome_tags": counts["genome_tags"],
            "total_nodes": counts["users"] + counts["movies"] + counts["genres"] + counts["genome_tags"]
        },
        "edges": {
            "rated": counts["rated_edges"],
            "in_genre": counts["in_genre_edges"],
            "has_genome_tag": counts["has_genome_tag_edges"],
            "total_edges": counts["rated_edges"] + counts["in_genre_edges"] + counts["has_genome_tag_edges"]
        }
    }

    # Giải phóng đồ thị của mốc hiện tại
    del graph
    gc.collect()

    return tier_result


def run_scaling_pipeline():
    print("=" * 80)
    print("MOODGRAPH TASK 3B: GATE 3 PILOT SCALING & RESOURCE BENCHMARK")
    print("=" * 80)

    # Danh sách các mốc quy mô dự kiến
    target_tiers = [100, 500, 1000, 2000, 5000]
    results = []

    # Ngưỡng an toàn RAM tối thiểu khả dụng (nếu RAM còn trống dưới 450MB -> Dừng an toàn)
    MIN_SAFE_AVAILABLE_RAM_MB = 450.0

    for tier in target_tiers:
        mem_status = get_system_memory_status()
        print(f"\n[KIỂM TRA AN TOÀN RAM TRƯỚC MỐC {tier} USERS]:")
        print(f"  - RAM hệ thống khả dụng: {mem_status['system_available_mb']} MB ({100 - mem_status['system_percent_used']:.1f}% trống)")
        print(f"  - Tiến trình hiện tại  : {mem_status['process_rss_mb']} MB")

        # Cơ chế RAM Safety Guard
        if mem_status["system_available_mb"] < MIN_SAFE_AVAILABLE_RAM_MB:
            print(f"[CẢNH BÁO RAM SAFETY GUARD]: RAM khả dụng ({mem_status['system_available_mb']} MB) thấp hơn ngưỡng an toàn ({MIN_SAFE_AVAILABLE_RAM_MB} MB).")
            print(f"[DỪNG AN TOÀN]: Hoàn thành ở mốc tối đa an toàn đã đạt được để ngăn ngừa OOM.")
            break

        print(f"[*] Đang thực thi benchmark mốc {tier} users...")
        try:
            tier_res = benchmark_scale_tier(num_users=tier, top_m=20, latency_sample_size=10)
            results.append(tier_res)
            print(f"  [OK] Hoàn tất mốc {tier} users:")
            print(f"    - Thời gian nạp : {tier_res['import_duration_s']}s (Thông lượng: {tier_res['import_throughput_records_s']} records/s)")
            print(f"    - Nodes / Edges : {tier_res['nodes']['total_nodes']:,} nodes / {tier_res['edges']['total_edges']:,} edges")
            print(f"    - Train Ratings : {tier_res['edges']['rated']:,} ratings")
            print(f"    - Genome Edges  : {tier_res['edges']['has_genome_tag']:,} edges (Top-20)")
            print(f"    - Peak RSS RAM  : {tier_res['process_peak_rss_mb']} MB (RAM còn trống: {tier_res['system_available_ram_mb']} MB)")
            print(f"    - Latency TB    : {tier_res['avg_recommendation_latency_ms']} ms/user")
        except Exception as exc:
            print(f"[LỖI TẠI MỐC {tier}]: {exc}")
            break

    # Lưu kết quả thực nghiệm ra file JSON
    out_file = PROJECT_ROOT / "docs/kg/scaling_benchmark_results.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 80)
    print(f"[HOÀN THÀNH]: Đã ghi nhận toàn bộ số liệu thực nghiệm vào: {out_file}")
    print("=" * 80)


if __name__ == "__main__":
    run_scaling_pipeline()

