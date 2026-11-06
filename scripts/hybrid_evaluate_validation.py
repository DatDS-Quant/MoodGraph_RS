#!/usr/bin/env python3
"""
MoodGraph Phase 4: Offline Validation Benchmark Script (Optimized Pipeline).
Đánh giá so sánh thực nghiệm độc lập trên tập Validation (100 users, 71 positive users):
1. Popularity Count Baseline
2. Spark ALS Champion (ALS_R8_REG0.3_ITER10)
3. Knowledge Graph Path-based (P1+P2+P3)
4. Hybrid RRF (k=60)
5. Hybrid Weighted Score Fusion (Grid search w_ALS in [0.1, 0.3, 0.5, 0.7, 0.9])

Tuân thủ nghiêm ngặt giao thức Leave-1-Last (docs/evaluation_protocol.md):
- Tập mẫu số đánh giá = positive cohort (val rating >= 3.5).
- Lọc lịch sử đã xem trong Train, KHÔNG lọc mục tiêu ground-truth trong Validation.
- Sinh ứng viên 1 lần (Single-pass Candidate Generation) để tối ưu hóa thời gian tính toán.
"""

from __future__ import annotations

import json
import math
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import pyarrow.dataset as ds

from recommender.als.delivery import get_delivery_service
from recommender.kg.config import load_kg_config
from recommender.kg.data_access import DataAccess
from recommender.kg.import_graph import InMemoryGraph, import_pilot_data
from recommender.kg.recommend import recommend_kg
from recommender.hybrid.fusion import reciprocal_rank_fusion, weighted_score_fusion


def compute_ndcg_at_k(target_movie_id: int, rec_movie_ids: List[int], k: int) -> float:
    top_k = rec_movie_ids[:k]
    if target_movie_id in top_k:
        rank = top_k.index(target_movie_id) + 1
        return 1.0 / math.log2(rank + 1)
    return 0.0


def compute_hr_at_k(target_movie_id: int, rec_movie_ids: List[int], k: int) -> float:
    return 1.0 if target_movie_id in rec_movie_ids[:k] else 0.0


def compute_mrr_at_k(target_movie_id: int, rec_movie_ids: List[int], k: int) -> float:
    top_k = rec_movie_ids[:k]
    if target_movie_id in top_k:
        rank = top_k.index(target_movie_id) + 1
        return 1.0 / rank
    return 0.0


