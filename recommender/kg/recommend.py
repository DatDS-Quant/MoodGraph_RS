"""
Facade gợi ý phim độc lập dựa trên Đồ thị tri thức (Knowledge Graph Recommendation Facade).
Điểm giao tiếp chính với Khối 4 Hybrid Recommender và Serving API.
"""

from typing import List, Dict, Any, Set, Optional
from recommender.kg.config import load_kg_config, KGConfig
from recommender.kg.scorer import PathBasedScorer
from recommender.kg.import_graph import InMemoryGraph, import_synthetic_data

# Singleton cache cho in-memory graph khi chạy ở chế độ synthetic
_CACHED_GRAPH: Optional[Any] = None


def get_default_graph(config: Optional[KGConfig] = None) -> Any:
    global _CACHED_GRAPH
    if _CACHED_GRAPH is not None:
        return _CACHED_GRAPH

    cfg = config or load_kg_config()
    # Kiểm tra kết nối Neo4j
    try:
        from neo4j import GraphDatabase
        from recommender.kg.import_graph import Neo4jGraph
        driver = GraphDatabase.driver(cfg.neo4j_uri, auth=(cfg.neo4j_user, cfg.neo4j_password))
        driver.verify_connectivity()
        driver.close()
        _CACHED_GRAPH = Neo4jGraph(cfg.neo4j_uri, auth=(cfg.neo4j_user, cfg.neo4j_password), database=cfg.neo4j_database)
        return _CACHED_GRAPH
    except Exception:
        # Fallback sang InMemoryGraph với synthetic fixture
        g = InMemoryGraph()
        import_synthetic_data(g)
        _CACHED_GRAPH = g
        return _CACHED_GRAPH


def set_cached_graph(graph: Any):
    """Gán trực tiếp graph instance (dùng cho testing hoặc sau khi import pilot)."""
    global _CACHED_GRAPH
    _CACHED_GRAPH = graph


def recommend_kg(
    user_id: int,
    top_n: int = 10,
    exclude_movie_ids: Optional[Set[int]] = None,
    graph: Optional[Any] = None,
    config: Optional[KGConfig] = None,
    enable_p1: bool = True,
    enable_p2: bool = True,
    enable_p3: bool = True
) -> List[Dict[str, Any]]:
    """
    Sinh danh sách Top-N gợi ý độc lập dựa trên Knowledge Graph.

    Args:
        user_id: ID người dùng cần gợi ý
        top_n: Số lượng phim gợi ý tối đa
        exclude_movie_ids: Tập ID phim loại trừ (phim đã xem trong Train/Val...)
        graph: Thể hiện đồ thị (nếu None sẽ dùng graph mặc định)
        config: Cấu hình tham số (nếu None sẽ đọc từ biến môi trường)
        enable_p1: Kích hoạt đường P1 (Genre)
        enable_p2: Kích hoạt đường P2 (Genome)
        enable_p3: Kích hoạt đường P3 (Collaborative Graph)

    Returns:
        Danh sách dict chứa các gợi ý Top-N kèm theo evidence truy vết từ đồ thị.
    """
    cfg = config or load_kg_config()
    target_graph = graph or get_default_graph(cfg)

    scorer = PathBasedScorer(
        min_liked_rating=cfg.min_liked_rating,
        alpha_genre=cfg.weight_alpha_genre,
        beta_genome=cfg.weight_beta_genome,
        gamma_collab=cfg.weight_gamma_collab
    )

    candidates = scorer.compute_user_candidates(
        user_id=user_id,
        graph=target_graph,
        exclude_movie_ids=exclude_movie_ids,
        enable_p1=enable_p1,
        enable_p2=enable_p2,
        enable_p3=enable_p3
    )

    return candidates[:top_n]

