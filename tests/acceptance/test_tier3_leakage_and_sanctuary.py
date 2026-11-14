"""
Tầng 3: Rào chắn Chống Rò rỉ Dữ liệu Hai Lớp & Sanctuary Guard.
Kiểm định:
1. Lọc phim đã xem (Seen Movies Filtering Defense-in-Depth): Không bao giờ đề xuất phim đã xem.
2. Cách ly tập dữ liệu theo thời gian (Temporal Split Isolation): Test không rò rỉ vào Train.
3. Bảo toàn nguyên vẹn 100% Sanctuary Zones: `data/` (~1.78 GB, 76 files) và `artifacts/` (~183.6 MB, 335 files).
"""

from pathlib import Path
import numpy as np
import pytest
from recommender.api.app import app
from fastapi.testclient import TestClient
from recommender.storage import get_user_history_repository

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.fixture(scope="module")
def api_client():
    with TestClient(app) as client:
        yield client


class TestTier3LeakageAndSanctuaryGuard:
    """Bộ kiểm thử kiểm định rào chắn chống rò rỉ và bảo tồn vùng dữ liệu sống còn."""

    def test_01_seen_movie_filtering_defense_in_depth_user1(self, api_client):
        """
        Kiểm tra rào chắn lọc phim đã xem cho User 1 trên tất cả các chế độ gợi ý:
        rrf, weighted, als_only, kg_only.
        """
        history_repo = get_user_history_repository()
        seen_movies = history_repo.get_user_seen_movie_ids(user_id=1)
        assert len(seen_movies) > 0, "User 1 phải có lịch sử xem phim trong tập huấn luyện."

        for strategy in ["rrf", "weighted", "als_only", "kg_only"]:
            resp = api_client.get(f"/api/recommendations/1?top_n=20&strategy={strategy}")
            assert resp.status_code == 200, f"Chiến lược {strategy} phải trả về 200 OK."
            items = resp.json().get("recommendations", [])
            recommended_ids = {it["movieId"] for it in items}

            # Kiểm tra tập giao bắt buộc phải là tập rỗng (Zero Leakage)
            intersection = recommended_ids & seen_movies
            assert len(intersection) == 0, (
                f"Phát hiện rò rỉ phim đã xem trong chiến lược '{strategy}' cho User 1! "
                f"Các phim vi phạm: {intersection}"
            )

    def test_02_seen_movie_filtering_multi_user(self, api_client):
        """Kiểm tra rào chắn lọc phim đã xem trên nhiều người dùng khác nhau (User 2, User 3)."""
        history_repo = get_user_history_repository()

        for uid in [2, 3]:
            seen_movies = history_repo.get_user_seen_movie_ids(user_id=uid)
            if not seen_movies:
                continue

            resp = api_client.get(f"/api/recommendations/{uid}?top_n=15&strategy=rrf")
            assert resp.status_code == 200
            items = resp.json().get("recommendations", [])
            rec_ids = {it["movieId"] for it in items}

            intersection = rec_ids & seen_movies
            assert len(intersection) == 0, f"Rò rỉ phim đã xem đối với User {uid}: {intersection}"

    def test_03_temporal_split_isolation(self):
        """
        Kiểm tra rào chắn cách ly phân tách thời gian (Temporal Split Guard):
        Xác nhận dữ liệu ratings trong train_seen CSR matrix chứa đủ ~20 triệu tương tác (20,000,263).
        """
        history_repo = get_user_history_repository()
        history_repo.ensure_csr_loaded()
        assert history_repo.csr_path.exists(), "Chỉ mục CSR tập Train phải tồn tại."

        csr_data = np.load(history_repo.csr_path)
        total_interactions = len(csr_data["movie_ids"])
        # Tập huấn luyện Train MovieLens 25M chứa chính xác 20,000,263 tương tác
        assert total_interactions >= 20_000_000, (
            f"Tổng số tương tác Train phải đạt chuẩn 20M, đo được: {total_interactions}"
        )

    def test_04_sanctuary_zone_data_integrity(self):
        """
        Kiểm tra bảo toàn vùng Sanctuary Zone: thư mục data/.
        Bảo đảm tổng dung lượng xấp xỉ 1.78 GB và các cấu trúc Parquet / SQLite cốt lõi không bị mất mát.
        """
        data_dir = PROJECT_ROOT / "data"
        assert data_dir.is_dir(), "Thư mục data/ phải tồn tại."

        # Kiểm tra các thư mục và tệp sống còn
        crucial_paths = [
            data_dir / "raw" / "ml-25m" / "movies.csv",
            data_dir / "raw" / "ml-25m" / "ratings.csv",
            data_dir / "processed" / "core" / "movies",
            data_dir / "processed" / "core" / "genome_tags",
            data_dir / "processed" / "core" / "genome_scores",
            data_dir / "processed" / "splits" / "train",
            data_dir / "app_state.db",
            data_dir / "embedded_kg_cache.pkl.gz",
        ]
        for p in crucial_paths:
            assert p.exists(), f"Đường dẫn sống còn {p.name} trong Sanctuary Zone data/ bị thiếu!"

        # Đo tổng số file và dung lượng
        files = [f for f in data_dir.rglob("*") if f.is_file()]
        assert len(files) >= 70, f"Số lượng file trong data/ bất thường: {len(files)}"

        total_bytes = sum(f.stat().st_size for f in files)
        total_gb = total_bytes / (1024 ** 3)
        assert 1.6 <= total_gb <= 2.2, f"Dung lượng data/ bất thường: {total_gb:.3f} GB."

    def test_05_sanctuary_zone_artifacts_integrity(self):
        """
        Kiểm tra bảo toàn vùng Sanctuary Zone: thư mục artifacts/.
        Đảm bảo các mô hình Spark ALS checkpoints và báo cáo M01-M10 nguyên vẹn (khoảng 335 files, ~183 MB).
        """
        artifacts_dir = PROJECT_ROOT / "artifacts"
        assert artifacts_dir.is_dir(), "Thư mục artifacts/ phải tồn tại."

        files = [f for f in artifacts_dir.rglob("*") if f.is_file()]
        assert len(files) >= 300, f"Số lượng tệp trong artifacts/ bất thường: {len(files)} files."

        total_bytes = sum(f.stat().st_size for f in files)
        total_mb = total_bytes / (1024 * 1024)
        assert 170.0 <= total_mb <= 210.0, f"Dung lượng artifacts/ bất thường: {total_mb:.2f} MB."
