"""
Chương trình nạp dữ liệu vào Đồ thị tri thức (Knowledge Graph Importer)
Hỗ trợ cả Neo4j Server (live) và In-Memory Graph Backend (deterministic testing).
Tuân thủ nghiêm ngặt nguyên tắc: Node trước, Edge sau; UNWIND + MERGE idempotent; Batch transaction.
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple, Optional

# UTF-8 stdout configuration for Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Project path resolution
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from recommender.kg.config import load_kg_config, KGConfig
from recommender.kg.data_access import DataAccess
from recommender.kg.checks import verify_idempotency, verify_split_isolation
from tests.kg.fixtures.synthetic_data import (
    SYNTHETIC_USERS, SYNTHETIC_MOVIES, SYNTHETIC_GENRES,
    SYNTHETIC_GENOME_TAGS, SYNTHETIC_MOVIE_GENRES,
    SYNTHETIC_GENOME_SCORES, SYNTHETIC_TRAIN_RATINGS,
    EXPECTED_COUNTS
)


class InMemoryGraph:
    """
    Đồ thị bộ nhớ trong (In-Memory Graph) hỗ trợ:
    - Ràng buộc tính duy nhất (Unique constraints trên User.userId, Movie.movieId, Genre.name, GenomeTag.tagId)
    - Lưu trữ quan hệ: RATED, IN_GENRE, HAS_GENOME_TAG
    - Idempotent merge (nạp 2 lần không tăng cạnh/node)
    - Khai phá các metapaths P1, P2, P3
    """
    def __init__(self):
        self.users: Dict[int, Dict[str, Any]] = {}
        self.movies: Dict[int, Dict[str, Any]] = {}
        self.genres: Dict[str, Dict[str, Any]] = {}
        self.genome_tags: Dict[int, Dict[str, Any]] = {}

        # Edges
        # user_id -> dict of movie_id -> {rating, timestamp}
        self.user_rated_movie: Dict[int, Dict[int, Dict[str, Any]]] = {}
        # movie_id -> dict of user_id -> {rating, timestamp} (reverse index for collab P3)
        self.movie_rated_by_users: Dict[int, Dict[int, Dict[str, Any]]] = {}

        # movie_id -> set of genre_name
        self.movie_in_genre: Dict[int, Set[str]] = {}
        # genre_name -> set of movie_id
        self.genre_to_movies: Dict[str, Set[int]] = {}

        # movie_id -> dict of tag_id -> relevance
        self.movie_has_genome_tag: Dict[int, Dict[int, float]] = {}
        # tag_id -> dict of movie_id -> relevance
        self.genome_tag_to_movies: Dict[int, Dict[int, float]] = {}

    def merge_user(self, user_id: int):
        if user_id not in self.users:
            self.users[user_id] = {"userId": user_id}
            self.user_rated_movie[user_id] = {}

    def merge_movie(self, movie_id: int, title: str, genres_raw: str = ""):
        self.movies[movie_id] = {"movieId": movie_id, "title": title, "genresRaw": genres_raw}
        if movie_id not in self.movie_rated_by_users:
            self.movie_rated_by_users[movie_id] = {}
        if movie_id not in self.movie_in_genre:
            self.movie_in_genre[movie_id] = set()
        if movie_id not in self.movie_has_genome_tag:
            self.movie_has_genome_tag[movie_id] = {}

    def merge_genre(self, name: str):
        if name not in self.genres:
            self.genres[name] = {"name": name}
            self.genre_to_movies[name] = set()

    def merge_genome_tag(self, tag_id: int, name: str):
        self.genome_tags[tag_id] = {"tagId": tag_id, "name": name}
        if tag_id not in self.genome_tag_to_movies:
            self.genome_tag_to_movies[tag_id] = {}

    def merge_movie_genre(self, movie_id: int, genre_name: str):
        if movie_id not in self.movies or genre_name not in self.genres:
            return
        self.movie_in_genre[movie_id].add(genre_name)
        self.genre_to_movies[genre_name].add(movie_id)

    def merge_genome_score(self, movie_id: int, tag_id: int, relevance: float):
        if movie_id not in self.movies or tag_id not in self.genome_tags:
            return
        self.movie_has_genome_tag[movie_id][tag_id] = relevance
        self.genome_tag_to_movies[tag_id][movie_id] = relevance

    def merge_rating(self, user_id: int, movie_id: int, rating: float, timestamp: int):
        if user_id not in self.users or movie_id not in self.movies:
            return
        edge_data = {"rating": rating, "timestamp": timestamp}
        self.user_rated_movie[user_id][movie_id] = edge_data
        self.movie_rated_by_users[movie_id][user_id] = edge_data

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


class Neo4jGraph:
    """Đồ thị thực thi trên Neo4j Community thông qua official driver."""
    def __init__(self, uri: str, auth: Tuple[str, str], database: str = "neo4j"):
        from neo4j import GraphDatabase
        self.driver = GraphDatabase.driver(uri, auth=auth)
        self.database = database

    def close(self):
        self.driver.close()

    def execute_constraints(self):
        from recommender.kg.queries import ALL_CONSTRAINTS
        with self.driver.session(database=self.database) as session:
            for query in ALL_CONSTRAINTS:
                session.run(query)

    def merge_users_batch(self, batch: List[Dict[str, Any]]):
        from recommender.kg.queries import IMPORT_USERS_BATCH
        with self.driver.session(database=self.database) as session:
            session.run(IMPORT_USERS_BATCH, batch=batch)

    def merge_movies_batch(self, batch: List[Dict[str, Any]]):
        from recommender.kg.queries import IMPORT_MOVIES_BATCH
        with self.driver.session(database=self.database) as session:
            session.run(IMPORT_MOVIES_BATCH, batch=batch)

    def merge_genres_batch(self, batch: List[Dict[str, Any]]):
        from recommender.kg.queries import IMPORT_GENRES_BATCH
        with self.driver.session(database=self.database) as session:
            session.run(IMPORT_GENRES_BATCH, batch=batch)

    def merge_genome_tags_batch(self, batch: List[Dict[str, Any]]):
        from recommender.kg.queries import IMPORT_GENOME_TAGS_BATCH
        with self.driver.session(database=self.database) as session:
            session.run(IMPORT_GENOME_TAGS_BATCH, batch=batch)

    def merge_movie_genres_batch(self, batch: List[Dict[str, Any]]):
        from recommender.kg.queries import IMPORT_MOVIE_GENRES_BATCH
        with self.driver.session(database=self.database) as session:
            session.run(IMPORT_MOVIE_GENRES_BATCH, batch=batch)

    def merge_genome_scores_batch(self, batch: List[Dict[str, Any]]):
        from recommender.kg.queries import IMPORT_GENOME_SCORES_BATCH
        with self.driver.session(database=self.database) as session:
            session.run(IMPORT_GENOME_SCORES_BATCH, batch=batch)

    def merge_ratings_batch(self, batch: List[Dict[str, Any]]):
        from recommender.kg.queries import IMPORT_TRAIN_RATINGS_BATCH
        with self.driver.session(database=self.database) as session:
            session.run(IMPORT_TRAIN_RATINGS_BATCH, batch=batch)

    def get_counts(self) -> Dict[str, int]:
        from recommender.kg.queries import QUERY_GRAPH_COUNTS
        with self.driver.session(database=self.database) as session:
            res = session.run(QUERY_GRAPH_COUNTS).single()
            if res:
                return {
                    "users": res["userCount"],
                    "movies": res["movieCount"],
                    "genres": res["genreCount"],
                    "genome_tags": res["tagCount"],
                    "rated_edges": res["ratedCount"],
                    "in_genre_edges": res["inGenreCount"],
                    "has_genome_tag_edges": res["hasGenomeTagCount"],
                }
        return {}


def import_synthetic_data(graph: Any) -> Dict[str, int]:
    """Nạp dữ liệu synthetic fixture vào đồ thị."""
    # 1. Nodes trước
    if isinstance(graph, InMemoryGraph):
        for u in SYNTHETIC_USERS:
            graph.merge_user(u["userId"])
        for m in SYNTHETIC_MOVIES:
            graph.merge_movie(m["movieId"], m["title"], m.get("genresRaw", ""))
        for g in SYNTHETIC_GENRES:
            graph.merge_genre(g["name"])
        for t in SYNTHETIC_GENOME_TAGS:
            graph.merge_genome_tag(t["tagId"], t["tag"])

        # 2. Edges sau
        for mg in SYNTHETIC_MOVIE_GENRES:
            graph.merge_movie_genre(mg["movieId"], mg["genre"])
        for gs in SYNTHETIC_GENOME_SCORES:
            graph.merge_genome_score(gs["movieId"], gs["tagId"], gs["relevance"])
        for r in SYNTHETIC_TRAIN_RATINGS:
            graph.merge_rating(r["userId"], r["movieId"], r["rating"], r["timestamp"])
    else:
        # Neo4j backend
        graph.execute_constraints()
        graph.merge_users_batch(SYNTHETIC_USERS)
        graph.merge_movies_batch(SYNTHETIC_MOVIES)
        graph.merge_genres_batch(SYNTHETIC_GENRES)
        graph.merge_genome_tags_batch([{"tagId": t["tagId"], "name": t["tag"]} for t in SYNTHETIC_GENOME_TAGS])
        graph.merge_movie_genres_batch(SYNTHETIC_MOVIE_GENRES)
        graph.merge_genome_scores_batch(SYNTHETIC_GENOME_SCORES)
        graph.merge_ratings_batch(SYNTHETIC_TRAIN_RATINGS)

    return graph.get_counts()


def import_pilot_data(
    graph: Any,
    data_access: DataAccess,
    user_cohort: Set[int],
    top_m: int = 20,
    batch_size: int = 5000
) -> Dict[str, int]:
    """Nạp dữ liệu pilot thật MovieLens trên tập cohort user xác định."""
    print(f"[*] Bắt đầu nạp pilot data cho {len(user_cohort)} users...")

    # 1. Nạp Users
    user_batch = [{"userId": uid} for uid in user_cohort]
    if isinstance(graph, InMemoryGraph):
        for u in user_batch:
            graph.merge_user(u["userId"])
    else:
        graph.merge_users_batch(user_batch)

    # 2. Nạp Train Ratings của cohort users
    pilot_movie_ids: Set[int] = set()
    total_ratings = 0
    for r_batch in data_access.stream_train_ratings(user_ids=user_cohort, batch_size=batch_size):
        total_ratings += len(r_batch)
        for r in r_batch:
            pilot_movie_ids.add(r["movieId"])
        if isinstance(graph, InMemoryGraph):
            for r in r_batch:
                # Cần đảm bảo movie node tồn tại
                if r["movieId"] not in graph.movies:
                    graph.merge_movie(r["movieId"], f"Movie #{r['movieId']}")
                graph.merge_rating(r["userId"], r["movieId"], r["rating"], r["timestamp"])
        else:
            graph.merge_ratings_batch(r_batch)
    print(f"  -> Đã nạp {total_ratings} ratings tương ứng với {len(pilot_movie_ids)} phim được đánh giá.")

    # 3. Nạp Movies & Genres
    movie_count = 0
    for m_batch in data_access.stream_movies(batch_size=batch_size):
        movie_count += len(m_batch)
        if isinstance(graph, InMemoryGraph):
            for m in m_batch:
                graph.merge_movie(m["movieId"], m["title"], m.get("genresRaw", ""))
        else:
            graph.merge_movies_batch(m_batch)
    print(f"  -> Đã nạp {movie_count} Movies.")

    # Nạp Genres & Movie-Genre edges
    genre_set: Set[str] = set()
    for mg_batch in data_access.stream_movie_genres(batch_size=batch_size):
        for mg in mg_batch:
            genre_set.add(mg["genre"])
        if isinstance(graph, InMemoryGraph):
            for g_name in genre_set:
                graph.merge_genre(g_name)
            for mg in mg_batch:
                graph.merge_movie_genre(mg["movieId"], mg["genre"])
        else:
            graph.merge_genres_batch([{"name": g} for g in genre_set])
            graph.merge_movie_genres_batch(mg_batch)
    print(f"  -> Đã nạp {len(genre_set)} Genres.")

    # 4. Nạp Genome Tags & Top-M Scores
    tag_count = 0
    for t_batch in data_access.stream_genome_tags(batch_size=batch_size):
        tag_count += len(t_batch)
        if isinstance(graph, InMemoryGraph):
            for t in t_batch:
                graph.merge_genome_tag(t["tagId"], t["tag"])
        else:
            graph.merge_genome_tags_batch([{"tagId": t["tagId"], "name": t["tag"]} for t in t_batch])
    print(f"  -> Đã nạp {tag_count} GenomeTags.")

    genome_edge_count = 0
    for gs_batch in data_access.stream_top_m_genome_scores(
        top_m=top_m,
        movie_ids=pilot_movie_ids,
        batch_size=batch_size
    ):
        genome_edge_count += len(gs_batch)
        if isinstance(graph, InMemoryGraph):
            for gs in gs_batch:
                graph.merge_genome_score(gs["movieId"], gs["tagId"], gs["relevance"])
        else:
            graph.merge_genome_scores_batch(gs_batch)
    print(f"  -> Đã nạp {genome_edge_count} cạnh HAS_GENOME_TAG (Top-{top_m}).")

    return graph.get_counts()


def main():
    parser = argparse.ArgumentParser(description="Knowledge Graph Importer CLI")
    parser.add_argument("--mode", choices=["synthetic", "pilot", "full"], default="synthetic")
    parser.add_argument("--users", type=int, default=200, help="Số users cho pilot cohort")
    parser.add_argument("--top-m", type=int, default=20, help="Top-M genome tags")
    parser.add_argument("--backend", choices=["auto", "neo4j", "inmemory"], default="auto")
    args = parser.parse_args()

    config = load_kg_config()
    print("=" * 70)
    print("MOODGRAPH TASK 3B: KNOWLEDGE GRAPH IMPORTER")
    print(f"Mode: {args.mode} | Top-M: {args.top_m} | Backend: {args.backend}")
    print("=" * 70)

    # Lựa chọn backend
    backend = None
    if args.backend in ["auto", "neo4j"]:
        try:
            from neo4j import GraphDatabase
            driver = GraphDatabase.driver(config.neo4j_uri, auth=(config.neo4j_user, config.neo4j_password))
            driver.verify_connectivity()
            driver.close()
            backend = Neo4jGraph(config.neo4j_uri, auth=(config.neo4j_user, config.neo4j_password), database=config.neo4j_database)
            print(f"[OK] Sử dụng Live Neo4j Backend tại {config.neo4j_uri}")
        except Exception as exc:
            if args.backend == "neo4j":
                print(f"[ERROR] Không thể kết nối Neo4j: {exc}")
                sys.exit(1)
            print(f"[WARN] Neo4j offline ({exc}). Chuyển sang InMemoryGraph Backend.")
            backend = InMemoryGraph()
    else:
        backend = InMemoryGraph()

    t0 = time.time()
    if args.mode == "synthetic":
        print("[*] Thực hiện LẦN NẠP 1 (Run 1)...")
        counts_1 = import_synthetic_data(backend)
        print(f"  -> Kết quả Lần 1: {counts_1}")

        print("[*] Thực hiện LẦN NẠP 2 (Run 2 - Idempotency Check)...")
        counts_2 = import_synthetic_data(backend)
        print(f"  -> Kết quả Lần 2: {counts_2}")

        is_idempotent, mismatches = verify_idempotency(counts_1, counts_2)
        if not is_idempotent:
            print(f"[FAIL] Thất bại Idempotency: {mismatches}")
            sys.exit(1)
        print("[PASS] Idempotency kiểm tra THÀNH CÔNG: counts_1 == counts_2.")

    elif args.mode == "pilot":
        data_access = DataAccess(config.data_root)
        # Chọn cohort xác định: các users đầu tiên theo userId
        user_cohort = set(range(1, args.users + 1))
        counts = import_pilot_data(backend, data_access, user_cohort, top_m=args.top_m, batch_size=config.batch_size)
        print(f"[PASS] Hoàn thành nạp Pilot Graph: {counts}")

    print(f"Thời gian thực thi: {time.time() - t0:.2f}s")


if __name__ == "__main__":
    main()
