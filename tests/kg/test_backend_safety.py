"""
Kiểm thử KG-19: Backend Fallback Guard, Security Masking & Runtime Resilience.
"""

import math
import os
import sys
from unittest.mock import MagicMock
import pytest
import warnings
from recommender.kg.config import load_kg_config, KGConfig
from recommender.kg.import_graph import InMemoryGraph, import_synthetic_data
from recommender.kg.recommend import (
    get_default_graph,
    reset_cached_graph,
    recommend_kg,
    set_cached_graph,
)
from recommender.kg.scorer import PathBasedScorer


def test_kg19_production_fail_fast_on_neo4j_unavailability():
    """
    KG-19a: Trong chế độ production/pilot, nếu Neo4j không khả dụng thì HỆ THỐNG
    PHẢI FAIL-FAST (ném ConnectionError), TUYỆT ĐỐI KHÔNG âm thầm chuyển sang synthetic graph.
    """
    reset_cached_graph()
    cfg = load_kg_config()
    cfg.neo4j_uri = "bolt://127.0.0.1:9999"
    cfg.import_mode = "pilot"

    old_env = os.environ.get("KG_ALLOW_SYNTHETIC_FALLBACK")
    if "KG_ALLOW_SYNTHETIC_FALLBACK" in os.environ:
        del os.environ["KG_ALLOW_SYNTHETIC_FALLBACK"]

    try:
        with pytest.raises(ConnectionError) as exc_info:
            get_default_graph(config=cfg)

        err_msg = str(exc_info.value)
        assert "Không thể kết nối cơ sở dữ liệu Neo4j" in err_msg
        assert "silent degradation" in err_msg or "vô hiệu hóa" in err_msg
    finally:
        if old_env is not None:
            os.environ["KG_ALLOW_SYNTHETIC_FALLBACK"] = old_env
        reset_cached_graph()


def test_kg19_no_credential_leakage_in_error_message():
    """
    KG-19b: Khi xảy ra lỗi kết nối Neo4j, mật khẩu tuyệt đối không được lộ trong error message.
    Nếu exception từ driver chứa chuỗi mật khẩu, chuỗi đó phải được mask thành '******'.
    """
    reset_cached_graph()
    cfg = load_kg_config()
    cfg.neo4j_uri = "bolt://127.0.0.1:9999"
    secret_pass = "super_secret_confidential_password_12345"
    cfg.neo4j_password = secret_pass
    cfg.import_mode = "pilot"

    old_env = os.environ.get("KG_ALLOW_SYNTHETIC_FALLBACK")
    if "KG_ALLOW_SYNTHETIC_FALLBACK" in os.environ:
        del os.environ["KG_ALLOW_SYNTHETIC_FALLBACK"]

    # Mock neo4j module và GraphDatabase.driver ném lỗi chứa plaintext secret
    mock_neo4j = MagicMock()
    mock_neo4j.GraphDatabase.driver.side_effect = Exception(f"Auth failed for user with password {secret_pass}")
    
    old_neo4j_mod = sys.modules.get("neo4j")
    sys.modules["neo4j"] = mock_neo4j
    try:
        with pytest.raises(ConnectionError) as exc_info:
            get_default_graph(config=cfg)

        err_msg = str(exc_info.value)
        assert secret_pass not in err_msg, "Mật khẩu bị lộ trong thông báo lỗi!"
        assert "******" in err_msg, "Mật khẩu chưa được thay thế bằng chuỗi ẩn danh!"
    finally:
        if old_neo4j_mod is not None:
            sys.modules["neo4j"] = old_neo4j_mod
        else:
            sys.modules.pop("neo4j", None)
        if old_env is not None:
            os.environ["KG_ALLOW_SYNTHETIC_FALLBACK"] = old_env
        reset_cached_graph()


def test_kg19_explicit_synthetic_fallback_in_dev_mode():
    """
    KG-19c: Chỉ khi cấu hình rõ ràng import_mode='synthetic' hoặc KG_ALLOW_SYNTHETIC_FALLBACK=true,
    hệ thống mới phát cảnh báo UserWarning và trả về InMemoryGraph phục vụ dev/unit test.
    """
    reset_cached_graph()
    cfg = load_kg_config()
    cfg.neo4j_uri = "bolt://127.0.0.1:9999"
    cfg.import_mode = "synthetic"

    with pytest.warns(UserWarning, match="Fallback sang InMemoryGraph với synthetic fixture"):
        g = get_default_graph(config=cfg)

    assert isinstance(g, InMemoryGraph)
    assert len(g.users) > 0
    reset_cached_graph()


def test_kg19_input_validation():
    """
    KG-19d: Kiểm tra xác thực đầu vào nghiêm ngặt cho recommend_kg (userId và top_n).
    """
    graph = InMemoryGraph()
    import_synthetic_data(graph)

    with pytest.raises(ValueError, match="user_id phải là số nguyên dương"):
        recommend_kg(user_id=-1, graph=graph)

    with pytest.raises(ValueError, match="user_id phải là số nguyên dương"):
        recommend_kg(user_id=0, graph=graph)

    with pytest.raises(ValueError, match="top_n phải là số nguyên dương"):
        recommend_kg(user_id=1, top_n=0, graph=graph)

    with pytest.raises(ValueError, match="top_n phải là số nguyên dương"):
        recommend_kg(user_id=1, top_n=-5, graph=graph)


def test_kg19_non_finite_score_resilience():
    """
    KG-19e: Đảm bảo bộ chuẩn hóa điểm số không bao giờ sinh NaN hay Inf khi gặp giá trị bất thường.
    """
    scorer = PathBasedScorer()
    scores_with_non_finite = [1.0, float("nan"), float("inf"), float("-inf"), 3.0]
    norm = scorer._normalize_scores(scores_with_non_finite)

    assert len(norm) == len(scores_with_non_finite)
    for s in norm:
        assert math.isfinite(s)
        assert 0.0 <= s <= 1.0


def test_kg20_data_root_portability():
    """
    KG-20: Kiểm tra tính độc lập của config data_root đối với thư mục làm việc hiện tại (CWD).
    """
    import tempfile
    from pathlib import Path
    
    # 1. Khi MOODGRAPH_DATA_ROOT được đặt rõ ràng
    old_root = os.environ.get("MOODGRAPH_DATA_ROOT")
    try:
        os.environ["MOODGRAPH_DATA_ROOT"] = "nonexistent_custom_data_path_xyz"
        cfg = load_kg_config()
        # Đảm bảo không âm thầm chuyển sang dataset khác khi biến môi trường được đặt rõ ràng
        assert "nonexistent_custom_data_path_xyz" in str(cfg.data_root)
    finally:
        if old_root is not None:
            os.environ["MOODGRAPH_DATA_ROOT"] = old_root
        else:
            os.environ.pop("MOODGRAPH_DATA_ROOT", None)

    # 2. Khi không có biến môi trường, canonical data root phải luôn trỏ tới thư mục tồn tại trong project
    cfg_default = load_kg_config()
    assert cfg_default.data_root.exists(), f"Default data root không tồn tại: {cfg_default.data_root}"
