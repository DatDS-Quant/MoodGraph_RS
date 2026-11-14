"""
Đồ thị Tri thức Nhúng Độc lập (Embedded Knowledge Graph Engine).
Hoạt động thuần in-process (RAM) sử dụng cấu trúc dictionaries và sets tối ưu hóa cao.
Không phụ thuộc socket mạng, không cần Neo4j Server.
Hỗ trợ nạp Parquet, đồng bộ SQLite app_state.db và trích xuất Subgraph giải thích trực quan.
"""

from __future__ import annotations

import heapq
import logging
import math
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("recommender.kg.embedded_graph")


class EmbeddedKnowledgeGraph:
    """
    Đồ thị tri thức nhúng in-memory:
    - Lưu trữ danh mục phim (Movies), thể loại (Genres), thẻ đặc trưng ngữ nghĩa (Genome Tags).
    - Inverted indices đa quan hệ: P1 (Genre), P2 (Genome), P3 (Collaborative Ratings).
    - Tự động đồng bộ với SQLite app_state.db cho các phiên người dùng tương tác thời gian thực.
    - Cung cấp phương thức trích xuất Subgraph cấu trúc (Nodes, Edges, Weights) chuẩn giao thức Lab API.
    """

    def __init__(self):
        # Nodes
        self.users: Dict[int, Dict[str, Any]] = {}
        self.movies: Dict[int, Dict[str, Any]] = {}
        self.genres: Dict[str, Dict[str, Any]] = {}
        self.genome_tags: Dict[int, Dict[str, Any]] = {}

        # Edges & Inverted Indices
        # user_id -> movie_id -> {"rating": float, "timestamp": int}
        self.user_rated_movie: Dict[int, Dict[int, Dict[str, Any]]] = {}
        # movie_id -> user_id -> {"rating": float, "timestamp": int}
        self.movie_rated_by_users: Dict[int, Dict[int, Dict[str, Any]]] = {}

        # movie_id -> set of genre names
        self.movie_in_genre: Dict[int, Set[str]] = {}
        # genre name -> set of movie_ids
        self.genre_to_movies: Dict[str, Set[int]] = {}

        # movie_id -> tag_id -> relevance
        self.movie_has_genome_tag: Dict[int, Dict[int, float]] = {}
        # tag_id -> movie_id -> relevance
        self.genome_tag_to_movies: Dict[int, Dict[int, float]] = {}

        # Bộ nhớ đệm số lượng phim đã thích của user (O(1) lookup cho Collaborative P3)
        self.user_liked_counts: Dict[int, int] = {}

    def __setstate__(self, state):
        self.__dict__.update(state)
        if not hasattr(self, "user_liked_counts"):
            self.user_liked_counts = {
                u: sum(1 for r in rdict.values() if r.get("rating", 0) >= 3.5)
                for u, rdict in getattr(self, "user_rated_movie", {}).items()
            }

    # =========================================================================
    # CÁC THAO TÁC HỢP NHẤT DỮ LIỆU CƠ BẢN (IDEMPOTENT MERGE)
    # =========================================================================

    def merge_user(self, user_id: int, metadata: Optional[Dict[str, Any]] = None):
        """Hợp nhất node người dùng (Idempotent)."""
        if user_id not in self.users:
            self.users[user_id] = {"userId": user_id, **(metadata or {})}
            self.user_rated_movie[user_id] = {}

    def merge_movie(self, movie_id: int, title: str, genres_raw: str = "", year: Optional[int] = None):
        """Hợp nhất node phim (Idempotent)."""
        self.movies[movie_id] = {
            "movieId": movie_id,
            "title": title,
            "genresRaw": genres_raw,
            "year": year
        }
        if movie_id not in self.movie_rated_by_users:
            self.movie_rated_by_users[movie_id] = {}
        if movie_id not in self.movie_in_genre:
            self.movie_in_genre[movie_id] = set()
        if movie_id not in self.movie_has_genome_tag:
            self.movie_has_genome_tag[movie_id] = {}

    def merge_genre(self, name: str):
        """Hợp nhất node thể loại (Idempotent)."""
        if name not in self.genres:
            self.genres[name] = {"name": name}
            self.genre_to_movies[name] = set()

    def merge_genome_tag(self, tag_id: int, name: str):
        """Hợp nhất node thẻ đặc trưng genome (Idempotent)."""
        self.genome_tags[tag_id] = {"tagId": tag_id, "name": name}
        if tag_id not in self.genome_tag_to_movies:
            self.genome_tag_to_movies[tag_id] = {}

    def merge_movie_genre(self, movie_id: int, genre_name: str):
        """Tạo liên kết có hướng hai chiều Movie <-> Genre."""
        if movie_id not in self.movies:
            self.merge_movie(movie_id, f"Movie #{movie_id}")
        if genre_name not in self.genres:
            self.merge_genre(genre_name)

        self.movie_in_genre[movie_id].add(genre_name)
        self.genre_to_movies[genre_name].add(movie_id)

    def merge_genome_score(self, movie_id: int, tag_id: int, relevance: float):
        """Tạo liên kết có trọng số Movie <-> GenomeTag."""
        if movie_id not in self.movies:
            self.merge_movie(movie_id, f"Movie #{movie_id}")
        if tag_id not in self.genome_tags:
            self.merge_genome_tag(tag_id, f"Tag #{tag_id}")

        self.movie_has_genome_tag[movie_id][tag_id] = float(relevance)
        self.genome_tag_to_movies[tag_id][movie_id] = float(relevance)

    def merge_rating(self, user_id: int, movie_id: int, rating: float, timestamp: int = 0):
        """Tạo liên kết đánh giá User <-> Movie."""
        if user_id not in self.users:
            self.merge_user(user_id)
        if movie_id not in self.movies:
            self.merge_movie(movie_id, f"Movie #{movie_id}")

        edge_data = {"rating": float(rating), "timestamp": int(timestamp)}
        self.user_rated_movie[user_id][movie_id] = edge_data
        self.movie_rated_by_users[movie_id][user_id] = edge_data
        if float(rating) >= 3.5:
            self.user_liked_counts[user_id] = self.user_liked_counts.get(user_id, 0) + 1

    # =========================================================================
    # CONTRACT INTERFACE CỦA EMBEDDED KNOWLEDGE GRAPH
    # =========================================================================

    def get_user_liked_movies(self, user_id: int, min_rating: float = 3.5) -> Dict[int, float]:
        """Lấy danh sách các phim user đã thích (rating >= min_rating)."""
        if user_id not in self.user_rated_movie:
            return {}
        return {
            mid: rinfo["rating"]
            for mid, rinfo in self.user_rated_movie[user_id].items()
            if rinfo["rating"] >= min_rating
        }

    def get_movie_genres(self, movie_id: int) -> Set[str]:
        """Lấy tập thể loại của một phim."""
        return set(self.movie_in_genre.get(movie_id, set()))

    def get_movies_by_genre(self, genre: str) -> Set[int]:
        """Lấy tập các phim thuộc một thể loại."""
        return set(self.genre_to_movies.get(genre, set()))

    def get_movie_top_genome_tags(self, movie_id: int, top_m: int = 20) -> Dict[int, float]:
        """Lấy Top-M thẻ đặc trưng ngữ nghĩa cao nhất của phim."""
        tags = self.movie_has_genome_tag.get(movie_id, {})
        if not tags:
            return {}
        # Sắp xếp theo relevance DESC, tag_id ASC
        sorted_tags = sorted(tags.items(), key=lambda x: (-x[1], x[0]))
        return dict(sorted_tags[:top_m])

    def get_movies_by_genome_tag(self, tag_id: int) -> Dict[int, float]:
        """Lấy danh sách các phim chứa thẻ đặc trưng tag_id kèm trọng số liên quan."""
        return dict(self.genome_tag_to_movies.get(tag_id, {}))

    def get_similar_users(self, user_id: int, top_k: int = 50) -> List[Tuple[int, float]]:
        """
        Tìm top_k người dùng láng giềng có gu tương đồng dựa trên Overlap Cosine của các phim đã thích.
        """
        liked = self.get_user_liked_movies(user_id)
        if not liked:
            return []

        user_liked_len = len(liked)
        neighbor_shared: Dict[int, int] = {}

        for anchor_mid in liked:
            for peer_id, rinfo in self.movie_rated_by_users.get(anchor_mid, {}).items():
                if peer_id != user_id and rinfo["rating"] >= 3.5:
                    neighbor_shared[peer_id] = neighbor_shared.get(peer_id, 0) + 1

        sims: List[Tuple[int, float]] = []
        for peer_id, shared_count in neighbor_shared.items():
            peer_ratings = self.user_rated_movie.get(peer_id, {})
            peer_liked_len = sum(1 for r in peer_ratings.values() if r["rating"] >= 3.5)
            if peer_liked_len > 0:
                cosine = shared_count / math.sqrt(user_liked_len * peer_liked_len)
                sims.append((peer_id, cosine))

        sims.sort(key=lambda x: (-x[1], x[0]))
        return sims[:top_k]

    # =========================================================================
    # ĐỒNG BỘ SQLITE APP_STATE.DB (LIVE USER RATINGS SYNC)
    # =========================================================================

    def sync_with_sqlite(self, db_path: Path):
        """
        Đọc và đồng bộ tức thời các đánh giá phim từ bảng user_ratings trong SQLite app_state.db.
        Cho phép người dùng tương tác trong web demo lập tức phản ánh vào KG mà không cần restart server.
        """
        db_file = Path(db_path)
        if not db_file.exists():
            return

        try:
            conn = sqlite3.connect(str(db_file), timeout=5.0)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 1. Đọc user_ratings
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_ratings'")
            if cursor.fetchone():
                cursor.execute("SELECT user_id, movie_id, rating, created_at FROM user_ratings")
                rows = cursor.fetchall()
                for row in rows:
                    raw_uid = row["user_id"]
                    try:
                        uid = int(raw_uid)
                    except ValueError:
                        # Với chuỗi không phải số như 'demo_user_1', map hash xác định
                        uid = abs(hash(raw_uid)) % 1000000 + 1000000
                    mid = int(row["movie_id"])
                    rating = float(row["rating"])
                    ts = int(row["created_at"]) if row["created_at"] is not None else 0
                    self.merge_rating(uid, mid, rating, ts)

            # 2. Đọc demo_users nếu có
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='demo_users'")
            if cursor.fetchone():
                cursor.execute("SELECT user_id, username, display_name FROM demo_users")
                users = cursor.fetchall()
                for u in users:
                    raw_uid = u["user_id"]
                    try:
                        uid = int(raw_uid)
                    except ValueError:
                        uid = abs(hash(raw_uid)) % 1000000 + 1000000
                    self.merge_user(uid, {"username": u["username"], "displayName": u["display_name"]})

            conn.close()
            logger.info("Đã đồng bộ thành công dữ liệu tương tác từ %s vào EmbeddedKnowledgeGraph.", db_file)
        except Exception as exc:
            logger.warning("Không thể đồng bộ SQLite %s: %s", db_file, exc)

    # =========================================================================
    # NẠP DỮ LIỆU TỪ PARQUET (PROCESSED DATASET)
    # =========================================================================

    def load_from_parquet(
        self,
        data_root: Path,
        max_users: int = 2000,
        top_m_genome: int = 20,
        target_user_ids: Optional[Set[int]] = None
    ):
        """
        Nạp toàn bộ catalog phim, thể loại, genome tags, Top-M genome scores và một cohort người dùng.
        """
        from recommender.kg.data_access import DataAccess
        da = DataAccess(data_root)

        # 1. Nạp phim
        logger.info("Nạp danh mục phim từ Parquet...")
        for batch in da.stream_movies(batch_size=10000):
            for row in batch:
                self.merge_movie(row["movieId"], row["title"], row.get("genresRaw", ""))

        # 2. Nạp thể loại
        logger.info("Nạp quan hệ thể loại...")
        for batch in da.stream_movie_genres(batch_size=10000):
            for row in batch:
                self.merge_movie_genre(row["movieId"], row["genre"])

        # 3. Nạp genome tags
        logger.info("Nạp danh mục genome tags...")
        for batch in da.stream_genome_tags(batch_size=5000):
            for row in batch:
                self.merge_genome_tag(row["tagId"], row["tag"])

        # 4. Nạp Top-M genome scores
        logger.info("Nạp Top-%d genome scores...", top_m_genome)
        for batch in da.stream_top_m_genome_scores(top_m=top_m_genome, batch_size=10000):
            for row in batch:
                self.merge_genome_score(row["movieId"], row["tagId"], row["relevance"])

        # 5. Xác định cohort users cần nạp
        user_ids_to_load: Set[int] = set()
        if target_user_ids:
            user_ids_to_load.update(target_user_ids)

        # Mặc định thêm các user mẫu phổ biến (User 1, 2, 3)
        user_ids_to_load.update([1, 2, 3])

        # Lấy thêm users từ tập train nếu số lượng chưa đạt max_users
        if len(user_ids_to_load) < max_users:
            import pyarrow.dataset as ds
            train_path = Path(data_root) / "splits" / "train"
            if train_path.exists():
                dataset = ds.dataset(str(train_path), format="parquet")
                scanner = dataset.scanner(columns=["userId"], batch_size=20000)
                for b in scanner.to_batches():
                    u_arr = b.to_pydict()["userId"]
                    user_ids_to_load.update(u_arr)
                    if len(user_ids_to_load) >= max_users:
                        break

        # 6. Nạp ratings của cohort users
        logger.info("Nạp ratings cho %d users từ splits/train...", len(user_ids_to_load))
        for batch in da.stream_train_ratings(user_ids=user_ids_to_load, batch_size=10000):
            for row in batch:
                self.merge_rating(row["userId"], row["movieId"], row["rating"], row.get("timestamp", 0))

        logger.info("Đã nạp hoàn tất EmbeddedKnowledgeGraph: %s", self.get_counts())

    # =========================================================================
    # TRÍCH XUẤT CẤU TRÚC SUBGRAPH GIẢI THÍCH (INTERFACE CONTRACT REQUIREMENT)
    # =========================================================================

    def extract_subgraph(self, user_id: int, candidate_movie_id: int) -> Dict[str, Any]:
        """
        Trích xuất cấu trúc mạng con (Subgraph: nodes, edges, weights) phục vụ trực quan hóa tương tác
        theo đúng Interface Contract trong PROJECT.md:
        - Nút Người dùng: Vàng Hổ Phách #F59E0B
        - Nút Phim Đã thích: Xanh Cyan #06B6D4
        - Nút Thể loại: Lục Bảo #10B981
        - Nút Thẻ Tâm trạng Genome: Xanh Ngọc #14B8A6
        - Nút Phim Đề xuất: Tím Thạch Anh #8B5CF6
        """
        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []
        node_ids_seen: Set[str] = set()

        cand_movie = self.movies.get(candidate_movie_id, {})
        cand_title = cand_movie.get("title", f"Movie #{candidate_movie_id}")
        cand_genres = self.get_movie_genres(candidate_movie_id)
        cand_tags = self.get_movie_top_genome_tags(candidate_movie_id, top_m=10)

        # 1. Thêm Node Khán giả (User)
        user_node_id = f"user_{user_id}"
        nodes.append({
            "id": user_node_id,
            "label": f"Khán giả #{user_id}",
            "type": "USER",
            "color": "#F59E0B"
        })
        node_ids_seen.add(user_node_id)

        # 2. Thêm Node Phim Đề xuất (Candidate Movie)
        cand_node_id = f"cand_{candidate_movie_id}"
        nodes.append({
            "id": cand_node_id,
            "label": cand_title,
            "type": "RECOMMENDED_MOVIE",
            "movieId": candidate_movie_id,
            "color": "#8B5CF6"
        })
        node_ids_seen.add(cand_node_id)

        # 3. Lấy lịch sử phim đã thích của user
        liked_movies = self.get_user_liked_movies(user_id, min_rating=3.5)

        # Bằng chứng Metapath P1 (Genre) & P2 (Genome)
        p1_found = False
        p2_found = False
        p3_found = False

        shared_genre_names: List[str] = []
        shared_tag_names: List[str] = []

        # Tìm các phim đã thích có giao thoa cao nhất với candidate
        scored_liked_movies: List[Tuple[int, float, Set[str], Dict[int, float]]] = []
        for src_mid, rating in liked_movies.items():
            src_genres = self.get_movie_genres(src_mid)
            common_g = src_genres & cand_genres
            src_tags = self.get_movie_top_genome_tags(src_mid, top_m=10)
            common_t = set(src_tags.keys()) & set(cand_tags.keys())

            score = len(common_g) * 0.5 + len(common_t) * 0.8
            if score > 0:
                scored_liked_movies.append((src_mid, rating, common_g, {t: src_tags[t] * cand_tags[t] for t in common_t}))

        scored_liked_movies.sort(key=lambda x: -x[1])
        top_liked = scored_liked_movies[:2]  # Lấy tối đa 2 phim đã thích tiêu biểu nhất

        for src_mid, rating, common_g, common_t_dict in top_liked:
            src_movie = self.movies.get(src_mid, {})
            src_title = src_movie.get("title", f"Movie #{src_mid}")
            src_node_id = f"movie_{src_mid}"

            if src_node_id not in node_ids_seen:
                nodes.append({
                    "id": src_node_id,
                    "label": src_title,
                    "type": "LIKED_MOVIE",
                    "movieId": src_mid,
                    "rating": rating,
                    "color": "#06B6D4"
                })
                node_ids_seen.add(src_node_id)

            # Cạnh User -> Liked Movie
            edges.append({
                "from": user_node_id,
                "to": src_node_id,
                "label": f"Đã thích ({rating}★)",
                "weight": round(rating / 5.0, 2),
                "type": "RATED"
            })

            # Nút & Cạnh Thể loại (P1)
            for g_name in list(common_g)[:2]:
                g_node_id = f"genre_{abs(hash(g_name)) % 100000}"
                if g_node_id not in node_ids_seen:
                    nodes.append({
                        "id": g_node_id,
                        "label": g_name,
                        "type": "GENRE",
                        "color": "#10B981"
                    })
                    node_ids_seen.add(g_node_id)

                edges.append({
                    "from": src_node_id,
                    "to": g_node_id,
                    "label": "Thể loại",
                    "weight": 0.72,
                    "type": "HAS_GENRE"
                })
                edges.append({
                    "from": g_node_id,
                    "to": cand_node_id,
                    "label": "Đồng thể loại",
                    "weight": 0.72,
                    "type": "HAS_GENRE"
                })
                p1_found = True
                if g_name not in shared_genre_names:
                    shared_genre_names.append(g_name)

            # Nút & Cạnh Genome Tag (P2)
            sorted_common_tags = sorted(common_t_dict.items(), key=lambda x: -x[1])
            for t_id, prod_rel in sorted_common_tags[:2]:
                t_name = self.genome_tags.get(t_id, {}).get("name", f"tag_{t_id}")
                t_node_id = f"tag_{t_id}"
                if t_node_id not in node_ids_seen:
                    nodes.append({
                        "id": t_node_id,
                        "label": t_name,
                        "type": "GENOME_TAG",
                        "relevance": round(cand_tags.get(t_id, 0.0), 3),
                        "color": "#14B8A6"
                    })
                    node_ids_seen.add(t_node_id)

                edges.append({
                    "from": src_node_id,
                    "to": t_node_id,
                    "label": f"rel = {round(self.movie_has_genome_tag.get(src_mid, {}).get(t_id, 0.9), 2)}",
                    "weight": round(self.movie_has_genome_tag.get(src_mid, {}).get(t_id, 0.9), 2),
                    "type": "HAS_TAG"
                })
                edges.append({
                    "from": t_node_id,
                    "to": cand_node_id,
                    "label": f"rel = {round(cand_tags.get(t_id, 0.9), 2)}",
                    "weight": round(cand_tags.get(t_id, 0.9), 2),
                    "type": "HAS_TAG"
                })
                p2_found = True
                if t_name not in shared_tag_names:
                    shared_tag_names.append(t_name)

        # Nếu không có liked movie nào khớp (ví dụ cold-start hoặc chưa có liên kết trực tiếp),
        # kết nối trực tiếp candidate với các thể loại tiêu biểu của candidate
        if not top_liked:
            for g_name in list(cand_genres)[:2]:
                g_node_id = f"genre_{abs(hash(g_name)) % 100000}"
                if g_node_id not in node_ids_seen:
                    nodes.append({
                        "id": g_node_id,
                        "label": g_name,
                        "type": "GENRE",
                        "color": "#10B981"
                    })
                    node_ids_seen.add(g_node_id)
                edges.append({
                    "from": g_node_id,
                    "to": cand_node_id,
                    "label": "Thể loại đặc trưng",
                    "weight": 0.8,
                    "type": "HAS_GENRE"
                })
                shared_genre_names.append(g_name)

        # Xây dựng lời giải thích học thuật (Academic Explanation)
        parts = []
        if shared_genre_names:
            parts.append(f"Metapath P1 (Đồng thể loại {', '.join(shared_genre_names)}, đóng góp 35%)")
        if shared_tag_names:
            parts.append(f"Metapath P2 (Cùng mang đặc trưng ngữ nghĩa '{', '.join(shared_tag_names)}', đóng góp 45%)")
        if not parts:
            parts.append("Đặc trưng thể loại danh mục phù hợp sở thích tiềm năng (đóng góp 20%)")

        explanation_str = f"Được đề xuất bởi tổ hợp {' và '.join(parts)}."

        return {
            "nodes": nodes,
            "edges": edges,
            "academic_explanation": explanation_str
        }

    # =========================================================================
    # THỐNG KÊ QUY MÔ ĐỒ THỊ
    # =========================================================================

    def get_counts(self) -> Dict[str, int]:
        total_rated = sum(len(m) for m in self.user_rated_movie.values())
        total_in_genre = sum(len(g) for g in self.movie_in_genre.values())
        total_genome = sum(len(t) for t in self.movie_has_genome_tag.values())
        return {
            "users": len(self.users),
            "movies": len(self.movies),
            "genres": len(self.genres),
            "genome_tags": len(self.genome_tags),
            "rated_edges": total_rated,
            "in_genre_edges": total_in_genre,
            "has_genome_tag_edges": total_genome,
        }
