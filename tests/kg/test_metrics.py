"""
Kiểm thử KG-15, KG-16, KG-17: Validation Metrics, Resource Sanity & Git Hygiene.
"""

import subprocess
import pytest
from pathlib import Path
from recommender.kg.evaluate import compute_hr_at_k, compute_ndcg_at_k, compute_mrr_at_k


def test_kg15_validation_metrics_calculation():
    """KG-15: Kiểm tra tính toán các chỉ số đánh giá offline chính xác."""
    target_id = 100
    rec_list = [10, 20, 100, 30, 40]  # Target nằm ở vị trí thứ 3 (1-based rank = 3)

    # HR@K
    assert compute_hr_at_k(target_id, rec_list, k=2) == 0.0
    assert compute_hr_at_k(target_id, rec_list, k=3) == 1.0
    assert compute_hr_at_k(target_id, rec_list, k=5) == 1.0

    # NDCG@K
    # dcg = 1 / log2(3 + 1) = 1 / log2(4) = 0.5
    assert compute_ndcg_at_k(target_id, rec_list, k=2) == 0.0
    assert abs(compute_ndcg_at_k(target_id, rec_list, k=3) - 0.5) < 1e-4

    # MRR@K
    # 1 / 3 = 0.3333...
    assert compute_mrr_at_k(target_id, rec_list, k=2) == 0.0
    assert abs(compute_mrr_at_k(target_id, rec_list, k=3) - (1.0 / 3.0)) < 1e-4


def test_kg16_resource_sanity():
    """KG-16: Kiểm tra tài nguyên và bộ nhớ xử lý trong ngưỡng an toàn."""
    import gc
    import psutil
    gc.collect()
    process = psutil.Process()
    mem_mb = process.memory_info().rss / (1024 * 1024)
    # Bộ nhớ Python runtime không vượt quá 750MB (an toàn ngay cả khi chạy chung tiến trình với PySpark JVM trong combined suite)
    assert mem_mb < 750.0, f"Bộ nhớ sử dụng quá cao: {mem_mb:.2f} MB"


def test_kg17_git_hygiene():
    """KG-17: Kiểm tra vệ sinh Git: không làm bẩn repo, không commit data/secrets."""
    # Kiểm tra git status không chứa file .env nhạy cảm
    res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    status_out = res.stdout

    # Không được có tệp .env (ngoại trừ .env.example)
    lines = status_out.splitlines()
    for line in lines:
        path = line[3:].strip()
        assert not path.endswith(".env"), f"Phát hiện tệp bí mật trong git status: {path}"
        assert not path.endswith(".parquet"), f"Phát hiện file parquet trong git status: {path}"
        assert not path.endswith(".zip"), f"Phát hiện file zip trong git status: {path}"

def test_kg18_evaluator_ground_truth_inclusion_regression():
    """
    KG-18: Regression test cho lỗi P0 trong Validation Evaluator.
    Đảm bảo mục tiêu ground-truth (target_mid) KHÔNG bị loại trừ khỏi candidate pool,
    và đạt Hit Rate chính xác khi ứng viên nằm trong Top-K.
    """
    from recommender.kg.import_graph import InMemoryGraph, import_synthetic_data
    from recommender.kg.evaluate import ValidationEvaluator
    from recommender.kg.recommend import recommend_kg

    graph = InMemoryGraph()
    import_synthetic_data(graph)

    # Giả lập evaluator với user 1 có ground-truth validation target là movie 3 (rating 5.0)
    # Movie 3 có liên kết mạnh với lịch sử của User 1 (Movie 1, Movie 2) qua cả P1, P2, P3
    evaluator = ValidationEvaluator(data_root=Path("."), positive_threshold=3.5)
    evaluator.val_data = {
        1: {"movieId": 3, "rating": 5.0}
    }

    # 1. Đánh giá cấu hình với mã nguồn đã sửa (không exclude target_mid)
    res = evaluator.evaluate_configuration(
        graph=graph,
        user_cohort=[1],
        config_name="Test_Regression_Fix",
        enable_p1=True,
        enable_p2=True,
        enable_p3=True,
        top_k_list=[5, 10, 20]
    )

    # Movie 3 bắt buộc phải đạt hit tại Top-5 (thực tế xếp hạng 1 với raw_score = 1.0)
    assert res["positive_cohort_denominator"] == 1
    assert res["scoreable_users"] == 1
    assert res["metrics"]["HR@5"] == 1.0, "Target Movie 3 không đạt hit dù là ứng viên hàng đầu!"
    assert res["metrics"]["NDCG@5"] > 0.0
    assert res["metrics"]["MRR@5"] == 1.0

    # 2. Khẳng định ngược lại: nếu cố tình truyền exclude_movie_ids={3} (lỗi cũ) thì HR@K bị ép về 0
    recs_buggy = recommend_kg(user_id=1, top_n=5, exclude_movie_ids={3}, graph=graph)
    buggy_ids = [r["movieId"] for r in recs_buggy]
    assert 3 not in buggy_ids, "Khi bị exclude, movie 3 không được xuất hiện"

