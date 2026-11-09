"""
MoodGraph Phase 5: FastAPI Dependency Injection Providers.
Extracts pre-warmed singleton services and repositories from application state.
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


def get_catalog_service(request: Request) -> CatalogService:
    """Retrieves CatalogService from app state or singleton."""
    return getattr(request.app.state, "catalog_service", None) or _default_catalog_service()


def get_user_profile_service(request: Request) -> UserProfileService:
    """Retrieves UserProfileService from app state or singleton."""
    return getattr(request.app.state, "user_profile_service", None) or _default_user_profile_service()


def get_explainability_service(request: Request) -> ExplainabilityService:
    """Retrieves ExplainabilityService from app state or singleton."""
    return getattr(request.app.state, "explainability_service", None) or _default_explain_service()


def get_lab_service(request: Request) -> LabService:
    """Retrieves LabService from app state or singleton."""
    return getattr(request.app.state, "lab_service", None) or _default_lab_service()


def get_interaction_service(request: Request) -> UserInteractionService:
    """Retrieves UserInteractionService from app state or singleton."""
    return getattr(request.app.state, "interaction_service", None) or _default_interaction_service()


def get_hybrid_engine(request: Request) -> Any:
    """Retrieves HybridRecommenderService from app state."""
    return getattr(request.app.state, "hybrid_engine", None)


def verify_admin_header_token(
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
) -> str:
    """
    Enforces strict server-side admin token authorization:
    - Missing server-side admin token configuration: Deny administrative access (fail-closed).
    - Missing request token header: 403 Forbidden.
    - Invalid request token header: 403 Forbidden.
    - Query-string token: Not accepted.
    - Constant-time comparison to prevent timing attacks.
    - Zero secret leakage in errors or logs.
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


