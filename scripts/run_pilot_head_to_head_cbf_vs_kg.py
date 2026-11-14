"""
Thực nghiệm đối chuẩn khoa học: Content-Based Baselines vs Knowledge Graph Metapaths
Chạy trên tập Pilot 100 người dùng thực tế từ MovieLens 25M (data/processed).
"""

import sys
import os
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Set

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from recommender.kg.config import load_kg_config
from recommender.kg.data_access import DataAccess
from recommender.kg.import_graph import InMemoryGraph, import_pilot_data
from recommender.kg.scorer import PathBasedScorer
from recommender.kg.recommend import recommend_kg
from recommender.kg.content_based_baseline import ContentBasedRecommender
from recommender.kg.evaluate import ValidationEvaluator, compute_hr_at_k, compute_ndcg_at_k, compute_mrr_at_k


def run():
    print("=" * 80)
    print("MOODGRAPH KHOA HỌC: ĐỐI CHUẨN HEAD-TO-HEAD CONTENT-BASED VS KNOWLEDGE GRAPH")
    print("=" * 80)

    cfg = load_kg_config()
    data_access = DataAccess(cfg.data_root)

    # 1. Xác định tập cohort 100 users đầu tiên từ tập validation
    val_path = Path(cfg.data_root) / "splits/validation"
    val_evaluator = ValidationEvaluator(data_root=Path(cfg.data_root), positive_threshold=3.5)

    import pyarrow.dataset as ds
    dataset = ds.dataset(str(val_path), format="parquet")
    sample_users = []
    for batch in dataset.to_batches():
        uids = batch.to_pydict()["userId"]
        for uid in uids:
            if uid not in sample_users:
                sample_users.append(int(uid))
            if len(sample_users) >= 100:
                break
        if len(sample_users) >= 100:
            break

    user_cohort = set(sample_users[:100])
    print(f"[*] Tập Cohort: {len(user_cohort)} người dùng từ Validation Split.")

    # 2. Khởi tạo đồ thị và nạp dữ liệu
    graph = InMemoryGraph()
    print("[*] Đang nạp dữ liệu vào InMemoryGraph...")
    counts = import_pilot_data(graph, data_access, user_cohort=user_cohort, top_m=cfg.tag_top_m)
    print(f"[+] Nạp thành công: {counts['users']} users, {counts['movies']} movies, "
          f"{counts['rated_edges']} ratings, {counts['in_genre_edges']} genre edges, "
          f"{counts['has_genome_tag_edges']} genome edges.")

    # 3. Đọc dữ liệu validation cho cohort này
    val_evaluator.load_validation_cohort(user_cohort)

    positive_cohort = [
        uid for uid in user_cohort
        if uid in val_evaluator.val_data and val_evaluator.val_data[uid]["rating"] >= 3.5
    ]
    positive_denom = len(positive_cohort)
    print(f"[+] Số người dùng kiểm thử tích cực (Positive Cohort): {positive_denom} / {len(user_cohort)}")

    top_k_list = [5, 10, 20]
    cbf = ContentBasedRecommender()

    experiments = [
        {"name": "Content-Based (Genre-only)", "type": "cbf", "mode": "genre_only"},
        {"name": "Content-Based (Genre+Genome TF-IDF)", "type": "cbf", "mode": "full"},
        {"name": "Knowledge Graph (P1 Genre Metapath)", "type": "kg", "p1": True, "p2": False, "p3": False},
        {"name": "Knowledge Graph (P1+P2 Genre+Genome Metapaths)", "type": "kg", "p1": True, "p2": True, "p3": False},
        {"name": "Knowledge Graph (P1+P2+P3 Full Metapaths)", "type": "kg", "p1": True, "p2": True, "p3": True},
    ]

    benchmark_rows = []

    for exp in experiments:
        name = exp["name"]
        print(f"\n---> Chạy thử nghiệm: {name}")

        hits = {k: 0.0 for k in top_k_list}
        ndcgs = {k: 0.0 for k in top_k_list}
        mrrs = {k: 0.0 for k in top_k_list}
        rec_catalog_top10: Set[int] = set()

        t0 = time.time()
        for uid in positive_cohort:
            target_mid = val_evaluator.val_data[uid]["movieId"]

            if exp["type"] == "cbf":
                recs = cbf.recommend(user_id=uid, graph=graph, top_n=20, mode=exp["mode"])
                rec_mids = [r["movieId"] for r in recs]
            else:
                recs = recommend_kg(
                    user_id=uid,
                    top_n=20,
                    graph=graph,
                    enable_p1=exp["p1"],
                    enable_p2=exp["p2"],
                    enable_p3=exp["p3"]
                )
                rec_mids = [r["movieId"] for r in recs]

            rec_catalog_top10.update(rec_mids[:10])

            for k in top_k_list:
                hits[k] += compute_hr_at_k(target_mid, rec_mids, k)
                ndcgs[k] += compute_ndcg_at_k(target_mid, rec_mids, k)
                mrrs[k] += compute_mrr_at_k(target_mid, rec_mids, k)

        elapsed = time.time() - t0
        latency_ms = (elapsed / positive_denom) * 1000

        row = {
            "model_name": name,
            "positive_denominator": positive_denom,
            "HR@5": round(hits[5] / positive_denom, 4),
            "HR@10": round(hits[10] / positive_denom, 4),
            "HR@20": round(hits[20] / positive_denom, 4),
            "NDCG@10": round(ndcgs[10] / positive_denom, 4),
            "MRR@10": round(mrrs[10] / positive_denom, 4),
            "Catalog_Coverage@10": len(rec_catalog_top10),
            "latency_ms_per_user": round(latency_ms, 2)
        }
        benchmark_rows.append(row)
        print(f"     => HR@10: {row['HR@10']} | NDCG@10: {row['NDCG@10']} | Coverage@10: {row['Catalog_Coverage@10']} | Latency: {row['latency_ms_per_user']} ms")

    # Lưu kết quả
    out_path = PROJECT_ROOT / "docs/audits/kg_scientific_validation_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(benchmark_rows, f, indent=2, ensure_ascii=False)

    print(f"\n[+] ĐÃ HOÀN THÀNH VÀ GHI KẾT QUẢ VÀO: {out_path}")


if __name__ == "__main__":
    run()
