"""
Kiểm thử KG-03 và KG-04: Graph Edges Referential Integrity & Import Idempotency.
"""

import pytest
from recommender.kg.import_graph import InMemoryGraph, import_synthetic_data
from recommender.kg.checks import verify_idempotency
from tests.kg.fixtures.synthetic_data import EXPECTED_COUNTS


def test_kg03_graph_edges_referential_integrity():
    """KG-03: Kiểm tra cạnh đồ thị chỉ nối các endpoint tồn tại, không có cạnh mồ côi (dangling)."""
    graph = InMemoryGraph()
    import_synthetic_data(graph)

    # 1. Kiểm tra cạnh RATED
    for uid, rated_dict in graph.user_rated_movie.items():
        assert uid in graph.users, f"User {uid} không tồn tại trong danh sách User nodes"
        for mid, rinfo in rated_dict.items():
            assert mid in graph.movies, f"Movie {mid} không tồn tại trong Movie nodes"
            assert 0.5 <= rinfo["rating"] <= 5.0, f"Rating {rinfo['rating']} nằm ngoài dải hợp lệ"

    # 2. Kiểm tra cạnh IN_GENRE
    for mid, genres in graph.movie_in_genre.items():
        assert mid in graph.movies, f"Movie {mid} không tồn tại"
        for g in genres:
            assert g in graph.genres, f"Genre {g} không tồn tại"

    # 3. Kiểm tra cạnh HAS_GENOME_TAG
    for mid, tag_dict in graph.movie_has_genome_tag.items():
        assert mid in graph.movies, f"Movie {mid} không tồn tại"
        for tid, rel in tag_dict.items():
            assert tid in graph.genome_tags, f"GenomeTag {tid} không tồn tại"
            assert 0.0 <= rel <= 1.0, f"Relevance {rel} nằm ngoài [0, 1]"


def test_kg04_import_idempotency():
    """KG-04: Kiểm tra tính bất biến khi chạy lặp nạp 2 lần liên tiếp."""
    graph = InMemoryGraph()

    # Lần 1
    counts_run1 = import_synthetic_data(graph)
    assert counts_run1 == EXPECTED_COUNTS, f"Lần 1 không khớp số lượng kỳ vọng: {counts_run1} vs {EXPECTED_COUNTS}"

    # Lần 2 trên cùng instance graph
    counts_run2 = import_synthetic_data(graph)

    # Kiểm tra không tăng node/edge
    is_idempotent, mismatches = verify_idempotency(counts_run1, counts_run2)
    assert is_idempotent, f"Vi phạm tính Idempotent: {mismatches}"
    assert counts_run2 == EXPECTED_COUNTS

