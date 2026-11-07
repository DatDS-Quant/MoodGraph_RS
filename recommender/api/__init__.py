"""
MoodGraph Phase 5: API Layer.
Exports the FastAPI application, schemas, and routers.
"""

from recommender.api.app import app, create_app

__all__ = ["app", "create_app"]
