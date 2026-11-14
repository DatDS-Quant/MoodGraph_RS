"""
Kịch bản đánh giá khoa học đối chuẩn độc lập (Scientific Benchmark Script):
So sánh đối đầu giữa Content-Based Filtering Baselines và Knowledge Graph Metapaths (P1, P2, P3).
"""

import sys
import os
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Set

# Đảm bảo đường dẫn gốc của repository
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from recommender.kg.config import load_kg_config
from recommender.kg.import_graph import InMemoryGraph, import_pilot_data, import_synthetic_data
from recommender.kg.recommend import recommend_kg
from recommender.kg.content_based_baseline import ContentBasedRecommender
from recommender.kg.evaluate import ValidationEvaluator, compute_hr_at_k, compute_ndcg_at_k, compute_mrr_at_k


def run_benchmark():
    print("=" * 70)
    print("BẮT ĐẦU ĐỐI CHUẨN KHOA HỌC: CONTENT-BASED VS KNOWLEDGE GRAPH")
    print("=" * 70)

    cfg = load_kg_config()
    graph = InMemoryGraph()

    # Kiểm tra xem có file pilot parquet không, nếu có thì nạp pilot, nếu không nạp synthetic
    pilot_dir = repo_root / "data/processed/pilot"
    if pilot_dir.exists() and (pilot_dir / "ratings_train.parquet").exists():
        print(f"Nạp dữ liệu Pilot Graph từ: {pilot_dir}")
        import_pilot_data(graph, pilot_dir)
    else:
        print("Không tìm thấy pilot parquet, nạp synthetic graph fixture...")
        import_synthetic_data(graph)

    # Khởi tạo ContentBasedRecommender
    cbf = ContentBasedRecommender()

    # Lấy danh sách users có trong đồ thị
    available_users = list(graph.user_rated_movie.keys()) if hasattr(graph, "user_rated_movie") else []
    print(f"Tổng số users có trong đồ thị: {len(available_users)}")

    # Đọc tập validation
    data_root = repo_root / "data/processed"
    val_evaluator = ValidationEvaluator(data_root=data_root, positive_threshold=3.5)
    
    val_path = data_root / "splits/validation"
    if val_path.exists():
        print(f"Đọc dữ liệu validation từ: {val_path}")
        val_evaluator.load_validation_cohort(set(available_users))
    else:
        print("Tập validation thực tế không có sẵn tại đường dẫn chuẩn, sử dụng synthetic validation...")
        # Tạo synthetic validation cho test
        for u in available_users[:50]:
            # lấy 1 phim chưa xem hoặc phim giả định
            val_evaluator.val_data[u] = {"movieId": 101, "rating": 4.5}

    positive_cohort = [
        uid for uid in available_users
        if uid in val_evaluator.val_data and val_evaluator.val_data[uid]["rating"] >= 3.5
    ]
    print(f"Số lượng positive users thẩm định: {len(positive_cohort)}")

    if not positive_cohort:
        print("Không có positive users nào trong tập thẩm định!")
        return

    top_k_list = [5, 10, 20]

    experiments = [
        {"name": "Content-Based (Genre-only)", "type": "cbf", "mode": "genre_only"},
        {"name": "Content-Based (Full: Genre+Genome TF-IDF)", "type": "cbf", "mode": "full"},
        {"name": "Knowledge Graph (P1 Genre Metapath)", "type": "kg", "p1": True, "p2": False, "p3": False},
        {"name": "Knowledge Graph (P1+P2 Genre+Genome Metapaths)", "type": "kg", "p1": True, "p2": True, "p3": False},
        {"name": "Knowledge Graph (P1+P2+P3 Full Metapaths)", "type": "kg", "p1": True, "p2": True, "p3": True},
    ]

    results = []

    for exp in experiments:
        exp_name = exp["name"]
        print(f"\n--- Đang đánh giá: {exp_name} ---")

        hits = {k: 0.0 for k in top_k_list}
        ndcgs = {k: 0.0 for k in top_k_list}
        mrrs = {k: 0.0 for k in top_k_list}
        recommended_catalog_items: Set[int] = set()

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
                    enable_p3=exp["p3"],
                )
                rec_mids = [r["movieId"] for r in recs]

            recommended_catalog_items.update(rec_mids[:10])

            for k in top_k_list:
                hits[k] += compute_hr_at_k(target_mid, rec_mids, k)
                ndcgs[k] += compute_ndcg_at_k(target_mid, rec_mids, k)
                mrrs[k] += compute_mrr_at_k(target_mid, rec_mids, k)

        elapsed = time.time() - t0
        n_denom = len(positive_cohort)

        res_row = {
            "model_name": exp_name,
            "positive_denominator": n_denom,
            "HR@5": round(hits[5] / n_denom, 4),
            "HR@10": round(hits[10] / n_denom, 4),
            "HR@20": round(hits[20] / n_denom, 4),
            "NDCG@10": round(ndcgs[10] / n_denom, 4),
            "MRR@10": round(mrrs[10] / n_denom, 4),
            "Catalog_Coverage@10": len(recommended_catalog_items),
            "latency_ms_per_user": round((elapsed / n_denom) * 1000, 2),
        }
        results.append(res_row)
        print(f"Kết quả {exp_name}: HR@10 = {res_row['HR@10']}, NDCG@10 = {res_row['NDCG@10']}, Coverage@10 = {res_row['Catalog_Coverage@10']}, Latency = {res_row['latency_ms_per_user']} ms/user")

    # Lưu kết quả vào docs/audits/kg_vs_cbf_results.json
    out_dir = repo_root / "docs/audits"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "kg_vs_cbf_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nĐã ghi nhận kết quả thành công tại: {out_file}")


if __name__ == "__main__":
    run_benchmark()
