"""
MoodGraph Phase 5: Catalog Application Service.
Provides business logic for movie discovery, details enrichment with external links,
genre filtering, and similar movies discovery.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from recommender.storage.catalog_repo import MovieCatalogRepository, get_catalog_repository

logger = logging.getLogger("recommender.services.catalog_service")


class CatalogService:
    """Service handling movie catalog discovery and details queries."""

    def __init__(self, catalog_repo: Optional[MovieCatalogRepository] = None):
        self.catalog_repo = catalog_repo or get_catalog_repository()

    def get_movie_detail(self, movie_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieves detailed movie metadata with external links, clean title,
        and simulated/real genome tags.
        """
        movie = self.catalog_repo.get_movie_by_id(movie_id)
        if not movie:
            return None

        imdb_id = movie.get("imdb_id")
        tmdb_id = movie.get("tmdb_id")

        imdb_url = f"https://www.imdb.com/title/tt{imdb_id}" if imdb_id else None
        tmdb_url = f"https://www.themoviedb.org/movie/{tmdb_id}" if tmdb_id else None

        # Build similar movies based on shared genres in catalog
        similar = self.get_similar_movies(movie_id, top_n=5)

        return {
            "movieId": movie["movieId"],
            "title": movie["title"],
            "clean_title": movie["clean_title"],
            "release_year": movie["release_year"],
            "genres": movie["genres"],
            "links": {
                "imdb_id": imdb_id,
                "tmdb_id": tmdb_id,
                "imdb_url": imdb_url,
                "tmdb_url": tmdb_url,
            },
            "stats": {
                "catalog_indexed": True,
            },
            "similar_movies": similar,
        }

    def search_movies(
        self,
        query: Optional[str] = None,
        genre: Optional[str] = None,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "title",
    ) -> Dict[str, Any]:
        """Performs paginated search with filtering."""
        items, total_count = self.catalog_repo.search_movies(
            query=query,
            genre=genre,
            year_min=year_min,
            year_max=year_max,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
        )

        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1

        formatted_items = []
        for it in items:
            imdb_id = it.get("imdb_id")
            tmdb_id = it.get("tmdb_id")
            formatted_items.append({
                "movieId": it["movieId"],
                "title": it["title"],
                "clean_title": it["clean_title"],
                "release_year": it["release_year"],
                "genres": it["genres"],
                "links": {
                    "imdb_id": imdb_id,
                    "tmdb_id": tmdb_id,
                    "imdb_url": f"https://www.imdb.com/title/tt{imdb_id}" if imdb_id else None,
                    "tmdb_url": f"https://www.themoviedb.org/movie/{tmdb_id}" if tmdb_id else None,
                },
            })

        return {
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "items": formatted_items,
        }

    def list_genres(self) -> List[str]:
        """Lists distinct genres."""
        return self.catalog_repo.list_genres()

    def get_similar_movies(self, movie_id: int, top_n: int = 5) -> List[Dict[str, Any]]:
        """Finds movies sharing the most genres with the target movie."""
        target = self.catalog_repo.get_movie_by_id(movie_id)
        if not target or not target["genres"]:
            return []

        primary_genre = target["genres"][0]
        same_genre_mids = self.catalog_repo._genre_index.get(primary_genre, [])

        similar = []
        for mid in same_genre_mids:
            if mid == movie_id:
                continue
            m = self.catalog_repo.get_movie_by_id(mid)
            if m:
                # Calculate simple Jaccard on genres
                s1 = set(target["genres"])
                s2 = set(m["genres"])
                overlap = len(s1 & s2) / float(len(s1 | s2))
                similar.append({
                    "movieId": m["movieId"],
                    "title": m["title"],
                    "genres": m["genres"],
                    "similarity": round(overlap, 3),
                })
            if len(similar) >= top_n * 3:
                break

        similar.sort(key=lambda x: x["similarity"], reverse=True)
        return similar[:top_n]


_global_catalog_service: Optional[CatalogService] = None


def get_catalog_service(catalog_repo: Optional[MovieCatalogRepository] = None) -> CatalogService:
    """Singleton getter for CatalogService."""
    global _global_catalog_service
    if _global_catalog_service is None or catalog_repo is not None:
        _global_catalog_service = CatalogService(catalog_repo)
    return _global_catalog_service

