"""
MoodGraph Phase 5: Movie Discovery Router (Mode A).
Provides endpoints for browsing movies, inspecting profiles and history,
real-time personalized recommendations, and explainability breakdowns.
"""

from __future__ import annotations

import logging
import os
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Path as FPath, Query, status

from recommender.api.dependencies import (
    get_catalog_service,
    get_explainability_service,
    get_hybrid_engine,
    get_user_profile_service,
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


# ---------------------------------------------------------------------------
# Movie Catalog Endpoints
# ---------------------------------------------------------------------------

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
    """Lists and searches movies with filtering and pagination."""
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
    """Convenience search endpoint supporting both ?q= and ?query=."""
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
    """Retrieves rich movie metadata, external IMDb/TMDb links, and similar movies."""
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
    """Returns the list of all 19 canonical genres in the movie catalog."""
    return GenreListResponse(genres=catalog_svc.list_genres())


# ---------------------------------------------------------------------------
# User Exploration & History Endpoints
# ---------------------------------------------------------------------------

@router.get("/users", response_model=UserListResponse)
def list_sample_users(
    user_type: str = Query("all", pattern="^(all|pilot_kg|active|cold_start)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    user_svc: UserProfileService = Depends(get_user_profile_service),
) -> UserListResponse:
    """Lists representative users for demo exploration and inspection."""
    res = user_svc.list_sample_users(user_type=user_type, page=page, page_size=page_size)
    return UserListResponse(**res)


@router.get("/users/{user_id}/profile", response_model=UserProfileResponse)
def get_user_profile(
    user_id: int = FPath(..., ge=1, le=10_000_000, description="User ID (positive integer)"),
    user_svc: UserProfileService = Depends(get_user_profile_service),
) -> UserProfileResponse:
    """
    Retrieves user profile statistics and genre distribution.
    Computed strictly from the Train split (Zero Leakage).
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
    Retrieves user ratings history strictly from the Train split.
    Validation and Test held-out data are completely protected.
    """
    res = user_svc.get_user_history(
        user_id=user_id,
        page=page,
        page_size=page_size,
        min_rating=min_rating,
    )
    return UserHistoryResponse(**res)


# ---------------------------------------------------------------------------
# Recommendations & Explainability Endpoints
# ---------------------------------------------------------------------------

@router.get("/recommendations/{user_id}")
def get_recommendations(
    user_id: int = FPath(..., ge=1, le=10_000_000, description="Target user ID"),
    top_n: int = Query(10, ge=1, le=50),
    strategy: Optional[str] = Query(None, pattern="^(rrf|weighted|als_only|kg_only)$"),
    filter_seen: bool = Query(True),
    allow_unfiltered: bool = Query(False, description="Allow disabling seen filtering for diagnostics"),
    use_cache: bool = Query(True),
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
    admin_token: Optional[str] = Query(None, description="Admin token if passed as query parameter"),
    hybrid_engine=Depends(get_hybrid_engine),
):
    """
    Generates personalized recommendations using Hybrid Recommender Engine.
    Fully backwards-compatible with Phase 4 response contracts.
    """
    if hybrid_engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Hybrid recommender engine is not initialized or still warming up.",
        )

    # Diagnostic security check if client requests disabling seen filtering
    if not filter_seen:
        admin_key = os.getenv("ADMIN_API_KEY") or os.getenv("HYBRID_ADMIN_TOKEN", "moodgraph-admin-secret")
        provided_token = x_admin_token or admin_token
        if not provided_token or provided_token != admin_key:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Disabling seen filtering (filter_seen=false) is a privileged diagnostic feature requiring a valid Admin Token via X-Admin-Token or admin_token parameter.",
            )
        if not allow_unfiltered:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Disabling seen filtering is restricted. Please pass allow_unfiltered=true along with the valid Admin Token for diagnostic evaluations.",
            )

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
    Provides multi-perspective explanation for a recommended movie:
    - Knowledge Graph metapaths (P1 Genre, P2 Genome, P3 Collaborative)
    - ALS collaborative filtering latent factor affinity
    """
    res = explain_svc.explain_recommendation(user_id=user_id, movie_id=movie_id)
    return ExplanationDetailResponse(**res)
