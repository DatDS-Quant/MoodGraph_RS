"""
MoodGraph Phase 5: User Interaction Router.
Manages demo user watchlist, feedback ratings, and personalized taste settings
in SQLite without altering read-only historical 25M ratings.
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


@router.post("/watchlist", response_model=WatchlistResponse)
def save_movie_to_watchlist(
    req: WatchlistRequest,
    interaction_svc: UserInteractionService = Depends(get_interaction_service),
) -> WatchlistResponse:
    """Saves a movie to user's watchlist or favorites."""
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
    """Removes a movie from user's watchlist or favorites."""
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
    """Lists saved movies in watchlist or favorites for a demo user."""
    return interaction_svc.get_saved_movies(user_id=user_id, list_type=list_type)


@router.post("/ratings", response_model=RatingSubmitResponse)
def submit_movie_rating(
    req: RatingSubmitRequest,
    interaction_svc: UserInteractionService = Depends(get_interaction_service),
) -> RatingSubmitResponse:
    """Submits a user rating for a movie (0.5 to 5.0 stars) and invalidates cached recommendations."""
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
    """Retrieves all demo ratings submitted by this user."""
    return interaction_svc.get_user_demo_ratings(user_id=user_id)


@router.post("/preferences", response_model=PreferencesResponse)
def save_user_preferences(
    req: PreferencesRequest,
    interaction_svc: UserInteractionService = Depends(get_interaction_service),
) -> PreferencesResponse:
    """Saves user genre, mood, and release year preferences."""
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
    """Retrieves saved user preferences."""
    return interaction_svc.get_preferences(user_id=user_id)

