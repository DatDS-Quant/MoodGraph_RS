"""
MoodGraph Giai đoạn 5: Các hàm Cung cấp Tiêm Phụ thuộc FastAPI (Dependency Injection Providers).
Trích xuất các thể hiện Singleton của Service và Repository đã được nạp sẵn từ trạng thái ứng dụng (app.state).
"""

from __future__ import annotations

import hmac
import os
from typing import Any, Optional
from fastapi import Header, HTTPException, Request, status

from recommender.services.catalog_service import CatalogService, get_catalog_service as _default_catalog_service
from recommender.services.user_profile_service import UserProfileService, get_user_profile_service as _default_user_profile_service
from recommender.services.explainability_service import ExplainabilityService, get_explainability_service as _default_explain_service
from recommender.services.lab_service import LabService, get_lab_service as _default_lab_service
from recommender.services.user_interaction_service import UserInteractionService, get_user_interaction_service as _default_interaction_service


# =============================================================================
# Các hàm phụ thuộc (Dependencies) trích xuất dịch vụ từ app.state
# =============================================================================

def get_catalog_service(request: Request) -> CatalogService:
    """Truy xuất CatalogService từ trạng thái ứng dụng (app.state) hoặc singleton mặc định."""
    return getattr(request.app.state, "catalog_service", None) or _default_catalog_service()


def get_user_profile_service(request: Request) -> UserProfileService:
    """Truy xuất UserProfileService từ trạng thái ứng dụng (app.state) hoặc singleton mặc định."""
    return getattr(request.app.state, "user_profile_service", None) or _default_user_profile_service()


def get_explainability_service(request: Request) -> ExplainabilityService:
    """Truy xuất ExplainabilityService từ trạng thái ứng dụng (app.state) hoặc singleton mặc định."""
    return getattr(request.app.state, "explainability_service", None) or _default_explain_service()


def get_lab_service(request: Request) -> LabService:
    """Truy xuất LabService từ trạng thái ứng dụng (app.state) hoặc singleton mặc định."""
    return getattr(request.app.state, "lab_service", None) or _default_lab_service()


def get_interaction_service(request: Request) -> UserInteractionService:
    """Truy xuất UserInteractionService từ trạng thái ứng dụng (app.state) hoặc singleton mặc định."""
    return getattr(request.app.state, "interaction_service", None) or _default_interaction_service()


def get_hybrid_engine(request: Request) -> Any:
    """Truy xuất thể hiện HybridRecommenderService từ trạng thái ứng dụng (app.state)."""
    return getattr(request.app.state, "hybrid_engine", None)


# =============================================================================
# Xác thực quyền quản trị viên (Admin Token Security Verification)
# =============================================================================

def verify_admin_header_token(
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
) -> str:
    """
    Thực thi xác thực bảo mật mã thông báo quản trị viên (Admin Token) nghiêm ngặt phía máy chủ:
    - Nếu máy chủ chưa cấu hình ADMIN_API_KEY: Từ chối truy cập quản trị ngay lập tức (chính sách fail-closed).
    - Thiếu tiêu đề X-Admin-Token trong request: Trả về mã lỗi 403 Forbidden.
    - Mã token không khớp: Trả về mã lỗi 403 Forbidden.
    - Không chấp nhận token truyền qua query string để tránh rò rỉ vào access log.
    - So sánh chuỗi với thời gian hằng số (hmac.compare_digest) để triệt tiêu tấn công định thời (timing attacks).
    - Bảo đảm 100% không rò rỉ khóa bí mật trong log hoặc thông báo lỗi.
    """
    admin_key = os.getenv("ADMIN_API_KEY")
    if not admin_key or not admin_key.strip():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative access denied: Server administrator token is unconfigured (fail-closed policy).",
        )

    if not x_admin_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative authorization required: Missing X-Admin-Token header.",
        )

    if not hmac.compare_digest(x_admin_token.strip(), admin_key.strip()):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative authorization failed: Invalid administrator token.",
        )

    return x_admin_token


