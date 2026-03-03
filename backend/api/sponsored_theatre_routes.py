"""Sponsored Theatre API routes — sponsor onboarding workflow.

Three endpoints for the sponsor workflow:
  POST /  — create a Sponsored Theatre in CREATED state
  GET  /{theatre_id}/review — return SponsorReviewPackage for sponsor approval
  POST /{theatre_id}/commit — sponsor approves, freeze parameters, transition to COMMITTED

Routes delegate all business logic to SponsoredTheatreService.

Cycle-012, Sprint 1 — Theatre Creation + Sponsor Onboarding.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.market.exceptions import ParameterMutationAfterCommit
from backend.schemas.sponsored_theatre import (
    SponsoredTheatreConfig,
    SponsorReviewPackage,
)

# Service instance is injected via set_service() — avoids circular imports
# and allows test injection.
_service = None

router = APIRouter(
    prefix="/api/v1/sponsored-theatres",
    tags=["sponsored-theatres"],
)


def set_service(service: object) -> None:
    """Inject the SponsoredTheatreService instance."""
    global _service
    _service = service


def _get_service():
    """Get the injected service or raise 503."""
    if _service is None:
        raise HTTPException(
            status_code=503,
            detail="SponsoredTheatreService not configured",
        )
    return _service


@router.post("/", status_code=201)
def create_sponsored_theatre(config: SponsoredTheatreConfig) -> dict:
    """Create a Sponsored Theatre in CREATED state.

    Request body: SponsoredTheatreConfig (Pydantic v2 validated)
    Response: {theatre_id, status: "CREATED", commitment_hash}
    """
    service = _get_service()
    try:
        review_package = service.create(config)
        return {
            "theatre_id": review_package.theatre_id,
            "status": "CREATED",
            "commitment_hash": review_package.commitment_hash,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{theatre_id}/review")
def get_review_package(theatre_id: str) -> SponsorReviewPackage:
    """Return SponsorReviewPackage for sponsor approval.

    Shows: template, commitment hash, worst-case loss, source manifest, fees.
    """
    service = _get_service()
    try:
        return service.review(theatre_id)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Theatre '{theatre_id}' not found",
        )


@router.post("/{theatre_id}/commit")
def commit_theatre(theatre_id: str) -> dict:
    """Sponsor approves — freeze parameters and transition to COMMITTED.

    Response: {theatre_id, status: "COMMITTED", commitment_hash, tx_hash}
    """
    service = _get_service()
    try:
        return service.commit(theatre_id)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Theatre '{theatre_id}' not found",
        )
    except ParameterMutationAfterCommit as e:
        raise HTTPException(status_code=409, detail=str(e))
