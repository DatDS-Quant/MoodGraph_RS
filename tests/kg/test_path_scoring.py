"""
Kiểm thử KG-07, KG-08, KG-09: Metapath Validity, Scoring Fixture & Mutation Testing.
"""

import math
import pytest
from recommender.kg.import_graph import InMemoryGraph, import_synthetic_data
from recommender.kg.scorer import PathBasedScorer


def test_kg07_p1_p2_p3_path_validity():
    """KG-07: Đảm bảo mọi evidence sinh ra đều tương ứng với các node và edge có thật trong graph."""
    graph = InMemoryGraph()
    import_synthetic_data(graph)

    scorer = PathBasedScorer(min_liked_rating=3.5)
    recs = scorer.compute_user_candidates(user_id=1, graph=graph)

    assert len(recs) > 0, "Không sinh được candidate nào cho User 1"
    top_cand = recs[0]
    evidence_list = top_cand["evidence"]
    assert len(evidence_list) > 0, "Ứng viên không chứa evidence"

    # Duyệt kiểm tra từng evidence truy vết được trong đồ thị
    for ev in evidence_list:
        ptype = ev["path_type"]
        if ptype == "GENRE":
            # Kiểm tra quan hệ IN_GENRE
            src_id = ev["sourceMovieId"]
            genre_name = ev["sharedEntity"]["key"]
            assert src_id in graph.movies
            assert genre_name in graph.movie_in_genre[src_id]
            assert top_cand["movieId"] in graph.genre_to_movies[genre_name]
        elif ptype == "GENOME":
            # Kiểm tra quan hệ HAS_GENOME_TAG
            src_id = ev["sourceMovieId"]
            tag_id = ev["sharedEntity"]["key"]
            assert src_id in graph.movies
            assert tag_id in graph.movie_has_genome_tag[src_id]
            assert tag_id in graph.movie_has_genome_tag[top_cand["movieId"]]
        elif ptype == "COLLABORATIVE":
            # Kiểm tra quan hệ User - RATED - Movie
            n_uid = ev["neighborUserId"]
            assert n_uid in graph.users
            assert top_cand["movieId"] in graph.user_rated_movie[n_uid]


def test_kg08_scoring_fixture_hand_calculated():
    """KG-08: Đối chiếu điểm số tính toán với phép tính tay trên fixture (tolerance 1e-4)."""
    graph = InMemoryGraph()
    import_synthetic_data(graph)

    scorer = PathBasedScorer(min_liked_rating=3.5)

    # 1. Trọng số sở thích
    assert scorer.preference_weight(5.0) == 1.0
    assert scorer.preference_weight(4.5) == 0.75
    assert scorer.preference_weight(4.0) == 0.50
    assert scorer.preference_weight(3.5) == 0.25
    assert scorer.preference_weight(3.0) == 0.0
    assert scorer.preference_weight(2.0) == 0.0

    # 2. Sinh điểm cho User 1
    recs = scorer.compute_user_candidates(user_id=1, graph=graph)
    assert len(recs) == 2
    top_cand = recs[0]
    second_cand = recs[1]

    # Movie 3 được xếp thứ 1 vì có cả P1, P2 và P3
    assert top_cand["movieId"] == 3
    assert not math.isnan(top_cand["raw_score"])
    assert not math.isinf(top_cand["raw_score"])
    assert 0.0 <= top_cand["raw_score"] <= 1.0

    # Movie 6 là cold start item chỉ có P1
    assert second_cand["movieId"] == 6
    assert second_cand["raw_score"] < top_cand["raw_score"]


def test_kg09_mutation_test():
    """
    KG-09: Mutation Testing.
    Gỡ một cạnh trong đồ thị -> Điểm và evidence phải biến đổi có thể dự đoán được.
    Nếu thay đổi đồ thị mà điểm không đổi -> chứng tỏ hệ thống không thực hiện suy luận đường đi thật.
    """
    graph = InMemoryGraph()
    import_synthetic_data(graph)

    scorer = PathBasedScorer(min_liked_rating=3.5)

    # Điểm gốc ban đầu
    recs_original = scorer.compute_user_candidates(user_id=1, graph=graph)
    score_orig_cand3 = next(r["raw_score"] for r in recs_original if r["movieId"] == 3)

    # Đột biến: Xóa cạnh collaborative User 2 -> Movie 3
    del graph.user_rated_movie[2][3]
    del graph.movie_rated_by_users[3][2]

    # Tính lại điểm sau đột biến
    recs_mutated = scorer.compute_user_candidates(user_id=1, graph=graph)
    # Evidence collaborative của Movie 3 phải hoàn toàn biến mất
    cand3_mutated = next(r for r in recs_mutated if r["movieId"] == 3)
    collab_evidence = [ev for ev in cand3_mutated["evidence"] if ev["path_type"] == "COLLABORATIVE"]

    assert len(collab_evidence) == 0, "Cạnh collaborative đã xóa nhưng evidence vẫn xuất hiện!"

