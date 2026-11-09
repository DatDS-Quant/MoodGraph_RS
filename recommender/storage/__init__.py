"""
MoodGraph Phase 5: Storage and Repository Layer.
Cung cấp các lớp truy xuất dữ liệu độc lập cho:
- Danh mục phim (MovieCatalogRepository)
- Lịch sử tương tác người dùng (UserHistoryRepository)
- Báo cáo kết quả nghiên cứu (ResearchMetricsRepository)
- Trạng thái ứng dụng demo (SQLiteStateRepository)
"""

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

