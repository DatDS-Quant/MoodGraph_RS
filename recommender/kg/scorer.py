"""
Thuật toán tính điểm theo đường đi trên Đồ thị tri thức (Path-based Weighted Evidence Scorer).
Hiện thực tối ưu hóa cao cho các đường suy luận:
- P1: Genre Metapath
- P2: Genome Metapath
- P3: Collaborative Graph Metapath
Tách biệt giai đoạn tích lũy điểm số (float accumulation) và trích xuất bằng chứng (top-candidate evidence extraction)
để đạt hiệu năng xử lý < 0.2s / user trên quy mô catalog lớn (62,000+ movies).
"""

import math
from typing import Dict, Any, List, Set, Tuple, Optional
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class EvidenceItem:
    path_type: str  # "GENRE", "GENOME", "COLLABORATIVE"
    source_movie_id: Optional[int] = None
    source_movie_title: Optional[str] = None
    shared_entity_type: Optional[str] = None
    shared_entity_key: Any = None
    shared_entity_name: Optional[str] = None
    source_rating: Optional[float] = None
    neighbor_user_id: Optional[int] = None
    neighbor_rating: Optional[float] = None
    contribution: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "path_type": self.path_type,
            "contribution": round(self.contribution, 4)
        }
        if self.source_movie_id is not None:
            d["sourceMovieId"] = self.source_movie_id
        if self.source_movie_title is not None:
            d["sourceMovieTitle"] = self.source_movie_title
        if self.shared_entity_type is not None:
            d["sharedEntity"] = {
                "type": self.shared_entity_type,
                "key": self.shared_entity_key
            }
            if self.shared_entity_name is not None:
                d["sharedEntity"]["name"] = self.shared_entity_name
        if self.source_rating is not None:
            d["sourceRating"] = self.source_rating
        if self.neighbor_user_id is not None:
            d["neighborUserId"] = self.neighbor_user_id
        if self.neighbor_rating is not None:
            d["neighborRating"] = self.neighbor_rating
        return d


