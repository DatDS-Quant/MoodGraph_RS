"""
Kiểm định chất lượng đồ thị và chống rò rỉ dữ liệu (KG-01 to KG-06 checks).
"""

from typing import Dict, Any, List, Tuple, Set


def verify_idempotency(counts_run1: Dict[str, int], counts_run2: Dict[str, int]) -> Tuple[bool, List[str]]:
    """
    Kiểm tra tính bất biến (idempotency) giữa 2 lần nạp liên tiếp.
    PASS khi tất cả số lượng nodes và edges của lần 2 hoàn toàn trùng khớp lần 1.
    """
    mismatches = []
    all_keys = set(counts_run1.keys()).union(set(counts_run2.keys()))
    for k in sorted(all_keys):
        c1 = counts_run1.get(k, 0)
        c2 = counts_run2.get(k, 0)
        if c1 != c2:
            mismatches.append(f"{k}: lần 1 có {c1}, lần 2 có {c2} (chênh lệch: {c2 - c1})")

    is_idempotent = len(mismatches) == 0
    return is_idempotent, mismatches


def verify_split_isolation(
    rated_pairs: Set[Tuple[int, int]],
    forbidden_val_pairs: Set[Tuple[int, int]],
    forbidden_test_pairs: Set[Tuple[int, int]]
) -> Tuple[bool, int, int]:
    """
    Kiểm tra rò rỉ dữ liệu (Split Isolation Guard - KG-05).
    Tuyệt đối không một cặp (userId, movieId) nào trong Validation hoặc Test được xuất hiện trong RATED.
    """
    val_leaks = rated_pairs.intersection(forbidden_val_pairs)
    test_leaks = rated_pairs.intersection(forbidden_test_pairs)

    passed = (len(val_leaks) == 0) and (len(test_leaks) == 0)
    return passed, len(val_leaks), len(test_leaks)


def verify_genome_top_m(
    movie_tag_counts: Dict[int, int],
    max_top_m: int
) -> Tuple[bool, int]:
    """
    Kiểm tra chính sách Top-M Genome Tag (KG-06).
    Mỗi phim chỉ được có tối đa max_top_m quan hệ HAS_GENOME_TAG.
    """
    violations = 0
    for movie_id, count in movie_tag_counts.items():
        if count > max_top_m:
            violations += 1
    return (violations == 0), violations

