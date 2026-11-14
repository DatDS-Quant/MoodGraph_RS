"""
MoodGraph Giai đoạn 5: Bộ định tuyến Khám phá Phim (Movie Discovery Router - Chế độ Người dùng Mode A).
Cung cấp các điểm cuối phục vụ duyệt danh mục phim, kiểm tra hồ sơ và lịch sử đánh giá của người dùng,
gợi ý cá nhân hóa thời gian thực, và phân rã các góc nhìn giải thích khuyến nghị.
"""

from __future__ import annotations

import hmac
import logging
import os
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Path as FPath, Query, status

from recommender.api.dependencies import (
    get_catalog_service,
    get_explainability_service,
    get_hybrid_engine,
    get_user_profile_service,
    verify_admin_header_token,
)
from recommender.api.schemas import (
    ExplanationDetailResponse,
    GenreListResponse,
    MovieDetailResponse,
    MovieSearchResponse,
    UserHistoryResponse,
    UserListResponse,
    UserProfileResponse,
)
from recommender.services.catalog_service import CatalogService
from recommender.services.explainability_service import ExplainabilityService
from recommender.services.user_profile_service import UserProfileService

logger = logging.getLogger("recommender.api.discovery_router")

router = APIRouter(prefix="/api", tags=["Mode A - Movie Discovery"])


# ===========================================================================
# 1. Các điểm cuối Danh mục Phim (Movie Catalog Endpoints)
# ===========================================================================

