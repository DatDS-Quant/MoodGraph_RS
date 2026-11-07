"""
MoodGraph Phase 5: User Interaction Application Service.
Coordinates client-side watchlist additions, user feedback ratings,
custom taste preferences, and cache invalidation.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from recommender.storage import (
    MovieCatalogRepository,
    SQLiteStateRepository,
    get_catalog_repository,
    get_sqlite_state_repository,
)

logger = logging.getLogger("recommender.services.user_interaction_service")


class UserInteractionService:
    """Application service managing mutable demo interactions and cache synchronization."""

    def __init__(
        self,
        sqlite_repo: Optional[SQLiteStateRepository] = None,
        catalog_repo: Optional[MovieCatalogRepository] = None,
        hybrid_engine: Optional[Any] = None,
    ):
        self.sqlite_repo = sqlite_repo or get_sqlite_state_repository()
        self.catalog_repo = catalog_repo or get_catalog_repository()
        self.hybrid_engine = hybrid_engine

    def save_movie_to_list(self, user_id: str, movie_id: int, list_type: str = "watchlist") -> Dict[str, Any]:
        """Saves a movie to user's watchlist or favorites."""
        movie = self.catalog_repo.get_movie_by_id(movie_id)
        if not movie:
            return {"success": False, "error": f"Movie {movie_id} not found in catalog."}

        success = self.sqlite_repo.save_movie(user_id=user_id, movie_id=movie_id, list_type=list_type)

        # Invalidate recommendation cache for this user if hybrid_engine is available
        self._invalidate_user_cache(user_id)

        return {
            "success": success,
            "user_id": user_id,
            "movie_id": movie_id,
            "list_type": list_type,
            "movie_title": movie["title"],
        }

    def remove_movie_from_list(self, user_id: str, movie_id: int, list_type: str = "watchlist") -> Dict[str, Any]:
        """Removes a movie from user's watchlist."""
        removed = self.sqlite_repo.remove_saved_movie(user_id=user_id, movie_id=movie_id, list_type=list_type)
        self._invalidate_user_cache(user_id)
        return {"success": removed, "user_id": user_id, "movie_id": movie_id, "list_type": list_type}

    def get_saved_movies(self, user_id: str, list_type: Optional[str] = "watchlist") -> List[Dict[str, Any]]:
        """Lists saved movies with rich movie details."""
        raw_saved = self.sqlite_repo.list_saved_movies(user_id=user_id, list_type=list_type)
        enriched = []
        for item in raw_saved:
            mid = item["movie_id"]
            m = self.catalog_repo.get_movie_by_id(mid)
            enriched.append({
                "movieId": mid,
                "title": m["title"] if m else f"Movie {mid}",
                "genres": m["genres"] if m else [],
                "list_type": item["list_type"],
                "saved_at": item["created_at"],
            })
        return enriched

    def submit_rating(
        self,
        user_id: str,
        movie_id: int,
        rating: float,
        feedback_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Submits a user rating for a movie and invalidates recommendations cache."""
        movie = self.catalog_repo.get_movie_by_id(movie_id)
        if not movie:
            return {"success": False, "error": f"Movie {movie_id} not found in catalog."}

        self.sqlite_repo.record_rating(
            user_id=user_id,
            movie_id=movie_id,
            rating=rating,
            feedback_text=feedback_text,
        )

        self._invalidate_user_cache(user_id)

        return {
            "success": True,
            "user_id": user_id,
            "movie_id": movie_id,
            "rating": rating,
            "movie_title": movie["title"],
        }

    def get_user_demo_ratings(self, user_id: str) -> List[Dict[str, Any]]:
        """Retrieves demo ratings provided by the user."""
        ratings = self.sqlite_repo.get_user_demo_ratings(user_id)
        enriched = []
        for r in ratings:
            mid = r["movie_id"]
            m = self.catalog_repo.get_movie_by_id(mid)
            enriched.append({
                "movieId": mid,
                "title": m["title"] if m else f"Movie {mid}",
                "rating": r["rating"],
                "feedback_text": r["feedback_text"],
                "created_at": r["created_at"],
            })
        return enriched

    def save_preferences(
        self,
        user_id: str,
        genres: List[str],
        moods: Optional[List[str]] = None,
        min_year: Optional[int] = None,
        max_year: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Saves user preferences."""
        success = self.sqlite_repo.save_preferences(
            user_id=user_id,
            genres=genres,
            moods=moods,
            min_year=min_year,
            max_year=max_year,
        )
        self._invalidate_user_cache(user_id)
        return {"success": success, "user_id": user_id, "genres": genres}

    def get_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Gets user preferences."""
        return self.sqlite_repo.get_preferences(user_id)

    def _invalidate_user_cache(self, user_id: str) -> None:
        """Invalidates user cache if hybrid engine is wired."""
        try:
            if self.hybrid_engine and hasattr(self.hybrid_engine, "cache") and self.hybrid_engine.cache:
                # If user_id is integer string, invalidate entries
                if user_id.isdigit():
                    uid_int = int(user_id)
                    cache = self.hybrid_engine.cache
                    with cache._lock:
                        keys_to_del = [k for k in cache._cache.keys() if k[0] == uid_int]
                        for k in keys_to_del:
                            del cache._cache[k]
        except Exception as e:
            logger.debug(f"Cache invalidation note: {e}")


_global_interaction_service: Optional[UserInteractionService] = None


def get_user_interaction_service(
    sqlite_repo: Optional[SQLiteStateRepository] = None,
    catalog_repo: Optional[MovieCatalogRepository] = None,
    hybrid_engine: Optional[Any] = None,
) -> UserInteractionService:
    """Singleton getter for UserInteractionService."""
    global _global_interaction_service
    if _global_interaction_service is None or hybrid_engine is not None:
        _global_interaction_service = UserInteractionService(sqlite_repo, catalog_repo, hybrid_engine)
    return _global_interaction_service
