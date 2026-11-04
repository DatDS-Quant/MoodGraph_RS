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
    import psutil
    process = psutil.Process()
    mem_mb = process.memory_info().rss / (1024 * 1024)
    # Bộ nhớ Python runtime hiện tại không vượt quá 500MB cho unit test
    assert mem_mb < 500.0, f"Bộ nhớ sử dụng quá cao: {mem_mb:.2f} MB"


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

