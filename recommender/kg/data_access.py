"""
Đọc dữ liệu Parquet phân mảnh theo lô (streaming batches) sử dụng pyarrow.
"""

from pathlib import Path
from typing import Generator, List, Dict, Any, Optional, Set
import pyarrow.parquet as pq
import pyarrow.dataset as ds


class DataAccess:
    def __init__(self, data_root: Path):
        self.data_root = Path(data_root)
        if not self.data_root.exists():
            raise FileNotFoundError(f"Thư mục dữ liệu không tồn tại: {self.data_root}")

    def _resolve_dataset_path(self, rel_path: str) -> Path:
        target = self.data_root / rel_path
        if not target.exists():
            raise FileNotFoundError(f"Không tìm thấy dataset tại: {target}")
        return target

    def stream_movies(self, batch_size: int = 5000) -> Generator[List[Dict[str, Any]], None, None]:
        """Đọc core/movies theo batch."""
        path = self._resolve_dataset_path("core/movies")
        dataset = ds.dataset(str(path), format="parquet")
        for batch in dataset.to_batches(columns=["movieId", "title", "genres"], batch_size=batch_size):
            pydict = batch.to_pydict()
            rows = []
            for i in range(batch.num_rows):
                rows.append({
                    "movieId": int(pydict["movieId"][i]),
                    "title": str(pydict["title"][i]),
                    "genresRaw": str(pydict["genres"][i]) if pydict["genres"][i] is not None else ""
                })
            yield rows

    def stream_movie_genres(self, batch_size: int = 5000) -> Generator[List[Dict[str, Any]], None, None]:
        """Đọc features/movie_genres theo batch."""
        path = self._resolve_dataset_path("features/movie_genres")
        dataset = ds.dataset(str(path), format="parquet")
        for batch in dataset.to_batches(columns=["movieId", "genre"], batch_size=batch_size):
            pydict = batch.to_pydict()
            rows = []
            for i in range(batch.num_rows):
                rows.append({
                    "movieId": int(pydict["movieId"][i]),
                    "genre": str(pydict["genre"][i])
                })
            yield rows

    def stream_genome_tags(self, batch_size: int = 5000) -> Generator[List[Dict[str, Any]], None, None]:
        """Đọc core/genome_tags theo batch."""
        path = self._resolve_dataset_path("core/genome_tags")
        dataset = ds.dataset(str(path), format="parquet")
        for batch in dataset.to_batches(columns=["tagId", "tag"], batch_size=batch_size):
            pydict = batch.to_pydict()
            rows = []
            for i in range(batch.num_rows):
                rows.append({
                    "tagId": int(pydict["tagId"][i]),
                    "tag": str(pydict["tag"][i])
                })
            yield rows

    def stream_top_m_genome_scores(
        self,
        top_m: int = 20,
        movie_ids: Optional[Set[int]] = None,
        batch_size: int = 5000
    ) -> Generator[List[Dict[str, Any]], None, None]:
        """
        Đọc core/genome_scores và lọc Top-M theo relevance DESC, tagId ASC cho từng phim.
        Nếu movie_ids được chỉ định, chỉ đọc các phim trong danh sách.
        """
        path = self._resolve_dataset_path("core/genome_scores")
        dataset = ds.dataset(str(path), format="parquet")
        
        # Nếu có tập movie_ids, tạo filter expression
        filter_expr = ds.field("movieId").isin(list(movie_ids)) if movie_ids else None
        
        # Nhóm theo movieId để lấy Top-M
        # Do genome_scores có 15.5M dòng, ta đọc từng chunk, gom theo movie và lọc
        movie_scores: Dict[int, List[Dict[str, Any]]] = {}
        buffer: List[Dict[str, Any]] = []

        scanner = dataset.scanner(columns=["movieId", "tagId", "relevance"], filter=filter_expr, batch_size=batch_size * 4)
        for record_batch in scanner.to_batches():
            pydict = record_batch.to_pydict()
            for i in range(record_batch.num_rows):
                m_id = int(pydict["movieId"][i])
                t_id = int(pydict["tagId"][i])
                rel = float(pydict["relevance"][i])
                if m_id not in movie_scores:
                    movie_scores[m_id] = []
                movie_scores[m_id].append({"movieId": m_id, "tagId": t_id, "relevance": rel})

            # Khi movie_scores có nhiều phim đã gom xong
            # Để an toàn cho bộ nhớ, nếu movie_scores vượt quá 2000 phim thì xuất bớt
            if len(movie_scores) >= 2000:
                # Xuất các phim
                for m_id, tags in list(movie_scores.items()):
                    # Sort theo relevance desc, tagId asc
                    tags.sort(key=lambda x: (-x["relevance"], x["tagId"]))
                    buffer.extend(tags[:top_m])
                    del movie_scores[m_id]

                    if len(buffer) >= batch_size:
                        yield buffer[:batch_size]
                        buffer = buffer[batch_size:]

        # Xử lý các phim còn lại
        for m_id, tags in movie_scores.items():
            tags.sort(key=lambda x: (-x["relevance"], x["tagId"]))
            buffer.extend(tags[:top_m])

        while len(buffer) > 0:
            yield buffer[:batch_size]
            buffer = buffer[batch_size:]

    def stream_train_ratings(
        self,
        user_ids: Optional[Set[int]] = None,
        batch_size: int = 5000
    ) -> Generator[List[Dict[str, Any]], None, None]:
        """
        Đọc splits/train (CHỈ TRAIN, TUYỆT ĐỐI KHÔNG ĐỌC VAL/TEST).
        Hỗ trợ lọc theo tập user_ids đại diện cho chế độ pilot.
        """
        path = self._resolve_dataset_path("splits/train")
        dataset = ds.dataset(str(path), format="parquet")
        filter_expr = ds.field("userId").isin(list(user_ids)) if user_ids else None

        scanner = dataset.scanner(
            columns=["userId", "movieId", "rating", "timestamp"],
            filter=filter_expr,
            batch_size=batch_size
        )
        for batch in scanner.to_batches():
            pydict = batch.to_pydict()
            rows = []
            for i in range(batch.num_rows):
                rows.append({
                    "userId": int(pydict["userId"][i]),
                    "movieId": int(pydict["movieId"][i]),
                    "rating": float(pydict["rating"][i]),
                    "timestamp": int(pydict["timestamp"][i])
                })
            yield rows