@router.get("/movies", response_model=MovieSearchResponse)
def list_and_search_movies(
    query: Optional[str] = Query(None, max_length=200, description="Search keyword in movie title"),
    genre: Optional[str] = Query(None, max_length=50, description="Filter by genre"),
    year_min: Optional[int] = Query(None, ge=1870, le=2050, description="Minimum release year"),
    year_max: Optional[int] = Query(None, ge=1870, le=2050, description="Maximum release year"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    sort_by: str = Query("title", pattern="^(title|year|movieId)$", description="Sort criterion"),
    catalog_svc: CatalogService = Depends(get_catalog_service),
) -> MovieSearchResponse:
    """Liệt kê và tìm kiếm danh mục phim có hỗ trợ bộ lọc (từ khóa, thể loại, khoảng năm phát hành) và phân trang."""
    res = catalog_svc.search_movies(
        query=query,
        genre=genre,
        year_min=year_min,
        year_max=year_max,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
    )
    return MovieSearchResponse(**res)


@router.get("/movies/search", response_model=MovieSearchResponse)
def search_movies_alias(
    q: Optional[str] = Query(None, max_length=200, description="Search keyword alias"),
    query: Optional[str] = Query(None, max_length=200, description="Search keyword in movie title"),
    genre: Optional[str] = Query(None, max_length=50, description="Filter by genre"),
    year_min: Optional[int] = Query(None, ge=1870, le=2050),
    year_max: Optional[int] = Query(None, ge=1870, le=2050),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("title", pattern="^(title|year|movieId)$"),
    catalog_svc: CatalogService = Depends(get_catalog_service),
) -> MovieSearchResponse:
    """Điểm cuối tìm kiếm tiện ích hỗ trợ đồng thời cả tham số truy vấn ?q= và ?query=."""
    target_query = q if q is not None else query
    res = catalog_svc.search_movies(
        query=target_query,
        genre=genre,
        year_min=year_min,
        year_max=year_max,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
    )
    return MovieSearchResponse(**res)


@router.get("/movies/{movie_id}", response_model=MovieDetailResponse)
def get_movie_detail(
    movie_id: int,
    catalog_svc: CatalogService = Depends(get_catalog_service),
) -> MovieDetailResponse:
    """Truy xuất siêu dữ liệu chi tiết của phim, liên kết ngoài IMDb/TMDb và danh sách các phim tương đồng."""
    detail = catalog_svc.get_movie_detail(movie_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with ID {movie_id} was not found in catalog.",
        )
    return MovieDetailResponse(**detail)


@router.get("/genres", response_model=GenreListResponse)
def list_genres(
    catalog_svc: CatalogService = Depends(get_catalog_service),
) -> GenreListResponse:
    """Trả về danh sách toàn bộ 19 thể loại phim chuẩn tắc có trong danh mục."""
    return GenreListResponse(genres=catalog_svc.list_genres())


# ===========================================================================
# 2. Các điểm cuối Hồ sơ & Lịch sử Người dùng (User Exploration & History)
# ===========================================================================

@router.get("/users", response_model=UserListResponse)
def list_sample_users(
    user_type: str = Query("all", pattern="^(all|pilot_kg|active|cold_start)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    user_svc: UserProfileService = Depends(get_user_profile_service),
) -> UserListResponse:
    """Liệt kê danh sách người dùng mẫu tiêu biểu phục vụ việc khám phá và kiểm thử trên giao diện demo."""
    res = user_svc.list_sample_users(user_type=user_type, page=page, page_size=page_size)
    return UserListResponse(**res)


@router.get("/users/{user_id}/profile", response_model=UserProfileResponse)
def get_user_profile(
    user_id: int = FPath(..., ge=1, le=10_000_000, description="User ID (positive integer)"),
    user_svc: UserProfileService = Depends(get_user_profile_service),
) -> UserProfileResponse:
    """
    Truy xuất thống kê hồ sơ người dùng và phân bố thể loại yêu thích.
    Được tính toán nghiêm ngặt chỉ từ phân vùng dữ liệu Train (bảo đảm 100% không rò rỉ dữ liệu).
    """
    res = user_svc.get_user_profile(user_id)
    return UserProfileResponse(**res)


@router.get("/users/{user_id}/history", response_model=UserHistoryResponse)
def get_user_history(
    user_id: int = FPath(..., ge=1, le=10_000_000, description="User ID (positive integer)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    min_rating: Optional[float] = Query(None, ge=0.5, le=5.0),
    user_svc: UserProfileService = Depends(get_user_profile_service),
) -> UserHistoryResponse:
    """
    Truy xuất lịch sử đánh giá của người dùng phân trang nghiêm ngặt từ tập Train.
    Tập dữ liệu kiểm định giữ lại (Validation và Test) được bảo vệ cách ly tuyệt đối.
    """
    res = user_svc.get_user_history(
        user_id=user_id,
        page=page,
        page_size=page_size,
        min_rating=min_rating,
    )
    return UserHistoryResponse(**res)


# ===========================================================================
# 3. Các điểm cuối Gợi ý Cá nhân hóa & Giải thích (Recommendations & Explainability)
# ===========================================================================

@router.get("/recommendations/{user_id}")
def get_recommendations(
    user_id: int = FPath(..., ge=1, le=10_000_000, description="Target user ID"),
    top_n: int = Query(10, ge=1, le=50),
    strategy: Optional[str] = Query(None, pattern="^(rrf|weighted|als_only|kg_only)$"),
    filter_seen: bool = Query(True),
    allow_unfiltered: bool = Query(False, description="Allow disabling seen filtering for diagnostics"),
    use_cache: bool = Query(True),
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
    hybrid_engine=Depends(get_hybrid_engine),
):
    """
    Tạo danh sách gợi ý phim cá nhân hóa bằng Động cơ Gợi ý Lai (Hybrid Recommender Engine).
    Tương thích ngược 100% với cấu trúc dữ liệu trả về từ Giai đoạn 4.
    Bắt buộc xác thực khóa quản trị viên (Admin Token) khi yêu cầu tắt bộ lọc phim đã xem.
    """
    if hybrid_engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Hybrid recommender engine is not initialized or still warming up.",
        )

    # Kiểm tra an ninh chẩn đoán nếu client yêu cầu tắt bộ lọc phim đã xem (chính sách fail-closed)
    if not filter_seen:
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
        if not allow_unfiltered:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Disabling seen filtering is restricted. Please pass allow_unfiltered=true along with the valid X-Admin-Token header for diagnostic evaluations.",
            )
        # Áp dụng cô lập hoàn toàn bộ nhớ đệm cho chế độ chẩn đoán: không đọc và không làm bẩn cache người dùng
        use_cache = False

    try:
        resp = hybrid_engine.recommend(
            user_id=user_id,
            top_n=top_n,
            fusion_strategy=strategy,
            filter_seen=filter_seen,
            use_cache=use_cache,
        )
        if hasattr(resp, "to_dict"):
            return resp.to_dict()
        elif hasattr(resp, "dict"):
            return resp.dict()
        return resp
    except Exception as e:
        logger.error(f"Error serving recommendations for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation pipeline error: {str(e)}",
        )


@router.get("/explanations/{user_id}/{movie_id}", response_model=ExplanationDetailResponse)
def get_recommendation_explanation(
    user_id: int = FPath(..., ge=1, le=10_000_000, description="Target user ID"),
    movie_id: int = FPath(..., ge=1, le=10_000_000, description="Target movie ID"),
    explain_svc: ExplainabilityService = Depends(get_explainability_service),
) -> ExplanationDetailResponse:
    """
    Cung cấp giải thích đa tầng cho một bộ phim được gợi ý:
    - Các siêu đường dẫn Đồ thị Tri thức (P1 Thể loại, P2 Genome Tag, P3 Cộng tác).
    - Tương quan nhân tố tiềm ẩn từ mô hình lọc cộng tác Spark ALS.
    """
    res = explain_svc.explain_recommendation(user_id=user_id, movie_id=movie_id)
    return ExplanationDetailResponse(**res)
