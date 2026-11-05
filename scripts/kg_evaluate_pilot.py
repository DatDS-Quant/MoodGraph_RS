#!/usr/bin/env python3
"""
MoodGraph Task 3B: Offline Validation & Ablation Study Script (Gate 4)
Đánh giá 3 cấu hình:
1. Genre-only (P1)
2. Genre + Genome (P1 + P2)
3. Full Path-based (P1 + P2 + P3)
"""

import sys
import json
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Fix Windows console UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from recommender.kg.config import load_kg_config
from recommender.kg.data_access import DataAccess
from recommender.kg.import_graph import InMemoryGraph, import_pilot_data
from recommender.kg.evaluate import ValidationEvaluator


def run_ablation_evaluation(num_users: int = 100, top_m: int = 20):
    config = load_kg_config()
    print("=" * 75)
    print(f"MOODGRAPH TASK 3B: GATE 4 VALIDATION & ABLATION STUDY ({num_users} USERS)")
    print("=" * 75)

    data_access = DataAccess(config.data_root)
    user_cohort = list(range(1, num_users + 1))

    # 1. Nạp Pilot Graph
    print(f"[*] Đang dựng đồ thị pilot cho {num_users} users...")
    graph = InMemoryGraph()
    import_pilot_data(graph, data_access, set(user_cohort), top_m=top_m, batch_size=config.batch_size)

    # 2. Khởi tạo Evaluator
    evaluator = ValidationEvaluator(config.data_root, positive_threshold=config.min_liked_rating)
    evaluator.load_validation_cohort(set(user_cohort))

    # 3. Đánh giá 3 cấu hình Ablation
    configs = [
        ("Genre-only (P1)", True, False, False),
        ("Genre+Genome (P1+P2)", True, True, False),
        ("Full Path-based (P1+P2+P3)", True, True, True),
    ]

    ablation_results = []
    for cfg_name, p1, p2, p3 in configs:
        print(f"\n[*] Đánh giá cấu hình: {cfg_name}...")
        res = evaluator.evaluate_configuration(
            graph=graph,
            user_cohort=user_cohort,
            config_name=cfg_name,
            enable_p1=p1,
            enable_p2=p2,
            enable_p3=p3,
            top_k_list=[5, 10, 20]
        )
        ablation_results.append(res)
        print(f"  -> Hoàn thành trong {res['duration_seconds']}s")
        print(f"  -> Positive Denominator: {res['positive_cohort_denominator']}")
        print(f"  -> Score Availability: {res['score_availability'] * 100:.1f}%")
        print(f"  -> Metrics: {json.dumps(res['metrics'], indent=2)}")

    # Ghi kết quả vào file json
    report_file = PROJECT_ROOT / "docs/kg/ablation_results.json"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(ablation_results, f, indent=2)
    print(f"\n[OK] Đã lưu kết quả ablation vào: {report_file}")


if __name__ == "__main__":
    users = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    run_ablation_evaluation(users)

