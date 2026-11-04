"""
Kiểm thử KG-14: Integration Output Contract & Evidence Schema.
"""

import pytest
from recommender.kg.import_graph import InMemoryGraph, import_synthetic_data
from recommender.kg.recommend import recommend_kg


def test_kg14_integration_output_schema():
    """KG-14: Kiểm tra định dạng đầu ra khớp chuẩn tích hợp với Khối 4 Hybrid."""
    graph = InMemoryGraph()
    import_synthetic_data(graph)

    recs = recommend_kg(user_id=1, top_n=5, graph=graph)
    assert len(recs) > 0

    required_keys = {"userId", "movieId", "title", "raw_score", "rank", "model_name", "evidence"}

    for r in recs:
        assert required_keys.issubset(r.keys()), f"Thiếu trường bắt buộc trong kết quả: {r.keys()}"
        assert isinstance(r["userId"], int)
        assert isinstance(r["movieId"], int)
        assert isinstance(r["title"], str)
        assert isinstance(r["raw_score"], float)
        assert isinstance(r["rank"], int)
        assert r["model_name"] == "KG_PATH"
        assert isinstance(r["evidence"], list)

        # Kiểm tra cấu trúc từng evidence
        for ev in r["evidence"]:
            assert "path_type" in ev
            assert ev["path_type"] in {"GENRE", "GENOME", "COLLABORATIVE"}
            assert "contribution" in ev
            assert isinstance(ev["contribution"], float)

