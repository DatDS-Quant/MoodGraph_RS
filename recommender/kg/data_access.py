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
        Sử dụng min-heap kích thước cố định top_m cho mỗi phim để đảm bảo bộ nhớ hữu hạn (<30MB)
        và tránh tuyệt đối hiện tượng cắt tỉa non (premature eviction) khi một phim trải dài qua nhiều chunks.
        """
        import heapq
        path = self._resolve_dataset_path("core/genome_scores")
        dataset = ds.dataset(str(path), format="parquet")
        
        filter_expr = ds.field("movieId").isin(list(movie_ids)) if movie_ids else None
        movie_heaps: Dict[int, List[Tuple[float, int]]] = {}

        scanner = dataset.scanner(columns=["movieId", "tagId", "relevance"], filter=filter_expr, batch_size=batch_size * 4)
        for record_batch in scanner.to_batches():
            pydict = record_batch.to_pydict()
            m_ids = pydict["movieId"]
            t_ids = pydict["tagId"]
            rels = pydict["relevance"]
            for i in range(record_batch.num_rows):
                m_id = int(m_ids[i])
                t_id = int(t_ids[i])
                rel = float(rels[i])
                if m_id not in movie_heaps:
                    movie_heaps[m_id] = []
                h = movie_heaps[m_id]
                item = (rel, -t_id)
                if len(h) < top_m:
                    heapq.heappush(h, item)
                elif item > h[0]:
                    heapq.heapreplace(h, item)

        buffer: List[Dict[str, Any]] = []
        for m_id in sorted(movie_heaps.keys()):
            tags = sorted(
                [{"movieId": m_id, "tagId": -t_neg, "relevance": rel} for rel, t_neg in movie_heaps[m_id]],
                key=lambda x: (-x["relevance"], x["tagId"])
            )
            buffer.extend(tags)
            if len(buffer) >= batch_size:
                yield buffer[:batch_size]
                buffer = buffer[batch_size:]

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

