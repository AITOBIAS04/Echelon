from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List

from ..schemas.user_schemas import (
    UserPosition, UserPositionsResponse,
    PrivateFork, PrivateForkCreateRequest, PrivateForksResponse,
    WatchlistItem, WatchlistAddRequest, WatchlistResponse, WatchlistItemType,
    PortfolioSummary
)
from ..dependencies import get_user_service, get_current_user

router = APIRouter(prefix="/api/v1/user", tags=["User Data"])

# =========================================
# POSITIONS (My Missions)
# =========================================

@router.get("/positions", response_model=UserPositionsResponse)
async def get_user_positions(
    include_at_risk: bool = Query(default=True),
    service = Depends(get_user_service),
    user = Depends(get_current_user)
):
    """
    Get user's active positions across all timelines.
    
    This populates the "My Missions" section of Field Kit.
    """
    positions = service.get_positions(user.id)
    
    # Calculate totals
    total_value = sum(p.shards_held * p.current_price for p in positions)
    total_pnl = sum(p.unrealised_pnl_usd for p in positions)
    total_yield = sum(p.founder_yield_earned_usd for p in positions)
    
    return UserPositionsResponse(
        positions=positions,
        total_value_usd=total_value,
        total_unrealised_pnl_usd=total_pnl,
        total_founder_yield_usd=total_yield
    )

@router.get("/positions/{timeline_id}", response_model=UserPosition)
async def get_position_in_timeline(
    timeline_id: str,
    service = Depends(get_user_service),
    user = Depends(get_current_user)
):
    """Get user's position in a specific timeline."""
    position = service.get_position(user.id, timeline_id)
    if not position:
        raise HTTPException(status_code=404, detail="No position in this timeline")
    return position

# =========================================
# PRIVATE FORKS (Simulations)
# =========================================

@router.get("/private-forks", response_model=PrivateForksResponse)
async def get_private_forks(
    service = Depends(get_user_service),
    user = Depends(get_current_user)
):
    """
    Get user's private forks (simulations).
    
    These are draft timelines that don't affect the global market.
    """
    forks = service.get_private_forks(user.id)
    max_allowed = service.get_max_private_forks(user.tier)
    
    return PrivateForksResponse(
        forks=forks,
        total_count=len(forks),
        max_allowed=max_allowed
    )

@router.post("/private-forks", response_model=PrivateFork)
async def create_private_fork(
    request: PrivateForkCreateRequest,
    service = Depends(get_user_service),
    user = Depends(get_current_user)
):
    """
    Create a new private fork (simulation).
    
    The fork starts from the specified base timeline's current state.
    """
    # Check limit
    current_count = service.count_private_forks(user.id)
    max_allowed = service.get_max_private_forks(user.tier)
    
    if current_count >= max_allowed:
        raise HTTPException(
            status_code=400, 
            detail=f"Maximum {max_allowed} private forks allowed. Delete one first."
        )
    
    fork = service.create_private_fork(
        user_id=user.id,
        name=request.name,
        narrative=request.narrative,
        base_timeline_id=request.base_timeline_id
    )
    
    return fork

@router.delete("/private-forks/{fork_id}")
async def delete_private_fork(
    fork_id: str,
    service = Depends(get_user_service),
    user = Depends(get_current_user)
):
    """Delete a private fork."""
    success = service.delete_private_fork(user.id, fork_id)
    if not success:
        raise HTTPException(status_code=404, detail="Fork not found")
    return {"message": "Fork deleted"}

@router.post("/private-forks/{fork_id}/publish")
async def publish_private_fork(
    fork_id: str,
    service = Depends(get_user_service),
    user = Depends(get_current_user)
):
    """
    Publish a private fork to the global market.
    
    Cost: $ECHELON (varies by fork complexity)
    The user becomes the Founder of the new public timeline.
    """
    fork = service.get_private_fork(user.id, fork_id)
    if not fork:
        raise HTTPException(status_code=404, detail="Fork not found")
    
    if not fork.can_publish:
        raise HTTPException(status_code=400, detail="Fork cannot be published")
    
    # Deduct cost
    # (Implementation depends on payment system)
    
    # Create public timeline
    public_timeline = service.publish_fork(user.id, fork_id)
    
    return {
        "message": "Fork published successfully",
        "timeline_id": public_timeline.id,
        "timeline_name": public_timeline.name,
        "founder_id": user.id
    }

# =========================================
# WATCHLIST
# =========================================

@router.get("/watchlist", response_model=WatchlistResponse)
async def get_watchlist(
    service = Depends(get_user_service),
    user = Depends(get_current_user)
):
    """
    Get user's watchlist.
    
    Contains agents and timelines the user is tracking.
    """
    items = service.get_watchlist(user.id)
    max_allowed = service.get_max_watchlist_items(user.tier)
    
    return WatchlistResponse(
        items=items,
        total_count=len(items),
        max_allowed=max_allowed
    )

@router.post("/watchlist", response_model=WatchlistItem)
async def add_to_watchlist(
    request: WatchlistAddRequest,
    service = Depends(get_user_service),
    user = Depends(get_current_user)
):
    """Add an agent or timeline to watchlist."""
    # Check limit
    current_count = service.count_watchlist(user.id)
    max_allowed = service.get_max_watchlist_items(user.tier)
    
    if current_count >= max_allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {max_allowed} watchlist items. Remove one first."
        )
    
    # Check not already watching
    if service.is_watching(user.id, request.item_type, request.item_id):
        raise HTTPException(status_code=400, detail="Already in watchlist")
    
    item = service.add_to_watchlist(
        user_id=user.id,
        item_type=request.item_type,
        item_id=request.item_id
    )
    
    return item

@router.delete("/watchlist/{item_id}")
async def remove_from_watchlist(
    item_id: str,
    service = Depends(get_user_service),
    user = Depends(get_current_user)
):
    """Remove item from watchlist."""
    success = service.remove_from_watchlist(user.id, item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not in watchlist")
    return {"message": "Removed from watchlist"}

# =========================================
# PORTFOLIO SUMMARY
# =========================================

@router.get("/portfolio/summary", response_model=PortfolioSummary)
async def get_portfolio_summary(
    service = Depends(get_user_service),
    user = Depends(get_current_user)
):
    """
    Get overview of user's entire portfolio.
    
    Quick snapshot for Field Kit header.
    """
    return service.get_portfolio_summary(user.id)

# =========================================
# ALERTS / NOTIFICATIONS
# =========================================

@router.get("/alerts")
async def get_alerts(
    unread_only: bool = Query(default=True),
    limit: int = Query(default=20, le=100),
    service = Depends(get_user_service),
    user = Depends(get_current_user)
):
    """
    Get user's alerts.
    
    Triggered by:
    - Paradox in watched timeline
    - Agent on watchlist makes trade
    - Position at risk (stability < 30%)
    - Founder yield earned
    """
    return service.get_alerts(
        user_id=user.id,
        unread_only=unread_only,
        limit=limit
    )

@router.post("/alerts/{alert_id}/read")
async def mark_alert_read(
    alert_id: str,
    service = Depends(get_user_service),
    user = Depends(get_current_user)
):
    """Mark an alert as read."""
    service.mark_alert_read(user.id, alert_id)
    return {"message": "Alert marked as read"}

@router.post("/alerts/read-all")
async def mark_all_alerts_read(
    service = Depends(get_user_service),
    user = Depends(get_current_user)
):
    """Mark all alerts as read."""
    count = service.mark_all_alerts_read(user.id)
    return {"message": f"Marked {count} alerts as read"}



