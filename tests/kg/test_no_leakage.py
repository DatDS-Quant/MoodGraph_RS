"""
Kiểm thử KG-05 và KG-06: Split Isolation & Genome Top-M Selection Policy.
"""

import json
from pathlib import Path
import pytest
from recommender.kg.config import load_kg_config
from recommender.kg.checks import verify_split_isolation, verify_genome_top_m
from tests.kg.fixtures.synthetic_data import SYNTHETIC_TRAIN_RATINGS


def test_kg05_split_isolation_guard():
    """KG-05: Kiểm tra tuyệt đối không có tương tác từ Validation/Test bị đưa vào Train RATED."""
    config = load_kg_config()
    test_results_path = config.data_root / "test_results.json"
    assert test_results_path.exists(), "test_results.json không tồn tại"

    with open(test_results_path, "r", encoding="utf-8") as f:
        results = json.load(f)

    # Đảm bảo leak guard test đã pass ở mức tiền xử lý
    leak_guard = results.get("test_6_leakage_guard", {})
    assert leak_guard.get("status") == "PASSED"
    assert leak_guard.get("test_in_train_count") == 0
    assert leak_guard.get("val_in_train_count") == 0

    # Kiểm tra trên tập synthetic
    train_pairs = {(r["userId"], r["movieId"]) for r in SYNTHETIC_TRAIN_RATINGS}
    val_synthetic_pairs = {(1, 4), (2, 5)}  # Giả lập các cặp val không thuộc train
    test_synthetic_pairs = {(1, 6), (2, 7)}  # Giả lập các cặp test không thuộc train

    passed, v_leaks, t_leaks = verify_split_isolation(train_pairs, val_synthetic_pairs, test_synthetic_pairs)
    assert passed
    assert v_leaks == 0
    assert t_leaks == 0


def test_kg06_genome_selection_top_m():
    """KG-06: Kiểm tra chính sách giới hạn Top-M Genome Tags cho mỗi phim."""
    # Kiểm tra hàm kiểm định Top-M
    sample_movie_tag_counts = {1: 10, 2: 20, 3: 5, 4: 25}
    passed_20, violations_20 = verify_genome_top_m(sample_movie_tag_counts, max_top_m=20)
    assert not passed_20
    assert violations_20 == 1  # Phim 4 có 25 > 20

    passed_30, violations_30 = verify_genome_top_m(sample_movie_tag_counts, max_top_m=30)
    assert passed_30
    assert violations_30 == 0

