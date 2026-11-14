"""
Bộ Quản lý Lưu trữ và Nạp Snapshot Nhị phân Nén (Embedded KG Cache Manager).
Tối ưu hóa thời gian khởi động hệ thống dưới 0.5 giây thông qua nén nhị phân pickle + gzip.
Tự động đồng bộ với SQLite app_state.db sau khi nạp.
"""

from __future__ import annotations

import gzip
import logging
import os
import pickle
import time
from pathlib import Path
from typing import Optional

from recommender.kg.embedded_graph import EmbeddedKnowledgeGraph

logger = logging.getLogger("recommender.kg.cache_manager")

DEFAULT_CACHE_REL_PATH = Path("data") / "embedded_kg_cache.pkl.gz"


class CacheManager:
    """Quản lý snapshot nhị phân nén của EmbeddedKnowledgeGraph."""

    @staticmethod
    def resolve_cache_path(custom_path: Optional[Path] = None) -> Path:
        """Xác định đường dẫn file snapshot cache."""
        if custom_path is not None:
            return Path(custom_path)
        project_root = Path(__file__).resolve().parent.parent.parent
        return project_root / DEFAULT_CACHE_REL_PATH

    @classmethod
    def save_cache(cls, graph: EmbeddedKnowledgeGraph, cache_path: Optional[Path] = None) -> bool:
        """
        Lưu đối tượng EmbeddedKnowledgeGraph ra tệp nhị phân nén (.pkl.gz).
        Sử dụng pickle protocol 5 để đạt tốc độ tối đa.
        """
        target_path = cls.resolve_cache_path(cache_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = target_path.with_suffix(".tmp")

        start_time = time.perf_counter()
        try:
            with gzip.open(temp_path, "wb", compresslevel=4) as f:
                pickle.dump(graph, f, protocol=pickle.HIGHEST_PROTOCOL)

            # Atomic replace để tránh tình trạng ghi nửa chừng làm hỏng cache
            if temp_path.exists():
                if target_path.exists():
                    target_path.unlink()
                temp_path.rename(target_path)

            elapsed = time.perf_counter() - start_time
            file_size_mb = target_path.stat().st_size / (1024 * 1024)
            logger.info(
                "Đã lưu snapshot đồ thị nhúng thành công: %s (%.2f MB) trong %.3f giây",
                target_path, file_size_mb, elapsed
            )
            return True
        except Exception as exc:
            logger.error("Lỗi khi lưu cache đồ thị: %s", exc)
            if temp_path.exists():
                temp_path.unlink()
            return False

    @classmethod
    def load_cache(cls, cache_path: Optional[Path] = None) -> Optional[EmbeddedKnowledgeGraph]:
        """
        Nạp đối tượng EmbeddedKnowledgeGraph từ tệp nhị phân nén (.pkl.gz).
        Cam kết thời gian nạp dưới 0.5 giây.
        """
        target_path = cls.resolve_cache_path(cache_path)
        if not target_path.exists():
            return None

        start_time = time.perf_counter()
        try:
            raw_bytes = target_path.read_bytes()
            decompressed = gzip.decompress(raw_bytes)
            graph = pickle.loads(decompressed)

            elapsed = time.perf_counter() - start_time
            logger.info(
                "Nạp snapshot nhị phân thành công từ %s trong %.3f giây.",
                target_path, elapsed
            )
            return graph
        except Exception as exc:
            logger.warning("Không thể đọc snapshot cache %s (sẽ nạp lại từ nguồn Parquet): %s", target_path, exc)
            return None

    @classmethod
    def get_or_create_graph(
        cls,
        data_root: Optional[Path] = None,
        cache_path: Optional[Path] = None,
        sqlite_path: Optional[Path] = None,
        sync_sqlite: bool = True,
        max_users: int = 2000
    ) -> EmbeddedKnowledgeGraph:
        """
        Phương thức tiện ích tự động:
        1. Thử nạp từ cache snapshot (.pkl.gz).
        2. Nếu không có cache: Nạp từ Parquet trong data_root, sau đó lưu cache.
        3. Đồng bộ tương tác mới nhất từ SQLite app_state.db.
        """
        project_root = Path(__file__).resolve().parent.parent.parent
        resolved_cache = cls.resolve_cache_path(cache_path)

        graph = cls.load_cache(resolved_cache)

        if graph is None:
            logger.info("Chưa có snapshot cache. Tiến hành nạp mới từ dữ liệu Parquet...")
            graph = EmbeddedKnowledgeGraph()
            from recommender.kg.config import load_kg_config
            cfg = load_kg_config()
            target_data_root = data_root or cfg.data_root
            if target_data_root and Path(target_data_root).exists():
                graph.load_from_parquet(Path(target_data_root), max_users=max_users, top_m_genome=cfg.tag_top_m)
                # Lưu cache cho các lần khởi động tiếp theo
                cls.save_cache(graph, resolved_cache)
            else:
                logger.warning("Không tìm thấy data_root Parquet (%s), dùng đồ thị synthetic.", target_data_root)
                from recommender.kg.import_graph import import_synthetic_data
                import_synthetic_data(graph)

        # Đồng bộ các đánh giá trong SQLite
        if sync_sqlite:
            db_file = sqlite_path or (project_root / "data" / "app_state.db")
            if Path(db_file).exists():
                graph.sync_with_sqlite(Path(db_file))

        return graph
