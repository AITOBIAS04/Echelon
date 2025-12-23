"""
Positions API Endpoints
=======================

REST API for user positions (wrapper around user routes).

Endpoints:
- GET /api/v1/positions - Get user positions
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse

from ..dependencies import get_current_user
from ..schemas.user_schemas import UserPositionsResponse

router = APIRouter(prefix="/api/v1/positions", tags=["Positions"])


@router.get("/", response_model=UserPositionsResponse)
async def get_positions(
    user = Depends(get_current_user)
):
    """
    Get user's active positions across all timelines.
    
    This is a convenience endpoint that redirects to /api/v1/user/positions.
    """
    # For now, return empty response - the frontend should use /api/v1/user/positions
    # This endpoint exists for API consistency
    raise HTTPException(
        status_code=501,
        detail="Use /api/v1/user/positions instead. This endpoint is a placeholder."
    )