class PathBasedScorer:
    def __init__(
        self,
        min_liked_rating: float = 3.5,
        alpha_genre: float = 0.35,
        beta_genome: float = 0.45,
        gamma_collab: float = 0.20,
        max_neighbors: int = 50,
        max_evidence_per_candidate: int = 5
    ):
        self.min_liked_rating = min_liked_rating
        total_w = alpha_genre + beta_genome + gamma_collab
        self.alpha = alpha_genre / total_w
        self.beta = beta_genome / total_w
        self.gamma = gamma_collab / total_w
        self.max_neighbors = max_neighbors
        self.max_evidence_per_candidate = max_evidence_per_candidate

    def preference_weight(self, rating: float) -> float:
        """Hàm trọng số ưa thích tích cực: w(r) = max(0, (r - 3.0) / 2.0)."""
        return max(0.0, (rating - 3.0) / 2.0)

    def compute_user_candidates(
        self,
        user_id: int,
        graph: Any,
        exclude_movie_ids: Optional[Set[int]] = None,
        enable_p1: bool = True,
        enable_p2: bool = True,
        enable_p3: bool = True,
        top_n: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Sinh và tính điểm ứng viên cho người dùng qua các đường suy luận P1, P2, P3.
        """
        seen_movies: Set[int] = set()
        user_history: Dict[int, float] = {}

        # 1. Trích xuất lịch sử xem của user từ graph
        if hasattr(graph, "user_rated_movie"):
            if user_id in graph.user_rated_movie:
                for mid, rinfo in graph.user_rated_movie[user_id].items():
                    seen_movies.add(mid)
                    user_history[mid] = rinfo["rating"]
        else:
            from recommender.kg.queries import QUERY_SEEN_MOVIES
            with graph.driver.session(database=graph.database) as session:
                records = session.run(QUERY_SEEN_MOVIES, userId=user_id)
                for rec in records:
                    seen_movies.add(rec["movieId"])
                    user_history[rec["movieId"]] = float(rec["rating"])

        if not user_history:
            return []

        total_exclude = set(seen_movies)
        if exclude_movie_ids:
            total_exclude.update(exclude_movie_ids)

        liked_movies = {
            mid: r for mid, r in user_history.items()
            if r >= self.min_liked_rating and self.preference_weight(r) > 0
        }

        if not liked_movies:
            return []

        cand_p1: Dict[int, float] = defaultdict(float)
        cand_p2: Dict[int, float] = defaultdict(float)
        cand_p3: Dict[int, float] = defaultdict(float)
        all_candidate_ids: Set[int] = set()

        # ======================================================================
        # P1: GENRE METAPATH
        # ======================================================================
        if enable_p1 and hasattr(graph, "movie_in_genre"):
            for source_mid, rating in liked_movies.items():
                w = self.preference_weight(rating)
                source_genres = graph.movie_in_genre.get(source_mid, set())
                for g in source_genres:
                    genre_movies = graph.genre_to_movies.get(g, set())
                    deg_g = len(genre_movies)
                    if deg_g == 0:
                        continue
                    norm_factor = 1.0 / math.sqrt(deg_g)
                    contrib = w * norm_factor
                    for cand_mid in genre_movies:
                        if cand_mid not in total_exclude:
                            cand_p1[cand_mid] += contrib
                            all_candidate_ids.add(cand_mid)

        # ======================================================================
        # P2: GENOME METAPATH
        # ======================================================================
        if enable_p2 and hasattr(graph, "movie_has_genome_tag"):
            for source_mid, rating in liked_movies.items():
                w = self.preference_weight(rating)
                source_tags = graph.movie_has_genome_tag.get(source_mid, {})
                for tag_id, rel_source in source_tags.items():
                    tag_movies = graph.genome_tag_to_movies.get(tag_id, {})
                    deg_t = len(tag_movies)
                    if deg_t == 0:
                        continue
                    norm_factor = 1.0 / math.log1p(deg_t)
                    base_contrib = w * rel_source * norm_factor
                    for cand_mid, rel_cand in tag_movies.items():
                        if cand_mid not in total_exclude:
                            cand_p2[cand_mid] += base_contrib * rel_cand
                            all_candidate_ids.add(cand_mid)

        # ======================================================================
        # P3: COLLABORATIVE GRAPH METAPATH
        # ======================================================================
        neighbor_sims: List[Tuple[int, float, List[int]]] = []
        if enable_p3 and hasattr(graph, "movie_rated_by_users"):
            neighbor_overlap: Dict[int, List[int]] = defaultdict(list)
            for anchor_mid in liked_movies.keys():
                users_rated_anchor = graph.movie_rated_by_users.get(anchor_mid, {})
                for n_uid, n_info in users_rated_anchor.items():
                    if n_uid != user_id and n_info["rating"] >= self.min_liked_rating:
                        neighbor_overlap[n_uid].append(anchor_mid)

            user_liked_count = len(liked_movies)
            for n_uid, shared_mids in neighbor_overlap.items():
                n_ratings = graph.user_rated_movie.get(n_uid, {})
                n_liked_count = sum(1 for r in n_ratings.values() if r["rating"] >= self.min_liked_rating)
                if n_liked_count == 0:
                    continue
                sim = len(shared_mids) / math.sqrt(user_liked_count * n_liked_count)
                neighbor_sims.append((n_uid, sim, shared_mids))

            neighbor_sims.sort(key=lambda x: (-x[1], x[0]))
            top_neighbors = neighbor_sims[:self.max_neighbors]

            for n_uid, sim, shared_mids in top_neighbors:
                n_ratings = graph.user_rated_movie.get(n_uid, {})
                for cand_mid, cand_rinfo in n_ratings.items():
                    if cand_mid not in total_exclude and cand_rinfo["rating"] >= self.min_liked_rating:
                        w_cand = self.preference_weight(cand_rinfo["rating"])
                        cand_p3[cand_mid] += sim * w_cand
                        all_candidate_ids.add(cand_mid)

        if not all_candidate_ids:
            return []

        # ======================================================================
        # CHUẨN HÓA VÀ KẾT HỢP ĐIỂM SỐ (SCORE FUSION)
        # ======================================================================
        cand_id_list = list(all_candidate_ids)
        p1_list = [cand_p1[mid] for mid in cand_id_list]
        p2_list = [cand_p2[mid] for mid in cand_id_list]
        p3_list = [cand_p3[mid] for mid in cand_id_list]

        norm_p1 = self._normalize_scores(p1_list)
        norm_p2 = self._normalize_scores(p2_list)
        norm_p3 = self._normalize_scores(p3_list)

        candidate_scores: List[Tuple[int, float]] = []
        for i, mid in enumerate(cand_id_list):
            s1 = norm_p1[i] if enable_p1 else 0.0
            s2 = norm_p2[i] if enable_p2 else 0.0
            s3 = norm_p3[i] if enable_p3 else 0.0
            raw_score = self.alpha * s1 + self.beta * s2 + self.gamma * s3
            candidate_scores.append((mid, raw_score))

        # Tie-break xác định: raw_score DESC, movieId ASC
        candidate_scores.sort(key=lambda x: (-x[1], x[0]))

        # Chỉ trích xuất evidence cho Top-N (tiết kiệm 99.9% CPU)
        target_candidates = candidate_scores[:top_n]
        top_cand_ids = {mid for mid, _ in target_candidates}

        # Trích xuất evidence cho các candidate được chọn
        cand_evidence = self._extract_evidence_for_candidates(
            top_cand_ids, liked_movies, graph, user_id, neighbor_sims[:self.max_neighbors] if enable_p3 else [],
            enable_p1, enable_p2, enable_p3
        )

        final_recs = []
        for rank_idx, (mid, score) in enumerate(target_candidates, start=1):
            title = graph.movies.get(mid, {}).get("title", f"Movie #{mid}")
            ev_list = cand_evidence.get(mid, [])
            ev_list.sort(key=lambda x: x.contribution, reverse=True)
            ev_dicts = [ev.to_dict() for ev in ev_list[:self.max_evidence_per_candidate]]

            final_recs.append({
                "userId": user_id,
                "movieId": mid,
                "title": title,
                "raw_score": round(score, 4),
                "rank": rank_idx,
                "model_name": "KG_PATH",
                "evidence": ev_dicts
            })

        return final_recs

    def _normalize_scores(self, scores: List[float]) -> List[float]:
        if not scores:
            return []
        clean_scores = [0.0 if not math.isfinite(s) else s for s in scores]
        min_v = min(clean_scores)
        max_v = max(clean_scores)
        if max_v - min_v < 1e-9:
            return [1.0 if max_v > 0 else 0.0 for _ in clean_scores]
        return [(s - min_v) / (max_v - min_v) for s in clean_scores]

    def _extract_evidence_for_candidates(
        self,
        candidate_ids: Set[int],
        liked_movies: Dict[int, float],
        graph: Any,
        user_id: int,
        top_neighbors: List[Tuple[int, float, List[int]]],
        enable_p1: bool,
        enable_p2: bool,
        enable_p3: bool
    ) -> Dict[int, List[EvidenceItem]]:
        evidence_map: Dict[int, List[EvidenceItem]] = defaultdict(list)

        # Evidence P1
        if enable_p1 and hasattr(graph, "movie_in_genre"):
            for source_mid, rating in liked_movies.items():
                w = self.preference_weight(rating)
                source_title = graph.movies.get(source_mid, {}).get("title", f"Movie #{source_mid}")
                source_genres = graph.movie_in_genre.get(source_mid, set())
                for g in source_genres:
                    genre_movies = graph.genre_to_movies.get(g, set())
                    deg_g = len(genre_movies)
                    if deg_g == 0:
                        continue
                    norm_factor = 1.0 / math.sqrt(deg_g)
                    contrib = w * norm_factor
                    # Giao với candidate_ids
                    common = genre_movies.intersection(candidate_ids)
                    for cand_mid in common:
                        evidence_map[cand_mid].append(EvidenceItem(
                            path_type="GENRE",
                            source_movie_id=source_mid,
                            source_movie_title=source_title,
                            shared_entity_type="Genre",
                            shared_entity_key=g,
                            source_rating=rating,
                            contribution=contrib
                        ))

        # Evidence P2
        if enable_p2 and hasattr(graph, "movie_has_genome_tag"):
            for source_mid, rating in liked_movies.items():
                w = self.preference_weight(rating)
                source_title = graph.movies.get(source_mid, {}).get("title", f"Movie #{source_mid}")
                source_tags = graph.movie_has_genome_tag.get(source_mid, {})
                for tag_id, rel_source in source_tags.items():
                    tag_movies = graph.genome_tag_to_movies.get(tag_id, {})
                    deg_t = len(tag_movies)
                    if deg_t == 0:
                        continue
                    norm_factor = 1.0 / math.log1p(deg_t)
                    base_contrib = w * rel_source * norm_factor
                    tag_name = graph.genome_tags.get(tag_id, {}).get("name", f"Tag #{tag_id}")
                    common = set(tag_movies.keys()).intersection(candidate_ids)
                    for cand_mid in common:
                        contrib = base_contrib * tag_movies[cand_mid]
                        evidence_map[cand_mid].append(EvidenceItem(
                            path_type="GENOME",
                            source_movie_id=source_mid,
                            source_movie_title=source_title,
                            shared_entity_type="GenomeTag",
                            shared_entity_key=tag_id,
                            shared_entity_name=tag_name,
                            source_rating=rating,
                            contribution=contrib
                        ))

        # Evidence P3
        if enable_p3 and hasattr(graph, "user_rated_movie"):
            for n_uid, sim, shared_mids in top_neighbors:
                n_ratings = graph.user_rated_movie.get(n_uid, {})
                common = set(n_ratings.keys()).intersection(candidate_ids)
                for cand_mid in common:
                    rinfo = n_ratings[cand_mid]
                    if rinfo["rating"] >= self.min_liked_rating:
                        w_cand = self.preference_weight(rinfo["rating"])
                        contrib = sim * w_cand
                        anchor_id = shared_mids[0]
                        anchor_title = graph.movies.get(anchor_id, {}).get("title", f"Movie #{anchor_id}")
                        evidence_map[cand_mid].append(EvidenceItem(
                            path_type="COLLABORATIVE",
                            source_movie_id=anchor_id,
                            source_movie_title=anchor_title,
                            neighbor_user_id=n_uid,
                            neighbor_rating=rinfo["rating"],
                            source_rating=liked_movies.get(anchor_id, 0.0),
                            contribution=contrib
                        ))

        return evidence_map
