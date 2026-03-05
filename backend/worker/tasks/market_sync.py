"""
Market Sync Task - Polymarket Data Integration

Polls Polymarket's public API and:
- Updates timeline prices from real orderbooks
- Creates wing flaps from real trades
- Detects anomalies for mission triggers

This bridges real prediction markets with Echelon's counterfactual layer.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Timeline, WingFlap, WingFlapType, FlapDirection
from backend.integrations.polymarket_client import PolymarketClient
from backend.worker.tasks._system_entity import ensure_system_entities
from backend.worker.tasks._ws_broadcast import broadcast_flap

logger = logging.getLogger('echelon.market_sync')


class MarketSyncTask:
    """Syncs real Polymarket data into Echelon.

    Call budget: 1 trending + up to MAX_ACTIVE_MARKETS trades = ≤11 calls/tick.
    At 10s cadence ≈ 66 req/min (within 100/60s Polymarket limit).
    """

    # Call-budget guardrail: cap active markets to keep within rate limit
    MAX_ACTIVE_MARKETS = 10

    def __init__(self):
        self.client = PolymarketClient()
        self.last_trade_ids: dict[str, str] = {}

        # Map Polymarket condition IDs to Echelon timeline IDs
        self.market_mapping: dict[str, str] = {}

        # Auto-discover mode: if no mapping, create timelines from Polymarket
        self.auto_discover = True
    
    async def tick(self, session: AsyncSession) -> str:
        """
        Sync market data from Polymarket.
        
        Returns a summary string for logging.
        """
        try:
            # Ensure SYSTEM user and agent exist (shared helper)
            await ensure_system_entities(session)

            # Get trending markets from Polymarket
            trending = await self.client.get_trending_markets(limit=20)

            # Filter out resolved markets (they have winner=True/False in tokens)
            active_markets = []
            for market in trending:
                tokens = market.get("tokens", [])
                is_resolved = any(t.get("winner") is not None for t in tokens)
                if not is_resolved and market.get("active", True):
                    active_markets.append(market)

            # Call-budget guardrail: cap active markets
            active_markets = active_markets[:self.MAX_ACTIVE_MARKETS]
            
            prices_updated = 0
            trades_synced = 0
            
            for market in active_markets:
                condition_id = market.get("condition_id", "")
                timeline_id = self.market_mapping.get(condition_id)
                
                # Auto-discover: sync even without mapping
                if not timeline_id and self.auto_discover:
                    timeline_id = await self._get_or_create_timeline(
                        session, market
                    )
                
                if timeline_id:
                    updated, new_trades = await self._sync_market(
                        session,
                        timeline_id,
                        market,
                    )
                    if updated:
                        prices_updated += 1
                    trades_synced += new_trades
            
            return f"Synced {prices_updated} prices, {trades_synced} trades"
            
        except Exception as e:
            logger.error(f"Polymarket sync error: {e}")
            return f"Sync failed: {str(e)[:50]}"
    
    async def _get_or_create_timeline(
        self,
        session: AsyncSession,
        market: dict,
    ) -> Optional[str]:
        """
        Get existing timeline or create from Polymarket market.
        
        Returns timeline ID.
        """
        condition_id = market.get("condition_id", "")
        timeline_id = f"TL_PM_{condition_id[:8].upper()}"
        
        # Check if exists
        result = await session.execute(
            select(Timeline).where(Timeline.id == timeline_id)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            return timeline_id
        
        # Create new timeline from market
        question = market.get("question", market.get("title", "Unknown Market"))
        
        # Get prices from tokens (Polymarket includes price in token data)
        tokens = market.get("tokens", [])
        
        yes_price = 0.5
        if tokens:
            # Skip if market is resolved (has winner field)
            if any(t.get("winner") is not None for t in tokens):
                logger.debug(f"Skipping resolved market: {question[:50]}")
                return None
            
            # Use first token as "Yes" price
            first_token = tokens[0]
            yes_price = float(first_token.get("price", 0.5))
            
            # Normalize if there are multiple tokens
            if len(tokens) >= 2:
                no_price = float(tokens[1].get("price", 1.0 - yes_price))
                total = yes_price + no_price
                if total > 0:
                    yes_price = yes_price / total
        
        timeline = Timeline(
            id=timeline_id,
            name=question[:100],
            narrative=question,
            keywords=self._extract_keywords(question),
            stability=0.75,        # 0-1 scale: start stable
            surface_tension=0.70,  # 0-1 scale
            price_yes=yes_price,
            price_no=1.0 - yes_price,
            osint_alignment=0.50,  # 0-1 scale
            logic_gap=0.0,
            gravity_score=0.50,    # 0-1 scale
            total_volume_usd=float(market.get("volume_24hr", 0) or 0),
            liquidity_depth_usd=float(market.get("liquidity", 0) or 0),
            active_agent_count=0,
            decay_rate_per_hour=0.01,  # 0-1 scale: 1% per hour
            is_anchor=True,            # Polymarket = anchor reality
            is_active=True,
        )
        session.add(timeline)
        await session.flush()
        
        logger.info(f"Created timeline from Polymarket: {timeline_id} - {question[:50]}")
        
        # Store mapping for future syncs
        self.market_mapping[condition_id] = timeline_id
        
        return timeline_id
    
    def _extract_keywords(self, question: str) -> list[str]:
        """Extract keywords from market question."""
        # Simple keyword extraction
        stop_words = {'will', 'the', 'be', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'by'}
        words = question.lower().split()
        keywords = [w.strip('?.,!') for w in words if w.lower() not in stop_words and len(w) > 2]
        return keywords[:10]
    
    async def _sync_market(
        self,
        session: AsyncSession,
        timeline_id: str,
        market: dict,
    ) -> tuple[bool, int]:
        """
        Sync a single market's data.
        
        Returns: (price_updated, num_new_trades)
        """
        # Get timeline from database
        result = await session.execute(
            select(Timeline).where(Timeline.id == timeline_id)
        )
        timeline = result.scalar_one_or_none()
        
        if not timeline:
            return (False, 0)
        
        price_updated = False
        new_trades = 0
        
        # Get current prices from tokens
        # Polymarket tokens have: token_id, outcome, price, winner
        # Outcomes are named (e.g., "Arizona State" vs "Nevada"), not "Yes"/"No"
        tokens = market.get("tokens", [])
        
        if tokens:
            # Skip if market is resolved (has winner field)
            if any(t.get("winner") is not None for t in tokens):
                logger.debug(f"Skipping price update for resolved market: {timeline_id}")
                return (False, 0)
            
            try:
                # Get prices from tokens - use first token as "Yes" price
                # In binary markets, first token is typically the affirmative outcome
                first_token = tokens[0]
                yes_price = float(first_token.get("price", 0.5))
                
                # If there's a second token, use it for "No" price
                # Otherwise calculate as 1 - yes_price
                if len(tokens) >= 2:
                    no_price = float(tokens[1].get("price", 1.0 - yes_price))
                else:
                    no_price = 1.0 - yes_price
                
                # Normalize to ensure they sum to 1.0
                total = yes_price + no_price
                if total > 0:
                    yes_price = yes_price / total
                    no_price = no_price / total
                
                logger.debug(f"  {timeline_id}: Token prices - {first_token.get('outcome', 'Token1')}: {yes_price:.4f}, No: {no_price:.4f}")
                
                # Update if price changed significantly
                if abs(timeline.price_yes - yes_price) > 0.01:
                    old_price = timeline.price_yes
                    
                    # Update timeline prices
                    await session.execute(
                        update(Timeline)
                        .where(Timeline.id == timeline_id)
                        .values(
                            price_yes=yes_price,
                            price_no=no_price
                        )
                    )
                    price_updated = True
                    
                    logger.info(
                        f"  {timeline_id}: Price updated {old_price:.4f} -> {yes_price:.4f}"
                    )
                else:
                    logger.debug(f"  {timeline_id}: Price unchanged ({yes_price:.4f})")
            except Exception as e:
                logger.warning(f"Price fetch error for {timeline_id}: {e}")
        
        # Sync recent trades (may require auth, so handle gracefully)
        condition_id = market.get("condition_id", "")
        try:
            trades = await self.client.get_trades(market=condition_id, limit=10)
            
            last_seen = self.last_trade_ids.get(condition_id)
            
            for trade in trades:
                trade_id = trade.get("id", "")
                
                if trade_id == last_seen:
                    break
                
                await self._create_trade_flap(session, timeline, trade)
                new_trades += 1
            
            if trades:
                self.last_trade_ids[condition_id] = trades[0].get("id", "")
                
        except Exception as e:
            error_str = str(e)
            # Handle authentication errors gracefully (trades may require auth)
            if "401" in error_str or "unauthorized" in error_str.lower():
                # Trades endpoint may require auth, this is expected
                logger.debug(f"Trade sync requires auth for {condition_id[:8]}... (skipping)")
            else:
                logger.debug(f"Trade sync error for {condition_id[:8]}...: {e}")
        
        # Update volume
        volume_24h = float(market.get("volume_24hr", 0) or 0)
        sync_timestamp = datetime.now(timezone.utc).replace(tzinfo=None)
        if volume_24h > timeline.total_volume_usd:
            await session.execute(
                update(Timeline)
                .where(Timeline.id == timeline_id)
                .values(total_volume_usd=volume_24h, last_sync_at=sync_timestamp)
            )
        else:
            # Record successful sync even when volume and price are unchanged.
            await session.execute(
                update(Timeline)
                .where(Timeline.id == timeline_id)
                .values(last_sync_at=sync_timestamp)
            )
        
        return (price_updated, new_trades)
    
    async def _create_trade_flap(
        self,
        session: AsyncSession,
        timeline: Timeline,
        trade: dict,
    ):
        """Create a MIRROR_TRADE wing flap from a Polymarket trade."""
        side = trade.get("side", "BUY")
        outcome = trade.get("outcome", "Yes")
        price = float(trade.get("price", 0.5))
        size = float(trade.get("size", 1))

        # Determine if this is YES or NO
        is_yes = (outcome == "Yes" and side == "BUY") or (outcome == "No" and side == "SELL")

        # Volume in USD
        volume_usd = size * price

        # Stability impact (0-1 scale: cap at 0.05 per trade)
        stability_delta = min(volume_usd / 10000, 0.05)
        if not is_yes:
            stability_delta = -stability_delta

        # Calculate new stability (0-1 clamped)
        new_stability = max(0.0, min(1.0, timeline.stability + stability_delta))

        action_text = f"Polymarket mirror: {side} {outcome} @ ${price:.2f}"

        flap_timestamp = datetime.now(timezone.utc).replace(tzinfo=None)

        flap_id = f"PM_{timeline.id}_{uuid.uuid4().hex[:8]}"
        flap = WingFlap(
            id=flap_id,
            timeline_id=timeline.id,
            agent_id="SYSTEM",
            flap_type=WingFlapType.MIRROR_TRADE,
            action=action_text,
            stability_delta=stability_delta,
            direction=(
                FlapDirection.STABILISE.value if stability_delta > 0
                else FlapDirection.DESTABILISE.value if stability_delta < 0
                else FlapDirection.NEUTRAL.value
            ),
            volume_usd=volume_usd,
            timeline_stability=new_stability,
            timeline_price=price,
            timestamp=flap_timestamp,
        )
        session.add(flap)
        await broadcast_flap(flap)

        # Update timeline stability + last_sync_at
        await session.execute(
            update(Timeline)
            .where(Timeline.id == timeline.id)
            .values(stability=new_stability, last_sync_at=flap_timestamp)
        )
