"""
MoodGraph Giai đoạn 5: Tầng Giao tiếp API RESTful (API Layer).
Cung cấp ứng dụng FastAPI, mô hình dữ liệu (schemas) và các bộ định tuyến (routers).
"""

from recommender.api.app import app, create_app

__all__ = ["app", "create_app"]

