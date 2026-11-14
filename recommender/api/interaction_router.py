"""
MoodGraph Giai đoạn 5: Bộ định tuyến Tương tác Người dùng (User Interaction Router).
Quản lý danh sách xem sau (watchlist), phản hồi đánh giá và cài đặt sở thích cá nhân của người dùng demo
trong cơ sở dữ liệu SQLite mà không làm biến đổi tập 25M đánh giá lịch sử chỉ đọc.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from recommender.api.dependencies import get_interaction_service
from recommender.api.schemas import (
    PreferencesRequest,
    PreferencesResponse,
    RatingSubmitRequest,
    RatingSubmitResponse,
    WatchlistRequest,
    WatchlistResponse,
)
from recommender.services.user_interaction_service import UserInteractionService

logger = logging.getLogger("recommender.api.interaction_router")

router = APIRouter(prefix="/api/interactions", tags=["User Interactions & Application State"])


# =============================================================================
# 1. Quản lý danh sách phim đã lưu (Watchlist / Favorites / Hidden)
# =============================================================================

@router.post("/watchlist", response_model=WatchlistResponse)
def save_movie_to_watchlist(
    req: WatchlistRequest,
    interaction_svc: UserInteractionService = Depends(get_interaction_service),
) -> WatchlistResponse:
    """Lưu phim vào danh sách xem sau (watchlist) hoặc yêu thích (favorites) của người dùng."""
    res = interaction_svc.save_movie_to_list(
        user_id=req.user_id,
        movie_id=req.movie_id,
        list_type=req.list_type,
    )
    if not res.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=res.get("error", "Failed to save movie to list."),
        )
    return WatchlistResponse(**res)


@router.delete("/watchlist", response_model=WatchlistResponse)
def remove_movie_from_watchlist(
    user_id: str = Query(..., description="User ID"),
    movie_id: int = Query(..., ge=1, description="Movie ID to remove"),
    list_type: str = Query("watchlist", pattern="^(watchlist|favorites|hidden)$"),
    interaction_svc: UserInteractionService = Depends(get_interaction_service),
) -> WatchlistResponse:
    """Xóa một bộ phim khỏi danh sách xem sau hoặc yêu thích của người dùng."""
    res = interaction_svc.remove_movie_from_list(
        user_id=user_id,
        movie_id=movie_id,
        list_type=list_type,
    )
    return WatchlistResponse(
        success=res["success"],
        user_id=user_id,
        movie_id=movie_id,
        list_type=list_type,
    )


@router.get("/watchlist/{user_id}", response_model=List[Dict[str, Any]])
def list_user_watchlist(
    user_id: str,
    list_type: Optional[str] = Query("watchlist", pattern="^(watchlist|favorites|hidden)$"),
    interaction_svc: UserInteractionService = Depends(get_interaction_service),
) -> List[Dict[str, Any]]:
    """Liệt kê danh sách các bộ phim đã lưu trong watchlist hoặc favorites của người dùng demo."""
    return interaction_svc.get_saved_movies(user_id=user_id, list_type=list_type)


# =============================================================================
# 2. Ghi nhận và truy xuất đánh giá phim (User Demo Ratings)
# =============================================================================

@router.post("/ratings", response_model=RatingSubmitResponse)
def submit_movie_rating(
    req: RatingSubmitRequest,
    interaction_svc: UserInteractionService = Depends(get_interaction_service),
) -> RatingSubmitResponse:
    """Ghi nhận đánh giá số sao (0.5 đến 5.0) của người dùng cho một phim và xóa bộ nhớ đệm gợi ý tương ứng."""
    res = interaction_svc.submit_rating(
        user_id=req.user_id,
        movie_id=req.movie_id,
        rating=req.rating,
        feedback_text=req.feedback_text,
    )
    if not res.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=res.get("error", "Failed to record movie rating."),
        )
    return RatingSubmitResponse(**res)


@router.get("/ratings/{user_id}", response_model=List[Dict[str, Any]])
def get_user_demo_ratings(
    user_id: str,
    interaction_svc: UserInteractionService = Depends(get_interaction_service),
) -> List[Dict[str, Any]]:
    """Truy xuất toàn bộ các đánh giá mà người dùng demo đã thực hiện trong phiên làm việc."""
    return interaction_svc.get_user_demo_ratings(user_id=user_id)


# =============================================================================
# 3. Quản lý sở thích cá nhân (User Preferences)
# =============================================================================

@router.post("/preferences", response_model=PreferencesResponse)
def save_user_preferences(
    req: PreferencesRequest,
    interaction_svc: UserInteractionService = Depends(get_interaction_service),
) -> PreferencesResponse:
    """Lưu cấu hình sở thích về thể loại, tâm trạng (moods) và khoảng năm phát hành của người dùng."""
    res = interaction_svc.save_preferences(
        user_id=req.user_id,
        genres=req.genres,
        moods=req.moods,
        min_year=req.min_year,
        max_year=req.max_year,
    )
    return PreferencesResponse(success=res["success"], user_id=req.user_id, genres=req.genres)


@router.get("/preferences/{user_id}", response_model=Optional[Dict[str, Any]])
def get_user_preferences(
    user_id: str,
    interaction_svc: UserInteractionService = Depends(get_interaction_service),
) -> Optional[Dict[str, Any]]:
    """Truy xuất cấu hình sở thích đã lưu của người dùng."""
    return interaction_svc.get_preferences(user_id=user_id)

