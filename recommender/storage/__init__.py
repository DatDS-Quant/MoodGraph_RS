"""
MoodGraph Giai đoạn 5: Tầng Lưu trữ và Truy xuất Dữ liệu (Storage & Repository Layer).
Cung cấp các lớp truy xuất dữ liệu độc lập và an toàn cho:
- Danh mục phim (MovieCatalogRepository): Tra cứu thông tin phim in-memory siêu tốc.
- Lịch sử tương tác người dùng (UserHistoryRepository): Đọc dữ liệu đánh giá chỉ từ tập Train (chống rò rỉ 100%).
- Báo cáo kết quả nghiên cứu (ResearchMetricsRepository): Đọc kết quả thực nghiệm và metadata từ Giai đoạn 4.
- Trạng thái ứng dụng demo (SQLiteStateRepository): Quản lý người dùng demo, danh sách phim lưu, đánh giá và cấu hình.
"""

# Khởi tạo và xuất bản các Repository singleton cho tầng Storage
from recommender.storage.catalog_repo import MovieCatalogRepository, get_catalog_repository
from recommender.storage.user_history_repo import UserHistoryRepository, get_user_history_repository
from recommender.storage.research_metrics_repo import ResearchMetricsRepository, get_research_metrics_repository
from recommender.storage.sqlite_state_repo import SQLiteStateRepository, get_sqlite_state_repository

__all__ = [
    "MovieCatalogRepository",
    "get_catalog_repository",
    "UserHistoryRepository",
    "get_user_history_repository",
    "ResearchMetricsRepository",
    "get_research_metrics_repository",
    "SQLiteStateRepository",
    "get_sqlite_state_repository",
]

