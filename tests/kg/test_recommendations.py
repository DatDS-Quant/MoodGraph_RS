"""
Kiểm thử KG-10, KG-11, KG-12, KG-13: Recommendation Logic & Edge Cases.
"""

import pytest
from recommender.kg.import_graph import InMemoryGraph, import_synthetic_data
from recommender.kg.recommend import recommend_kg


def test_kg10_seen_item_filtering():
    """KG-10: Kiểm tra không bao giờ gợi ý phim người dùng đã đánh giá trong Train (hoặc exclude_movie_ids)."""
    graph = InMemoryGraph()
    import_synthetic_data(graph)

    # User 1 đã đánh giá Movie 1 và Movie 2 trong Train
    recs = recommend_kg(user_id=1, top_n=10, graph=graph)
    recommended_ids = {r["movieId"] for r in recs}

    assert 1 not in recommended_ids, "Movie 1 (đã xem trong Train) bị gợi ý lại"
    assert 2 not in recommended_ids, "Movie 2 (đã xem trong Train) bị gợi ý lại"

    # Kiểm tra exclude_movie_ids (loại thêm Movie 3)
    recs_filtered = recommend_kg(user_id=1, top_n=10, exclude_movie_ids={3}, graph=graph)
    filtered_ids = {r["movieId"] for r in recs_filtered}
    assert 3 not in filtered_ids


def test_kg11_deterministic_ranking():
    """KG-11: Trên cùng graph và cấu hình, các lần chạy phải trả về thứ tự Top-N và tie-break hoàn toàn giống nhau."""
    graph = InMemoryGraph()
    import_synthetic_data(graph)

    recs_run1 = recommend_kg(user_id=1, top_n=10, graph=graph)
    recs_run2 = recommend_kg(user_id=1, top_n=10, graph=graph)

    assert len(recs_run1) == len(recs_run2)
    for r1, r2 in zip(recs_run1, recs_run2):
        assert r1["movieId"] == r2["movieId"]
        assert r1["raw_score"] == r2["raw_score"]
        assert r1["rank"] == r2["rank"]


def test_kg12_cold_start_movie_behavior():
    """
    KG-12: Phim không có rating trong Train nhưng có metadata (Movie 6) có thể được gợi ý;
    Phim cô lập hoàn toàn không metadata (Movie 7) không bị ảo giác tạo liên kết.
    """
    graph = InMemoryGraph()
    import_synthetic_data(graph)

    recs = recommend_kg(user_id=1, top_n=10, graph=graph)
    rec_ids = [r["movieId"] for r in recs]

    # Phim 6 chưa từng được ai rate trong Train nhưng có genre "Animation" -> Được gợi ý
    assert 6 in rec_ids

    # Phim 7 không có genre, không genome, không rating -> Tuyệt đối không xuất hiện
    assert 7 not in rec_ids


def test_kg13_no_history_user_behavior():
    """KG-13: Người dùng không có lịch sử trong Train (User 4) trả về danh sách rỗng, không sập chương trình."""
    graph = InMemoryGraph()
    import_synthetic_data(graph)

    recs = recommend_kg(user_id=4, top_n=10, graph=graph)
    assert recs == []

