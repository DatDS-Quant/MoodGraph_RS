"""
Kho lưu trữ danh mục phim (MovieCatalogRepository) cho MoodGraph Phase 5.
Tải dữ liệu phim từ Parquet (`data/processed/core/movies` và `data/processed/core/links`),
xây dựng chỉ mục in-memory để phục vụ truy vấn O(1) theo movieId, tìm kiếm theo tên,
lọc theo thể loại, năm phát hành và phân trang an toàn.
"""

from __future__ import annotations

import re
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

import pyarrow.dataset as ds


_DEFAULT_DATA_ROOT = Path(__file__).resolve().parent.parent.parent / "data" / "processed"


class MovieCatalogRepository:
    """
    Kho lưu trữ danh mục phim chỉ đọc (Read-only In-Memory Catalog Repository).
    Thread-safe và tối ưu hóa cao cho các thao tác tra cứu metadata.
    """

    def __init__(self, data_root: Optional[Path] = None) -> None:
        self.data_root = Path(data_root) if data_root else _DEFAULT_DATA_ROOT
        self.movies_path = self.data_root / "core" / "movies"
        self.links_path = self.data_root / "core" / "links"

        self._lock = threading.RLock()
        self._is_loaded: bool = False
        self._movies_by_id: Dict[int, Dict[str, Any]] = {}
        self._all_movie_ids: List[int] = []
        self._title_index: List[Tuple[str, int]] = []
        self._genre_index: Dict[str, List[int]] = {}
        self._distinct_genres: List[str] = []

    def load_and_index(self) -> None:
        """Tải và lập chỉ mục toàn bộ danh mục phim vào RAM."""
        with self._lock:
            if self._is_loaded:
                return

            if not self.movies_path.exists():
                raise FileNotFoundError(f"Không tìm thấy thư mục phim tại: {self.movies_path}")

            # 1. Tải liên kết IMDb/TMDb
            links_map: Dict[int, Dict[str, Any]] = {}
            if self.links_path.exists():
                links_ds = ds.dataset(str(self.links_path), format="parquet")
                for batch in links_ds.to_batches():
                    pydict = batch.to_pydict()
                    for i in range(batch.num_rows):
                        mid = int(pydict["movieId"][i])
                        imdb = str(pydict["imdbId"][i]) if pydict.get("imdbId") and pydict["imdbId"][i] else None
                        tmdb_raw = pydict["tmdbId"][i] if pydict.get("tmdbId") else None
                        tmdb = str(int(tmdb_raw)) if tmdb_raw is not None and str(tmdb_raw).isdigit() else None
                        links_map[mid] = {"imdb_id": imdb, "tmdb_id": tmdb}

            # 2. Tải danh mục phim
            movies_ds = ds.dataset(str(self.movies_path), format="parquet")
            movies_by_id: Dict[int, Dict[str, Any]] = {}
            title_index: List[Tuple[str, int]] = []
            genre_index: Dict[str, List[int]] = {}
            distinct_genres: Set[str] = set()

            year_pattern = re.compile(r"\((\d{4})\)")

            for batch in movies_ds.to_batches():
                pydict = batch.to_pydict()
                for i in range(batch.num_rows):
                    mid = int(pydict["movieId"][i])
                    title = str(pydict["title"][i])
                    genres_raw = str(pydict["genres"][i]) if pydict.get("genres") else ""
                    
                    # Tách danh sách thể loại
                    if pydict.get("genre_list") and isinstance(pydict["genre_list"][i], list):
                        genre_list = [str(g) for g in pydict["genre_list"][i] if g]
                    else:
                        genre_list = [g.strip() for g in genres_raw.split("|") if g.strip()]

                    for g in genre_list:
                        if g and g != "(no genres listed)":
                            distinct_genres.add(g)
                            if g not in genre_index:
                                genre_index[g] = []
                            genre_index[g].append(mid)

                    # Trích xuất năm phát hành từ tiêu đề (ví dụ: "Toy Story (1995)" -> 1995)
                    year_match = year_pattern.search(title)
                    release_year = int(year_match.group(1)) if year_match else None

                    # Tiêu đề làm sạch (loại bỏ năm ở đuôi nếu có)
                    clean_title = year_pattern.sub("", title).strip() if release_year else title

                    link_info = links_map.get(mid, {})
                    record = {
                        "movieId": mid,
                        "title": title,
                        "clean_title": clean_title,
                        "release_year": release_year,
                        "genres": genre_list,
                        "imdb_id": link_info.get("imdb_id"),
                        "tmdb_id": link_info.get("tmdb_id"),
                    }
                    movies_by_id[mid] = record
                    title_index.append((title.lower(), mid))

            # Sắp xếp các chỉ mục phục vụ truy vấn ổn định
            all_movie_ids = sorted(movies_by_id.keys())
            sorted_genres = sorted(distinct_genres)

            self._movies_by_id = movies_by_id
            self._all_movie_ids = all_movie_ids
            self._title_index = title_index
            self._genre_index = genre_index
            self._distinct_genres = sorted_genres
            self._is_loaded = True

    def ensure_loaded(self) -> None:
        """Đảm bảo chỉ mục đã được nạp."""
        if not self._is_loaded:
            self.load_and_index()

    def get_movie_count(self) -> int:
        """Tổng số lượng phim trong danh mục."""
        self.ensure_loaded()
        return len(self._movies_by_id)

    def get_movie_by_id(self, movie_id: int) -> Optional[Dict[str, Any]]:
        """Truy xuất metadata của một phim theo movieId trong O(1)."""
        self.ensure_loaded()
        return self._movies_by_id.get(int(movie_id))

    def get_movies_by_ids(self, movie_ids: Sequence[int]) -> List[Dict[str, Any]]:
        """Truy xuất danh sách phim theo thứ tự ID được yêu cầu."""
        self.ensure_loaded()
        results: List[Dict[str, Any]] = []
        for mid in movie_ids:
            item = self._movies_by_id.get(int(mid))
            if item:
                results.append(item)
        return results

    def list_genres(self) -> List[str]:
        """Danh sách tất cả các thể loại phim riêng biệt."""
        self.ensure_loaded()
        return list(self._distinct_genres)

    def search_movies(
        self,
        query: Optional[str] = None,
        genre: Optional[str] = None,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "title",
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Tìm kiếm và lọc phim có hỗ trợ phân trang an toàn.
        
        Args:
            query: Từ khóa tìm kiếm trong tên phim
            genre: Lọc theo thể loại phim
            year_min: Năm phát hành nhỏ nhất
            year_max: Năm phát hành lớn nhất
            page: Số thứ tự trang (>= 1)
            page_size: Kích thước trang (1 đến 100)
            sort_by: Tiêu chí sắp xếp: "title", "year", "movieId"
        
        Returns:
            Tuple gồm (Danh sách phim của trang hiện tại, Tổng số kết quả phù hợp)
        """
        self.ensure_loaded()
        if page < 1:
            page = 1
        page_size = max(1, min(page_size, 100))

        # 1. Xác định tập ứng viên ban đầu
        if genre and genre in self._genre_index:
            candidate_mids = set(self._genre_index[genre])
        else:
            candidate_mids = set(self._all_movie_ids)

        # 2. Lọc theo từ khóa tìm kiếm (query)
        if query and query.strip():
            q_lower = query.strip().lower()
            matched_mids: Set[int] = set()
            for title_lower, mid in self._title_index:
                if q_lower in title_lower and mid in candidate_mids:
                    matched_mids.add(mid)
            candidate_mids = matched_mids

        # 3. Lọc theo năm phát hành
        filtered_movies: List[Dict[str, Any]] = []
        for mid in candidate_mids:
            movie = self._movies_by_id[mid]
            yr = movie["release_year"]
            if year_min is not None and (yr is None or yr < year_min):
                continue
            if year_max is not None and (yr is None or yr > year_max):
                continue
            filtered_movies.append(movie)

        total_count = len(filtered_movies)

        # 4. Sắp xếp kết quả
        if sort_by == "year":
            filtered_movies.sort(key=lambda m: (m["release_year"] or 0, m["title"], m["movieId"]), reverse=True)
        elif sort_by == "movieId":
            filtered_movies.sort(key=lambda m: m["movieId"])
        else:  # "title" mặc định
            filtered_movies.sort(key=lambda m: (m["title"].lower(), m["movieId"]))

        # 5. Cắt trang (Pagination)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_items = filtered_movies[start_idx:end_idx]

        return page_items, total_count


# Singleton Repository instance
_CATALOG_REPO_INSTANCE: Optional[MovieCatalogRepository] = None


def get_catalog_repository(data_root: Optional[Path] = None) -> MovieCatalogRepository:
    """Lấy hoặc khởi tạo singleton MovieCatalogRepository."""
    global _CATALOG_REPO_INSTANCE
    if _CATALOG_REPO_INSTANCE is None:
        _CATALOG_REPO_INSTANCE = MovieCatalogRepository(data_root=data_root)
        _CATALOG_REPO_INSTANCE.load_and_index()
    return _CATALOG_REPO_INSTANCE

