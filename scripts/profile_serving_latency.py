#!/usr/bin/env python3
"""
MoodGraph Phase 4 Hardening: Comprehensive Latency & Serving Profiler.
Đo lường độc lập, chi tiết từng thành phần của pipeline gợi ý:
1. Model/artifact loading
2. ALS candidate generation
3. KG candidate generation
4. Candidate union
5. Fusion (RRF vs Weighted)
6. Metadata/evidence enrichment
7. Response serialization
8. Complete API request (Cold vs Warm)
9. Load test đo thông lượng thực tế (Throughput RPS)
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from recommender.als.delivery import get_delivery_service
from recommender.kg.config import load_kg_config
from recommender.kg.data_access import DataAccess
from recommender.kg.import_graph import InMemoryGraph, import_pilot_data
from recommender.kg.recommend import recommend_kg
from recommender.hybrid.engine import HybridRecommenderService
from recommender.hybrid.config import HybridConfig
from recommender.hybrid.fusion import reciprocal_rank_fusion, weighted_score_fusion
from recommender.hybrid.api import app, set_api_service
from starlette.testclient import TestClient


def run_latency_profiling():
    print("=" * 80)
    print("MOODGRAPH PHASE 4: SERVING LATENCY & COMPONENT PROFILING")
    print("=" * 80)

    results: Dict[str, Any] = {}

    # 1. Model / Artifact Loading
    print("\n[1] Đo thời gian nạp Model / Artifacts...")
    t0 = time.perf_counter()
    als_service = get_delivery_service()
    als_load_time = time.perf_counter() - t0
    print(f"  -> ALS Delivery Service load: {als_load_time * 1000:.2f} ms")

    cfg = load_kg_config()
    da = DataAccess(cfg.data_root)
    g = InMemoryGraph()
    t0 = time.perf_counter()
    import_pilot_data(g, da, set(range(1, 101)), top_m=20, batch_size=5000)
    kg_load_time = time.perf_counter() - t0
    print(f"  -> KG Pilot Graph (100 users, 62k movies, 73k edges) load: {kg_load_time * 1000:.2f} ms")

    results["loading"] = {
        "als_load_ms": round(als_load_time * 1000, 2),
        "kg_load_ms": round(kg_load_time * 1000, 2),
    }

    # 2. ALS Candidate Generation
    print("\n[2] Đo thời gian sinh ứng viên ALS (Top-50)...")
    als_latencies = []
    for uid in range(1, 31):
        t0 = time.perf_counter()
        _ = als_service.recommend(user_id=uid, top_n=50)
        als_latencies.append((time.perf_counter() - t0) * 1000)
    
    als_mean = statistics.mean(als_latencies)
    als_p95 = statistics.quantiles(als_latencies, n=20)[18] if len(als_latencies) >= 20 else max(als_latencies)
    print(f"  -> ALS: Mean = {als_mean:.3f} ms, P95 = {als_p95:.3f} ms")
    results["als_candidate_generation_ms"] = {"mean": round(als_mean, 3), "p95": round(als_p95, 3)}

    # 3. KG Candidate Generation
    print("\n[3] Đo thời gian sinh ứng viên KG (Top-50 Cold Traversal)...")
    kg_latencies = []
    for uid in range(1, 11):
        t0 = time.perf_counter()
        _ = recommend_kg(user_id=uid, top_n=50, graph=g)
        kg_latencies.append((time.perf_counter() - t0) * 1000)
    
    kg_mean = statistics.mean(kg_latencies)
    kg_p95 = statistics.quantiles(kg_latencies, n=20)[18] if len(kg_latencies) >= 20 else max(kg_latencies)
    print(f"  -> KG: Mean = {kg_mean:.2f} ms, P95 = {kg_p95:.2f} ms")
    results["kg_candidate_generation_ms"] = {"mean": round(kg_mean, 2), "p95": round(kg_p95, 2)}

    # Chuẩn bị candidate samples để đo các bước tiếp theo
    sample_als = als_service.recommend(user_id=1, top_n=50)
    sample_kg = recommend_kg(user_id=1, top_n=50, graph=g)

    # 4. Candidate Union
    print("\n[4] Đo thời gian Hợp nhất Ứng viên (Candidate Union)...")
    union_latencies = []
    for _ in range(500):
        t0 = time.perf_counter()
        _ = set(int(c["movieId"]) for c in sample_als) | set(int(c["movieId"]) for c in sample_kg)
        union_latencies.append((time.perf_counter() - t0) * 1000)
    union_mean = statistics.mean(union_latencies)
    print(f"  -> Candidate Union: Mean = {union_mean:.4f} ms")
    results["candidate_union_ms"] = round(union_mean, 4)

    # 5. Fusion Algorithms
    print("\n[5] Đo thời gian Thuật toán Dung hợp (Fusion Overhead)...")
    rrf_latencies = []
    for _ in range(500):
        t0 = time.perf_counter()
        _ = reciprocal_rank_fusion(sample_als, sample_kg, rrf_k=60, top_n=10)
        rrf_latencies.append((time.perf_counter() - t0) * 1000)
    rrf_mean = statistics.mean(rrf_latencies)

    weighted_latencies = []
    for _ in range(500):
        t0 = time.perf_counter()
        _ = weighted_score_fusion(sample_als, sample_kg, weight_als=0.5, weight_kg=0.5, top_n=10)
        weighted_latencies.append((time.perf_counter() - t0) * 1000)
    weighted_mean = statistics.mean(weighted_latencies)
    print(f"  -> RRF Fusion (Top-10): Mean = {rrf_mean:.4f} ms")
    print(f"  -> Weighted Fusion (Top-10): Mean = {weighted_mean:.4f} ms")
    results["fusion_overhead_ms"] = {"rrf_mean": round(rrf_mean, 4), "weighted_mean": round(weighted_mean, 4)}

    # 6. Metadata / Evidence Enrichment & Serialization
    print("\n[6] Đo thời gian Đóng gói & Serialization...")
    hybrid_service = HybridRecommenderService(als_service=als_service, kg_graph=g, config=HybridConfig(cache_enabled=False))
    resp = hybrid_service.recommend(user_id=1, top_n=10, use_cache=False)
    
    ser_latencies = []
    for _ in range(500):
        t0 = time.perf_counter()
        _ = json.dumps(resp.to_dict())
        ser_latencies.append((time.perf_counter() - t0) * 1000)
    ser_mean = statistics.mean(ser_latencies)
    print(f"  -> JSON Serialization: Mean = {ser_mean:.4f} ms")
    results["serialization_ms"] = round(ser_mean, 4)

    # 7. Complete API Request (Cold vs Warm)
    print("\n[7] Đo thời gian End-to-End API Request (Starlette TestClient)...")
    cached_service = HybridRecommenderService(als_service=als_service, kg_graph=g, config=HybridConfig(cache_enabled=True))
    set_api_service(cached_service)
    client = TestClient(app)

    # Cold request (Cache miss)
    t0 = time.perf_counter()
    resp_cold = client.get("/api/recommendations/2?top_n=10&use_cache=true")
    api_cold_latency = (time.perf_counter() - t0) * 1000
    assert resp_cold.status_code == 200
    assert resp_cold.json()["metadata"]["cache_hit"] is False
    print(f"  -> End-to-End API Cold (Cache Miss): {api_cold_latency:.2f} ms")

    # Warm requests (Cache hit)
    warm_latencies = []
    for _ in range(100):
        t0 = time.perf_counter()
        resp_warm = client.get("/api/recommendations/2?top_n=10&use_cache=true")
        warm_latencies.append((time.perf_counter() - t0) * 1000)
        assert resp_warm.status_code == 200
        assert resp_warm.json()["metadata"]["cache_hit"] is True

    warm_p50 = statistics.median(warm_latencies)
    warm_p90 = statistics.quantiles(warm_latencies, n=10)[8]
    warm_p95 = statistics.quantiles(warm_latencies, n=20)[18]
    warm_p99 = statistics.quantiles(warm_latencies, n=100)[98]
    print(f"  -> End-to-End API Warm (Cache Hit): P50 = {warm_p50:.3f} ms, P95 = {warm_p95:.3f} ms, P99 = {warm_p99:.3f} ms")

    results["api_latency_ms"] = {
        "cold_p95": round(api_cold_latency, 2),
        "warm_p50": round(warm_p50, 3),
        "warm_p90": round(warm_p90, 3),
        "warm_p95": round(warm_p95, 3),
        "warm_p99": round(warm_p99, 3),
    }

    # 8. Load Test Throughput (RPS)
    print("\n[8] Thực thi Load Test đo thông lượng thực tế (Warm Serving)...")
    load_iterations = 2000
    t_start = time.perf_counter()
    for _ in range(load_iterations):
        _ = client.get("/api/recommendations/2?top_n=10&use_cache=true")
    load_duration = time.perf_counter() - t_start
    rps = load_iterations / load_duration
    print(f"  -> Thực hiện {load_iterations} requests trong {load_duration:.3f}s")
    print(f"  -> Thông lượng phục vụ đạt: {rps:.1f} Requests/giây (RPS)")
    results["throughput_rps"] = round(rps, 1)

    out_file = PROJECT_ROOT / "docs" / "phase4" / "hardening_latency_profile.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n[OK] Đã lưu kết quả đo đạc vào: {out_file}")

    return results


if __name__ == "__main__":
    run_latency_profiling()
