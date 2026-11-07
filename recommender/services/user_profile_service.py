"""
MoodGraph Phase 5: User Profile Application Service.
Provides user activity profiles, history inspections strictly from the Train split,
and curated test users lists for interactive demo exploration.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from recommender.storage.catalog_repo import MovieCatalogRepository, get_catalog_repository
from recommender.storage.user_history_repo import UserHistoryRepository, get_user_history_repository

logger = logging.getLogger("recommender.services.user_profile_service")


class UserProfileService:
    """Application service for user preferences, activity profile, and history exploration."""

    def __init__(
        self,
        history_repo: Optional[UserHistoryRepository] = None,
        catalog_repo: Optional[MovieCatalogRepository] = None,
    ):
        self.history_repo = history_repo or get_user_history_repository()
        self.catalog_repo = catalog_repo or get_catalog_repository()

    def get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """
        Retrieves user activity summary and genre distribution computed
        strictly from the Train partition.
        """
        summary = self.history_repo.get_user_profile_summary(
            user_id=user_id,
            catalog_lookup=self.catalog_repo,
        )

        total_ratings = summary.get("interaction_count", summary.get("total_train_ratings", 0))
        mean_rating = summary.get("rating_mean", summary.get("mean_rating", 0.0))
        top_genres = summary.get("favorite_genres", [])
        genre_dist = summary.get("genre_distribution", {})
        if not genre_dist and top_genres:
            genre_dist = {g: 1 for g in top_genres}

        # Classify activity level
        if total_ratings >= 200:
            activity = "highly_active"
        elif total_ratings >= 50:
            activity = "moderate"
        elif total_ratings > 0:
            activity = "casual"
        else:
            activity = "cold"

        return {
            "userId": user_id,
            "ratings_count": total_ratings,
            "mean_rating": round(mean_rating, 2),
            "genre_distribution": genre_dist,
            "top_favorite_genres": top_genres,
            "activity_level": activity,
            "is_in_als_train": total_ratings > 0,
        }

    def get_user_history(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        min_rating: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Retrieves paginated rating history strictly from the Train dataset.
        Zero data leakage: Validation/Test held-out interactions are never returned.
        """
        all_ratings = self.history_repo.get_user_train_ratings(user_id)

        # Optional filter by rating
        if min_rating is not None:
            filtered = [r for r in all_ratings if r["rating"] >= min_rating]
        else:
            filtered = all_ratings

        total = len(filtered)
        page = max(1, page)
        page_size = max(1, min(page_size, 100))

        start = (page - 1) * page_size
        end = start + page_size
        page_items = filtered[start:end]

        # Enrich with movie catalog details
        enriched_items = []
        for r in page_items:
            mid = r["movieId"]
            movie = self.catalog_repo.get_movie_by_id(mid)
            enriched_items.append({
                "movieId": mid,
                "title": movie["title"] if movie else f"Movie {mid}",
                "genres": movie["genres"] if movie else [],
                "rating": r["rating"],
                "timestamp": r["timestamp"],
            })

        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        return {
            "userId": user_id,
            "total_rated": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "items": enriched_items,
        }

    def list_sample_users(
        self,
        user_type: str = "all",
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        Lists curated representative users from the evaluation cohorts
        and active users for demo navigation.
        """
        # Curated representative users:
        # Users 1 to 20 are active in validation cohort
        # Users 100, 200, 500, 1000, 2000 are verified in ALS factors
        sample_pool = [
            1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
            11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
            25, 30, 42, 50, 75, 100, 150, 200, 300, 500,
            1000, 2000, 5000, 10000, 20000, 50000, 100000, 162541,
        ]

        if user_type == "pilot_kg":
            # Cohort users tested in Phase 4 pilot
            pool = [u for u in sample_pool if u <= 200]
        elif user_type == "active":
            pool = [1, 2, 3, 4, 10, 50, 100, 200, 500, 1000]
        elif user_type == "cold_start":
            pool = [999999, 1000001]
        else:
            pool = sample_pool

        total = len(pool)
        start = (page - 1) * page_size
        end = start + page_size
        selected_ids = pool[start:end]

        items = []
        for uid in selected_ids:
            seen_ids = self.history_repo.get_user_seen_movie_ids(uid)
            profile = self.get_user_profile(uid) if seen_ids else None
            items.append({
                "userId": uid,
                "train_ratings_count": len(seen_ids),
                "favorite_genres": profile["top_favorite_genres"] if profile else [],
                "is_in_kg_pilot": uid <= 200,
                "is_in_als_train": len(seen_ids) > 0,
            })

        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "items": items,
        }


_global_user_profile_service: Optional[UserProfileService] = None


def get_user_profile_service(
    history_repo: Optional[UserHistoryRepository] = None,
    catalog_repo: Optional[MovieCatalogRepository] = None,
) -> UserProfileService:
    """Singleton getter for UserProfileService."""
    global _global_user_profile_service
    if _global_user_profile_service is None:
        _global_user_profile_service = UserProfileService(history_repo, catalog_repo)
    return _global_user_profile_service
