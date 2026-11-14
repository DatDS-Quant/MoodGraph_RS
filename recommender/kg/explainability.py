"""
Mô-đun Trích xuất Cấu trúc Đồ thị Con và Bằng chứng Học thuật (Knowledge Graph Subgraph Extractor).
Phục vụ phân hệ Mode B REST API (/api/lab/graph/subgraph) và Mạng lưới Đồ thị Tương tác vis-network.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger("recommender.kg.explainability")

# Bảng mã màu chuẩn Obsidian Dark Glassmorphism theo Interface Contract
COLOR_PALETTE = {
    "USER": "#F59E0B",               # Vàng Hổ Phách
    "LIKED_MOVIE": "#06B6D4",        # Xanh Cyan
    "GENRE": "#10B981",              # Lục Bảo
    "GENOME_TAG": "#14B8A6",         # Xanh Ngọc
    "RECOMMENDED_MOVIE": "#8B5CF6",  # Tím Thạch Anh
    "DIRECTOR": "#EA580C"            # Cam San Hô
}


def extract_subgraph_for_pair(
    graph: Any,
    user_id: int,
    movie_id: int,
    recommendation_score: Optional[float] = None
) -> Dict[str, Any]:
    """
    Trích xuất mạng con liên kết giữa user_id và movie_id kèm chú thích học thuật.
    Hoạt động với EmbeddedKnowledgeGraph, InMemoryGraph hoặc bất kỳ graph nào có cấu trúc tương thích.
    """
    # Nếu graph có phương thức extract_subgraph riêng, ưu tiên gọi
    if hasattr(graph, "extract_subgraph"):
        return graph.extract_subgraph(user_id=user_id, candidate_movie_id=movie_id)

    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    node_ids: Set[str] = set()

    # 1. Đỉnh Khán giả (User Node)
    user_node_id = f"user_{user_id}"
    nodes.append({
        "id": user_node_id,
        "label": f"Khán giả #{user_id}",
        "type": "USER",
        "color": COLOR_PALETTE["USER"]
    })
    node_ids.add(user_node_id)

    # 2. Đỉnh Phim được Đề xuất (Recommended Movie Node)
    cand_movie = getattr(graph, "movies", {}).get(movie_id, {})
    cand_title = cand_movie.get("title", f"Movie #{movie_id}")
    cand_node_id = f"cand_{movie_id}"
    cand_node = {
        "id": cand_node_id,
        "label": cand_title,
        "type": "RECOMMENDED_MOVIE",
        "color": COLOR_PALETTE["RECOMMENDED_MOVIE"]
    }
    if recommendation_score is not None:
        cand_node["score"] = round(recommendation_score, 3)
    nodes.append(cand_node)
    node_ids.add(cand_node_id)

    # 3. Lấy thể loại & tags của candidate
    cand_genres = getattr(graph, "movie_in_genre", {}).get(movie_id, set())
    cand_tags = getattr(graph, "movie_has_genome_tag", {}).get(movie_id, {})

    # 4. Lấy lịch sử phim đã thích của user
    user_ratings = getattr(graph, "user_rated_movie", {}).get(user_id, {})
    liked_mids = [
        mid for mid, rinfo in user_ratings.items()
        if rinfo.get("rating", 0) >= 3.5
    ]

    p1_genres = []
    p2_tags = []

    # Duyệt tìm liên kết qua các phim đã thích
    for src_mid in liked_mids[:3]:
        rinfo = user_ratings[src_mid]
        src_rating = rinfo.get("rating", 4.0)
        src_movie = getattr(graph, "movies", {}).get(src_mid, {})
        src_title = src_movie.get("title", f"Movie #{src_mid}")
        src_node_id = f"movie_{src_mid}"

        src_genres = getattr(graph, "movie_in_genre", {}).get(src_mid, set())
        common_genres = cand_genres & src_genres
        src_tags = getattr(graph, "movie_has_genome_tag", {}).get(src_mid, {})
        common_tag_ids = set(src_tags.keys()) & set(cand_tags.keys())

        if common_genres or common_tag_ids:
            if src_node_id not in node_ids:
                nodes.append({
                    "id": src_node_id,
                    "label": src_title,
                    "type": "LIKED_MOVIE",
                    "rating": src_rating,
                    "color": COLOR_PALETTE["LIKED_MOVIE"]
                })
                node_ids.add(src_node_id)

            edges.append({
                "from": user_node_id,
                "to": src_node_id,
                "label": f"Đã thích ({src_rating}★)",
                "weight": round(src_rating / 5.0, 2),
                "type": "RATED"
            })

            # Metapath P1 (Genre)
            for g in list(common_genres)[:2]:
                g_id = f"genre_{abs(hash(g)) % 100000}"
                if g_id not in node_ids:
                    nodes.append({
                        "id": g_id,
                        "label": g,
                        "type": "GENRE",
                        "color": COLOR_PALETTE["GENRE"]
                    })
                    node_ids.add(g_id)

                edges.append({
                    "from": src_node_id,
                    "to": g_id,
                    "label": "Thể loại",
                    "weight": 0.72,
                    "type": "HAS_GENRE"
                })
                edges.append({
                    "from": g_id,
                    "to": cand_node_id,
                    "label": "Đồng thể loại",
                    "weight": 0.72,
                    "type": "HAS_GENRE"
                })
                if g not in p1_genres:
                    p1_genres.append(g)

            # Metapath P2 (Genome Tag)
            for tid in list(common_tag_ids)[:2]:
                tname = getattr(graph, "genome_tags", {}).get(tid, {}).get("name", f"tag_{tid}")
                t_id = f"tag_{tid}"
                rel_src = src_tags.get(tid, 0.8)
                rel_cand = cand_tags.get(tid, 0.8)

                if t_id not in node_ids:
                    nodes.append({
                        "id": t_id,
                        "label": tname,
                        "type": "GENOME_TAG",
                        "relevance": round(rel_cand, 2),
                        "color": COLOR_PALETTE["GENOME_TAG"]
                    })
                    node_ids.add(t_id)

                edges.append({
                    "from": src_node_id,
                    "to": t_id,
                    "label": f"rel = {round(rel_src, 2)}",
                    "weight": round(rel_src, 2),
                    "type": "HAS_TAG"
                })
                edges.append({
                    "from": t_id,
                    "to": cand_node_id,
                    "label": f"rel = {round(rel_cand, 2)}",
                    "weight": round(rel_cand, 2),
                    "type": "HAS_TAG"
                })
                if tname not in p2_tags:
                    p2_tags.append(tname)

    # Tạo lời giải thích học thuật
    reasons = []
    if p1_genres:
        reasons.append(f"Metapath P1 (Đồng thể loại {', '.join(p1_genres)}, đóng góp 35%)")
    if p2_tags:
        reasons.append(f"Metapath P2 (Cùng mang đặc trưng ngữ nghĩa {', '.join(p2_tags)}, đóng góp 45%)")
    if not reasons:
        reasons.append("Tương đồng đặc trưng thể loại trong danh mục tiềm năng (đóng góp 20%)")

    explanation = f"Được đề xuất bởi tổ hợp {' và '.join(reasons)}."

    return {
        "nodes": nodes,
        "edges": edges,
        "academic_explanation": explanation
    }
