"""
Mô hình đối chuẩn Content-Based Filtering truyền thống (Content-Based Baseline Recommender).
Phục vụ đối chiếu khoa học trực tiếp với Mô hình Đồ thị Tri thức (Knowledge Graph Metapaths P1/P2/P3).

Mục tiêu nghiên cứu:
- Đo lường và chứng minh giá trị gia tăng độc lập của cấu trúc đồ thị (Graph Structure & Metapaths)
  so với mô hình so khớp đặc trưng nội dung phẳng (Flat Feature Vector Matching).

Kiến trúc:
1. Vector Space Model (VSM) dựa trên Thể loại (Genre TF-IDF / Normalized Profile).
2. Vector Space Model dựa trên Thẻ ngữ nghĩa Genome (Genome Tag Relevance Profile).
3. Hybrid Content-Based (Genre + Genome kết hợp với chuẩn hóa Cosine).
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple


class ContentBasedRecommender:
    """
    Hệ gợi ý dựa trên nội dung thuần túy (Vector Space Model - Cosine Similarity).
    Tuyệt đối không sử dụng cấu trúc liên kết đồ thị đa chặng (No Metapath Walk)
    và không sử dụng thông tin từ người dùng khác (No Collaborative Signal / No P3).
    """

    def __init__(
        self,
        min_liked_rating: float = 3.5,
        alpha_genre: float = 0.40,
        beta_genome: float = 0.60,
    ):
        self.min_liked_rating = min_liked_rating
        total = alpha_genre + beta_genome
        self.alpha_genre = alpha_genre / total
        self.beta_genome = beta_genome / total

    @staticmethod
    def preference_weight(rating: float) -> float:
        """Trọng số yêu thích tuyến tính trên thang [3.0, 5.0]: max(0.0, (r - 3.0) / 2.0)."""
        return max(0.0, (rating - 3.0) / 2.0)

    def build_user_genre_profile(
        self,
        liked_movies: Dict[int, float],
        movie_in_genre: Dict[int, Set[str]],
        genre_idf: Dict[str, float],
    ) -> Dict[str, float]:
        """
        Xây dựng vector đặc trưng thể loại của người dùng (User Genre Profile Vector).
        u_genre[g] = sum_{m in Liked} w(r_m) * IDF(g) * 1_{m has g}
        """
        profile: Dict[str, float] = defaultdict(float)
        for mid, rating in liked_movies.items():
            w = self.preference_weight(rating)
            genres = movie_in_genre.get(mid, set())
            for g in genres:
                idf = genre_idf.get(g, 1.0)
                profile[g] += w * idf
        return dict(profile)

    def build_user_genome_profile(
        self,
        liked_movies: Dict[int, float],
        movie_has_genome_tag: Dict[int, Dict[int, float]],
        tag_idf: Dict[int, float],
    ) -> Dict[int, float]:
        """
        Xây dựng vector đặc trưng thẻ ngữ nghĩa của người dùng (User Genome Profile Vector).
        u_genome[t] = sum_{m in Liked} w(r_m) * rel(m, t) * IDF(t)
        """
        profile: Dict[int, float] = defaultdict(float)
        for mid, rating in liked_movies.items():
            w = self.preference_weight(rating)
            tags = movie_has_genome_tag.get(mid, {})
            for tag_id, rel in tags.items():
                idf = tag_idf.get(tag_id, 1.0)
                profile[tag_id] += w * rel * idf
        return dict(profile)

    @staticmethod
    def cosine_similarity(
        vec_a: Dict[Any, float],
        vec_b: Dict[Any, float],
    ) -> float:
        """Tính Cosine Similarity giữa 2 sparse vectors."""
        if not vec_a or not vec_b:
            return 0.0

        # Lấy giao điểm các keys
        common_keys = set(vec_a.keys()) & set(vec_b.keys())
        if not common_keys:
            return 0.0

        dot = sum(vec_a[k] * vec_b[k] for k in common_keys)
        norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
        norm_b = math.sqrt(sum(v * v for v in vec_b.values()))

        if norm_a <= 1e-9 or norm_b <= 1e-9:
            return 0.0

        return dot / (norm_a * norm_b)

    def recommend(
        self,
        user_id: int,
        graph: Any,
        top_n: int = 10,
        exclude_movie_ids: Optional[Set[int]] = None,
        mode: str = "full",  # "genre_only", "genome_only", "full"
    ) -> List[Dict[str, Any]]:
        """
        Sinh danh sách gợi ý Content-Based Top-N cho người dùng.

        Args:
            user_id: ID người dùng
            graph: InMemoryGraph instance chứa dữ liệu quan hệ
            top_n: Số lượng phim gợi ý tối đa
            exclude_movie_ids: Tập ID phim cần loại trừ
            mode: "genre_only" | "genome_only" | "full"

        Returns:
            Danh sách gợi ý [{'movieId': ..., 'score': ..., 'rank': ...}]
        """
        # 1. Trích xuất lịch sử xem
        user_history: Dict[int, float] = {}
        if hasattr(graph, "user_rated_movie") and user_id in graph.user_rated_movie:
            for mid, rinfo in graph.user_rated_movie[user_id].items():
                user_history[mid] = rinfo["rating"]

        if not user_history:
            return []

        # Danh sách loại trừ
        total_exclude = set(user_history.keys())
        if exclude_movie_ids:
            total_exclude.update(exclude_movie_ids)

        # Lọc phim thích
        liked_movies = {
            mid: r for mid, r in user_history.items()
            if r >= self.min_liked_rating and self.preference_weight(r) > 0
        }
        if not liked_movies:
            return []

        # 2. Chuẩn bị tập ứng viên (Candidate Universe)
        all_movies = set()
        if hasattr(graph, "movie_title"):
            all_movies = set(graph.movie_title.keys())
        elif hasattr(graph, "movie_in_genre"):
            all_movies = set(graph.movie_in_genre.keys())

        candidate_movies = [m for m in all_movies if m not in total_exclude]
        if not candidate_movies:
            return []

        # 3. Tính IDF cho Genre và Genome
        total_items = max(1, len(all_movies))
        genre_idf: Dict[str, float] = {}
        if hasattr(graph, "genre_to_movies"):
            for g, mset in graph.genre_to_movies.items():
                genre_idf[g] = math.log1p(total_items / max(1, len(mset)))

        tag_idf: Dict[int, float] = {}
        if hasattr(graph, "genome_tag_to_movies"):
            for t, mdict in graph.genome_tag_to_movies.items():
                tag_idf[t] = math.log1p(total_items / max(1, len(mdict)))

        # 4. Xây dựng user profile
        user_genre_vec = (
            self.build_user_genre_profile(liked_movies, graph.movie_in_genre, genre_idf)
            if hasattr(graph, "movie_in_genre") and mode in ("genre_only", "full")
            else {}
        )
        user_genome_vec = (
            self.build_user_genome_profile(liked_movies, graph.movie_has_genome_tag, tag_idf)
            if hasattr(graph, "movie_has_genome_tag") and mode in ("genome_only", "full")
            else {}
        )

        # 5. Chấm điểm từng ứng viên
        scored_candidates: List[Tuple[int, float]] = []

        for cand_id in candidate_movies:
            sim_genre = 0.0
            sim_genome = 0.0

            if user_genre_vec and hasattr(graph, "movie_in_genre"):
                cand_genres = graph.movie_in_genre.get(cand_id, set())
                cand_genre_vec = {g: genre_idf.get(g, 1.0) for g in cand_genres}
                sim_genre = self.cosine_similarity(user_genre_vec, cand_genre_vec)

            if user_genome_vec and hasattr(graph, "movie_has_genome_tag"):
                cand_tags = graph.movie_has_genome_tag.get(cand_id, {})
                cand_genome_vec = {t: rel * tag_idf.get(t, 1.0) for t, rel in cand_tags.items()}
                sim_genome = self.cosine_similarity(user_genome_vec, cand_genome_vec)

            if mode == "genre_only":
                final_score = sim_genre
            elif mode == "genome_only":
                final_score = sim_genome
            else:
                final_score = self.alpha_genre * sim_genre + self.beta_genome * sim_genome

            if final_score > 0.0:
                scored_candidates.append((cand_id, final_score))

        # 6. Sắp xếp hạng giảm dần theo score, hòa theo movieId tăng dần
        scored_candidates.sort(key=lambda x: (-x[1], x[0]))
        top_candidates = scored_candidates[:top_n]

        results = []
        for rank, (mid, score) in enumerate(top_candidates, start=1):
            title = graph.movie_title.get(mid, f"Movie {mid}") if hasattr(graph, "movie_title") else f"Movie {mid}"
            results.append({
                "movieId": mid,
                "title": title,
                "score": round(score, 6),
                "rank": rank,
                "source": "CONTENT_BASED_BASELINE",
                "mode": mode,
            })

        return results