def run_benchmark(num_users: int = 100, top_m: int = 20) -> List[Dict[str, Any]]:
    print("=" * 80)
    print(f"MOODGRAPH PHASE 4: HYBRID OFFLINE VALIDATION BENCHMARK ({num_users} USERS)")
    print("=" * 80)

    cfg = load_kg_config()
    data_root = cfg.data_root
    user_cohort = list(range(1, num_users + 1))
    positive_threshold = 3.5
    top_k_list = [5, 10, 20]

    # 1. Tải tập Validation
    print(f"[*] Đang nạp tập Validation từ {data_root / 'splits/validation'}...")
    val_path = data_root / "splits/validation"
    val_dataset = ds.dataset(str(val_path), format="parquet")
    scanner = val_dataset.scanner(
        columns=["userId", "movieId", "rating"],
        filter=ds.field("userId").isin(user_cohort)
    )
    val_data: Dict[int, Dict[str, Any]] = {}
    for batch in scanner.to_batches():
        pydict = batch.to_pydict()
        for i in range(batch.num_rows):
            uid = int(pydict["userId"][i])
            mid = int(pydict["movieId"][i])
            r = float(pydict["rating"][i])
            val_data[uid] = {"movieId": mid, "rating": r}

    positive_cohort = [
        u for u in user_cohort
        if u in val_data and val_data[u]["rating"] >= positive_threshold
    ]
    positive_denom = len(positive_cohort)
    print(f"  -> Tổng số users: {len(user_cohort)}, Positive Cohort Denominator: {positive_denom}")

    # 2. Khởi tạo ALS Service và KG Pilot Graph
    print("[*] Đang nạp ALS Delivery Service...")
    als_service = get_delivery_service()

    print(f"[*] Đang nạp KG Pilot Graph ({num_users} users)...")
    data_access = DataAccess(data_root)
    graph = InMemoryGraph()
    import_pilot_data(graph, data_access, set(user_cohort), top_m=top_m, batch_size=cfg.batch_size)

    # 3. Tính toán Popularity Count toàn cục trên tập Train
    print("[*] Đang tính tần suất phổ biến (Popularity Count) từ Train CSR...")
    als_service._load_csr_if_available()
    if als_service._csr_mids is not None:
        counts = Counter(als_service._csr_mids)
        sorted_pop_movies = [mid for mid, _ in counts.most_common(500)]
    else:
        sorted_pop_movies = [int(m) for m in list(graph.movies.keys())[:500]]

    # 4. Tiền trích xuất ứng viên C_ALS và C_KG (Single-pass Candidate Generation)
    print(f"[*] Đang sinh tập ứng viên Top-50 cho {positive_denom} positive users...")
    user_cand_als: Dict[int, List[Dict[str, Any]]] = {}
    user_cand_kg: Dict[int, List[Dict[str, Any]]] = {}

    t_cand_start = time.perf_counter()
    for idx, uid in enumerate(positive_cohort, start=1):
        # ALS
        als_recs = als_service.recommend(user_id=uid, top_n=50, stage="validation")
        user_cand_als[uid] = als_recs

        # KG
        kg_recs = recommend_kg(
            user_id=uid,
            top_n=50,
            exclude_movie_ids=None,
            graph=graph,
            enable_p1=True,
            enable_p2=True,
            enable_p3=True,
        )
        user_cand_kg[uid] = kg_recs

        if idx % 15 == 0 or idx == positive_denom:
            elapsed = time.perf_counter() - t_cand_start
            print(f"  -> Đã sinh ứng viên cho {idx}/{positive_denom} users ({elapsed:.1f}s)...")

    # 5. Đánh giá các mô hình thực nghiệm
    models_to_evaluate: List[Tuple[str, str, Dict[str, Any]]] = [
        ("Popularity Count (M03)", "popularity", {}),
        ("Spark ALS Champion (ALS_R8_REG0.3_ITER10)", "als_only", {}),
        ("Knowledge Graph (P1+P2+P3)", "kg_only", {}),
        ("Hybrid RRF (k=60)", "rrf", {"rrf_k": 60}),
        ("Hybrid Weighted (w_ALS=0.1, w_KG=0.9)", "weighted", {"weight_als": 0.1, "weight_kg": 0.9}),
        ("Hybrid Weighted (w_ALS=0.3, w_KG=0.7)", "weighted", {"weight_als": 0.3, "weight_kg": 0.7}),
        ("Hybrid Weighted (w_ALS=0.5, w_KG=0.5)", "weighted", {"weight_als": 0.5, "weight_kg": 0.5}),
        ("Hybrid Weighted (w_ALS=0.7, w_KG=0.3)", "weighted", {"weight_als": 0.7, "weight_kg": 0.3}),
        ("Hybrid Weighted (w_ALS=0.9, w_KG=0.1)", "weighted", {"weight_als": 0.9, "weight_kg": 0.1}),
    ]

    all_results: List[Dict[str, Any]] = []

    for model_label, strategy_type, params in models_to_evaluate:
        print(f"\n[*] Đang đánh giá: {model_label}...")
        hits = {k: 0.0 for k in top_k_list}
        ndcgs = {k: 0.0 for k in top_k_list}
        mrrs = {k: 0.0 for k in top_k_list}
        catalog_coverage_10: Set[int] = set()
        scoreable_count = 0

        t0 = time.perf_counter()
        for uid in positive_cohort:
            target_mid = val_data[uid]["movieId"]
            train_seen = als_service.get_train_seen_for_user(uid)

            rec_ids: List[int] = []

            if strategy_type == "popularity":
                candidates = [m for m in sorted_pop_movies if m not in train_seen]
                rec_ids = candidates[:max(top_k_list)]
            elif strategy_type == "als_only":
                rec_ids = [r["movieId"] for r in user_cand_als[uid][:max(top_k_list)]]
            elif strategy_type == "kg_only":
                rec_ids = [r["movieId"] for r in user_cand_kg[uid][:max(top_k_list)]]
            elif strategy_type == "rrf":
                fused = reciprocal_rank_fusion(
                    candidates_als=user_cand_als[uid],
                    candidates_kg=user_cand_kg[uid],
                    rrf_k=params.get("rrf_k", 60),
                    top_n=max(top_k_list),
                )
                rec_ids = [r["movieId"] for r in fused]
            elif strategy_type == "weighted":
                fused = weighted_score_fusion(
                    candidates_als=user_cand_als[uid],
                    candidates_kg=user_cand_kg[uid],
                    weight_als=params.get("weight_als", 0.5),
                    weight_kg=params.get("weight_kg", 0.5),
                    top_n=max(top_k_list),
                )
                rec_ids = [r["movieId"] for r in fused]

            if rec_ids:
                scoreable_count += 1
                catalog_coverage_10.update(rec_ids[:10])
                for k in top_k_list:
                    hits[k] += compute_hr_at_k(target_mid, rec_ids, k)
                    ndcgs[k] += compute_ndcg_at_k(target_mid, rec_ids, k)
                    mrrs[k] += compute_mrr_at_k(target_mid, rec_ids, k)

        elapsed = time.perf_counter() - t0
        latency_per_user_ms = (elapsed * 1000.0) / positive_denom if positive_denom > 0 else 0.0

        model_res = {
            "model_name": model_label,
            "strategy": strategy_type,
            "params": params,
            "total_users": len(user_cohort),
            "positive_denominator": positive_denom,
            "scoreable_users": scoreable_count,
            "score_availability": round(scoreable_count / positive_denom if positive_denom > 0 else 0.0, 4),
            "total_duration_sec": round(elapsed, 4),
            "latency_ms_per_user": round(latency_per_user_ms, 3),
            "metrics": {
                "HR@5": round(hits[5] / positive_denom if positive_denom > 0 else 0.0, 4),
                "NDCG@5": round(ndcgs[5] / positive_denom if positive_denom > 0 else 0.0, 4),
                "MRR@5": round(mrrs[5] / positive_denom if positive_denom > 0 else 0.0, 4),
                "HR@10": round(hits[10] / positive_denom if positive_denom > 0 else 0.0, 4),
                "NDCG@10": round(ndcgs[10] / positive_denom if positive_denom > 0 else 0.0, 4),
                "MRR@10": round(mrrs[10] / positive_denom if positive_denom > 0 else 0.0, 4),
                "HR@20": round(hits[20] / positive_denom if positive_denom > 0 else 0.0, 4),
                "NDCG@20": round(ndcgs[20] / positive_denom if positive_denom > 0 else 0.0, 4),
                "MRR@20": round(mrrs[20] / positive_denom if positive_denom > 0 else 0.0, 4),
                "Catalog_Coverage@10": len(catalog_coverage_10),
            },
        }
        all_results.append(model_res)
        print(f"  -> Duration: {elapsed:.4f}s ({latency_per_user_ms:.3f} ms/user)")
        print(f"  -> Metrics: HR@10={model_res['metrics']['HR@10']}, NDCG@10={model_res['metrics']['NDCG@10']}, HR@20={model_res['metrics']['HR@20']}, Coverage@10={model_res['metrics']['Catalog_Coverage@10']}")

    # 6. Lưu kết quả
    out_dir = PROJECT_ROOT / "docs" / "phase4"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / "hybrid_validation_results.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n[OK] Đã lưu toàn bộ kết quả benchmark vào: {out_json}")

    return all_results


if __name__ == "__main__":
    run_benchmark(100)
