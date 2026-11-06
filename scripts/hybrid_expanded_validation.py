#!/usr/bin/env python3
"""
MoodGraph Phase 4: Expanded Scientific Validation Benchmark Script.
Evaluates 200 users on Validation split (Leave-1-Last protocol):
- Baselines: Popularity Count (M03), Spark ALS Champion, Knowledge Graph (P1+P2+P3).
- Hybrid Fusion Variants:
  * RRF (k=60)
  * Weighted (w_ALS=0.5, w_KG=0.5, imputation='zero')
  * Weighted (w_ALS=0.5, w_KG=0.5, imputation='min')
  * Weighted (w_ALS=0.5, w_KG=0.5, imputation='neutral')
  * Weighted (w_ALS=0.5, w_KG=0.5, imputation='source_aware')
  * Weighted Cross-Scored (w_ALS=0.5, w_KG=0.5, cross_score_als=True)
- Metrics: HR@5/10/20, NDCG@5/10/20, MRR@5/10/20, Coverage@10/20, Candidate Recall@50, Paired Wins/Losses.
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


def run_expanded_benchmark(num_users: int = 200, top_m: int = 20) -> Dict[str, Any]:
    print("=" * 80)
    print(f"MOODGRAPH PHASE 4: EXPANDED SCIENTIFIC VALIDATION BENCHMARK ({num_users} USERS)")
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
    als_service._load_csr_if_available()

    print(f"[*] Đang nạp KG Pilot Graph ({num_users} users)...")
    data_access = DataAccess(data_root)
    graph = InMemoryGraph()
    import_pilot_data(graph, data_access, set(user_cohort), top_m=top_m, batch_size=cfg.batch_size)

    # 3. Tính toán Popularity Count toàn cục trên tập Train
    print("[*] Đang tính tần suất phổ biến (Popularity Count) từ Train CSR...")
    if als_service._csr_mids is not None:
        counts = Counter(als_service._csr_mids)
        sorted_pop_movies = [mid for mid, _ in counts.most_common(500)]
    else:
        sorted_pop_movies = [int(m) for m in list(graph.movies.keys())[:500]]

    # 4. Tiền trích xuất ứng viên C_ALS và C_KG (Single-pass Candidate Generation)
    print(f"[*] Đang sinh tập ứng viên Top-50 cho {positive_denom} positive users...")
    user_cand_als: Dict[int, List[Dict[str, Any]]] = {}
    user_cand_kg: Dict[int, List[Dict[str, Any]]] = {}
    user_cand_kg_cross: Dict[int, List[Dict[str, Any]]] = {}

    als_candidate_hits = 0
    kg_candidate_hits = 0
    union_candidate_hits = 0

    t_cand_start = time.perf_counter()
    for idx, uid in enumerate(positive_cohort, start=1):
        target_mid = val_data[uid]["movieId"]

        # ALS Top-50
        als_recs = als_service.recommend(user_id=uid, top_n=50, stage="validation")
        user_cand_als[uid] = als_recs

        # KG Top-50
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

        # Candidate recall audit
        als_mids = {r["movieId"] for r in als_recs}
        kg_mids = {r["movieId"] for r in kg_recs}
        if target_mid in als_mids:
            als_candidate_hits += 1
        if target_mid in kg_mids:
            kg_candidate_hits += 1
        if target_mid in (als_mids | kg_mids):
            union_candidate_hits += 1

        # Precompute ALS cross-scores for KG candidates
        cross_als_candidates: List[Dict[str, Any]] = list(als_recs)
        existing_als_mids = set(als_mids)
        user_factors = getattr(als_service.generator, "user_factors", None)
        item_factors = getattr(als_service.generator.catalog, "factors", None)
        user_id_map = getattr(als_service.generator, "user_id_map", {})
        item_id_map = getattr(als_service.generator.catalog, "item_id_map", {})

        if user_factors is not None and item_factors is not None and uid in user_id_map:
            u_idx = user_id_map[uid]
            u_vec = user_factors[u_idx]
            for kg_item in kg_recs:
                k_mid = kg_item["movieId"]
                if k_mid not in existing_als_mids and k_mid in item_id_map:
                    m_idx = item_id_map[k_mid]
                    m_vec = item_factors[m_idx]
                    dot_score = float(u_vec @ m_vec)
                    cross_als_candidates.append({
                        "movieId": k_mid,
                        "title": kg_item.get("title", f"Movie {k_mid}"),
                        "score": dot_score,
                        "rank": None,
                    })
        user_cand_kg_cross[uid] = cross_als_candidates

        if idx % 25 == 0 or idx == positive_denom:
            elapsed = time.perf_counter() - t_cand_start
            print(f"  -> Đã sinh ứng viên cho {idx}/{positive_denom} users ({elapsed:.1f}s)...")

    candidate_recall = {
        "als_recall_at_50": round(als_candidate_hits / positive_denom if positive_denom > 0 else 0.0, 4),
        "kg_recall_at_50": round(kg_candidate_hits / positive_denom if positive_denom > 0 else 0.0, 4),
        "union_recall_at_50": round(union_candidate_hits / positive_denom if positive_denom > 0 else 0.0, 4),
        "als_hits": als_candidate_hits,
        "kg_hits": kg_candidate_hits,
        "union_hits": union_candidate_hits,
        "positive_denom": positive_denom,
    }
    print(f"\n[*] Candidate Recall@50: ALS={candidate_recall['als_recall_at_50']} ({als_candidate_hits}/{positive_denom}), "
          f"KG={candidate_recall['kg_recall_at_50']} ({kg_candidate_hits}/{positive_denom}), "
          f"Union={candidate_recall['union_recall_at_50']} ({union_candidate_hits}/{positive_denom})")

    # 5. Các mô hình thực nghiệm
    models_to_evaluate: List[Tuple[str, str, Dict[str, Any]]] = [
        ("Popularity Count (M03 Baseline)", "popularity", {}),
        ("Spark ALS Champion (ALS_R8_REG0.3_ITER10)", "als_only", {}),
        ("Knowledge Graph (P1+P2+P3)", "kg_only", {}),
        ("Hybrid RRF (k=60)", "rrf", {"rrf_k": 60}),
        ("Hybrid Weighted (w_ALS=0.5, w_KG=0.5, Impute Zero)", "weighted", {"weight_als": 0.5, "weight_kg": 0.5, "imputation_strategy": "zero"}),
        ("Hybrid Weighted (w_ALS=0.5, w_KG=0.5, Impute Min)", "weighted", {"weight_als": 0.5, "weight_kg": 0.5, "imputation_strategy": "min"}),
        ("Hybrid Weighted (w_ALS=0.5, w_KG=0.5, Impute Neutral)", "weighted", {"weight_als": 0.5, "weight_kg": 0.5, "imputation_strategy": "neutral"}),
        ("Hybrid Weighted (w_ALS=0.5, w_KG=0.5, Impute Source-Aware)", "weighted", {"weight_als": 0.5, "weight_kg": 0.5, "imputation_strategy": "source_aware"}),
        ("Hybrid Weighted Cross-Scored (w_ALS=0.5, w_KG=0.5)", "weighted_cross", {"weight_als": 0.5, "weight_kg": 0.5, "imputation_strategy": "neutral"}),
    ]

    all_results: List[Dict[str, Any]] = []
    user_ndcg10_by_model: Dict[str, Dict[int, float]] = {}

    for model_label, strategy_type, params in models_to_evaluate:
        print(f"\n[*] Đang đánh giá: {model_label}...")
        hits = {k: 0.0 for k in top_k_list}
        hit_counts = {k: 0 for k in top_k_list}
        ndcgs = {k: 0.0 for k in top_k_list}
        mrrs = {k: 0.0 for k in top_k_list}
        catalog_coverage_10: Set[int] = set()
        catalog_coverage_20: Set[int] = set()
        scoreable_count = 0
        user_ndcg10: Dict[int, float] = {}

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
                    imputation_strategy=params.get("imputation_strategy", "zero"),
                    top_n=max(top_k_list),
                )
                rec_ids = [r["movieId"] for r in fused]
            elif strategy_type == "weighted_cross":
                fused = weighted_score_fusion(
                    candidates_als=user_cand_kg_cross[uid],
                    candidates_kg=user_cand_kg[uid],
                    weight_als=params.get("weight_als", 0.5),
                    weight_kg=params.get("weight_kg", 0.5),
                    imputation_strategy=params.get("imputation_strategy", "neutral"),
                    top_n=max(top_k_list),
                )
                rec_ids = [r["movieId"] for r in fused]

            if rec_ids:
                scoreable_count += 1
                catalog_coverage_10.update(rec_ids[:10])
                catalog_coverage_20.update(rec_ids[:20])
                for k in top_k_list:
                    h = compute_hr_at_k(target_mid, rec_ids, k)
                    hits[k] += h
                    if h > 0:
                        hit_counts[k] += 1
                    ndcg_val = compute_ndcg_at_k(target_mid, rec_ids, k)
                    ndcgs[k] += ndcg_val
                    mrrs[k] += compute_mrr_at_k(target_mid, rec_ids, k)
                user_ndcg10[uid] = compute_ndcg_at_k(target_mid, rec_ids, 10)
            else:
                user_ndcg10[uid] = 0.0

        user_ndcg10_by_model[model_label] = user_ndcg10

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
            "hit_counts": hit_counts,
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
                "Catalog_Coverage@20": len(catalog_coverage_20),
            },
        }
        all_results.append(model_res)
        print(f"  -> Duration: {elapsed:.4f}s ({latency_per_user_ms:.3f} ms/user)")
        print(f"  -> Metrics: HR@10={model_res['metrics']['HR@10']} ({hit_counts[10]}/{positive_denom}), "
              f"NDCG@10={model_res['metrics']['NDCG@10']}, HR@20={model_res['metrics']['HR@20']} ({hit_counts[20]}/{positive_denom}), "
              f"Coverage@10={model_res['metrics']['Catalog_Coverage@10']}, Coverage@20={model_res['metrics']['Catalog_Coverage@20']}")

    # 6. So sánh cặp (Paired Comparisons) đối với NDCG@10 giữa RRF và các baseline
    rrf_key = "Hybrid RRF (k=60)"
    rrf_ndcgs = user_ndcg10_by_model.get(rrf_key, {})

    paired_comparisons = {}
    for other_label, other_ndcgs in user_ndcg10_by_model.items():
        if other_label == rrf_key:
            continue
        wins = 0
        losses = 0
        ties = 0
        for uid in positive_cohort:
            r_val = rrf_ndcgs.get(uid, 0.0)
            o_val = other_ndcgs.get(uid, 0.0)
            if r_val > o_val + 1e-6:
                wins += 1
            elif r_val < o_val - 1e-6:
                losses += 1
            else:
                ties += 1
        paired_comparisons[f"RRF_vs_{other_label}"] = {
            "wins": wins,
            "losses": losses,
            "ties": ties,
            "win_rate": round(wins / positive_denom if positive_denom > 0 else 0.0, 4),
        }

    final_payload = {
        "candidate_recall_at_50": candidate_recall,
        "models": all_results,
        "paired_comparisons": paired_comparisons,
    }

    # 7. Lưu kết quả
    out_dir = PROJECT_ROOT / "docs" / "phase4"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / "expanded_validation_results.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(final_payload, f, indent=2)
    print(f"\n[OK] Đã lưu kết quả mở rộng vào: {out_json}")

    return final_payload


if __name__ == "__main__":
    run_expanded_benchmark(200)
