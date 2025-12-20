"""
Kalshi Sync Task - Real Market Data Integration

Polls Kalshi's public API and:
- Updates timeline prices from real orderbooks
- Creates wing flaps from real trades
- Detects anomalies for mission triggers

This bridges real prediction markets with Echelon's counterfactual layer.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Timeline, WingFlap, WingFlapType
from backend.integrations.kalshi_client import KalshiClient

logger = logging.getLogger('echelon.kalshi')


class KalshiSyncTask:
    """Syncs real Kalshi market data into Echelon."""
    
    def __init__(self):
        import os
        self.client = KalshiClient(use_demo=os.getenv("KALSHI_USE_DEMO", "false").lower() == "true")
        self.last_trade_ids: dict[str, str] = {}  # Track last seen trade per market
        
        # Map Kalshi tickers to Echelon timeline IDs
        # This would be configured in database in production
        self.ticker_mapping = {
            # Example mappings - configure based on your timelines
            'FED-RATE-25JAN': 'TL_FED_RATE',
            'OIL-100-DEC': 'TL_OIL_CRISIS',
        }
    
    async def tick(self, session: AsyncSession) -> str:
        """
        Sync market data from Kalshi.
        
        Returns a summary string for logging.
        """
        try:
            # Ensure client session is initialized
            if not hasattr(self.client, '_session') or not self.client._session:
                await self.client._ensure_session()
            
            # Get active Kalshi events
            # Note: get_events_public may not support status filter, so we filter client-side
            events, _ = await self.client.get_events_public(
                limit=20
            )
            
            # Filter for active events if needed
            events = [e for e in events if e.get('status', '').lower() in ('active', 'open')]
            
            prices_updated = 0
            trades_synced = 0
            
            for event in events:
                # Get markets for this event
                markets, _ = await self.client.get_event_markets_public(
                    event_ticker=event.get('ticker', ''),
                    limit=10
                )
                
                for market in markets:
                    ticker = market.get('ticker', '')
                    timeline_id = self.ticker_mapping.get(ticker)
                    
                    if timeline_id:
                        # Sync this market
                        updated, new_trades = await self._sync_market(
                            session, 
                            timeline_id, 
                            ticker,
                            market
                        )
                        if updated:
                            prices_updated += 1
                        trades_synced += new_trades
            
            return f"Synced {prices_updated} prices, {trades_synced} trades"
            
        except Exception as e:
            error_str = str(e)
            # Handle authentication errors gracefully
            if "401" in error_str or "unauthorized" in error_str.lower():
                logger.debug(f"Kalshi authentication required (401): {error_str[:100]}")
                return "Kalshi auth required (check API credentials)"
            else:
                logger.error(f"Kalshi sync error: {e}")
                return f"Sync failed: {error_str[:50]}"
    
    async def _sync_market(
        self,
        session: AsyncSession,
        timeline_id: str,
        ticker: str,
        market_data: dict
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
        
        # Update prices from market data
        yes_price = market_data.get('yes_price', market_data.get('last_price'))
        if yes_price:
            yes_price_decimal = yes_price / 100.0 if yes_price > 1 else yes_price
            
            if abs(timeline.price_yes - yes_price_decimal) > 0.01:
                old_price = timeline.price_yes
                
                # Update timeline prices
                # Note: updated_at is auto-updated by SQLAlchemy
                await session.execute(
                    update(Timeline)
                    .where(Timeline.id == timeline_id)
                    .values(
                        price_yes=yes_price_decimal,
                        price_no=1.0 - yes_price_decimal
                    )
                )
                price_updated = True
                
                logger.debug(
                    f"  {ticker}: Price updated {old_price:.2f} -> {yes_price_decimal:.2f}"
                )
        
        # Sync recent trades
        try:
            trades, _ = await self.client.get_trades_public(
                ticker=ticker,
                limit=10
            )
            
            last_seen = self.last_trade_ids.get(ticker)
            
            for trade in trades:
                trade_id = trade.get('trade_id', '')
                
                # Skip if we've already processed this trade
                if trade_id == last_seen:
                    break
                
                # Create wing flap from trade
                await self._create_trade_flap(session, timeline, trade)
                new_trades += 1
            
            # Update last seen trade
            if trades:
                self.last_trade_ids[ticker] = trades[0].get('trade_id', '')
                
        except Exception as e:
            logger.debug(f"Trade sync error for {ticker}: {e}")
        
        return (price_updated, new_trades)
    
    async def _create_trade_flap(
        self,
        session: AsyncSession,
        timeline: Timeline,
        trade: dict
    ):
        """Create a wing flap from a Kalshi trade."""
        import uuid
        
        side = trade.get('side', 'yes').upper()
        price = trade.get('price', 50)
        # Handle price as cents (0-100) or decimal (0-1)
        if price > 1:
            price_decimal = price / 100.0
        else:
            price_decimal = price
        
        count = trade.get('count', 1)
        
        # Calculate stability impact
        # Large trades have more impact
        volume_usd = count * price_decimal * 100  # Approximate USD value
        stability_delta = min(volume_usd / 10000, 5.0)  # Max 5% per trade
        
        # YES trades anchor (stabilise), NO trades destabilise
        if side == 'NO':
            stability_delta = -stability_delta
        
        # Get or create SYSTEM agent for wing flaps
        from backend.database.models import Agent, AgentArchetype, User
        from backend.auth.password import hash_password
        
        system_user_result = await session.execute(
            select(User).where(User.id == "SYSTEM")
        )
        system_user = system_user_result.scalar_one_or_none()
        
        if not system_user:
            system_user = User(
                id="SYSTEM",
                username="SYSTEM",
                email="system@echelon.io",
                password_hash=hash_password("system"),
                tier="system",
            )
            session.add(system_user)
            await session.flush()
        
        system_agent_result = await session.execute(
            select(Agent).where(Agent.id == "SYSTEM")
        )
        system_agent = system_agent_result.scalar_one_or_none()
        
        if not system_agent:
            system_agent = Agent(
                id="SYSTEM",
                name="SYSTEM",
                archetype=AgentArchetype.DEGEN,
                owner_id="SYSTEM",
                wallet_address="0x0000000000000000000000000000000000000000",
                is_alive=True,
            )
            session.add(system_agent)
            await session.flush()
        
        # Calculate new stability
        new_stability = max(0, min(100, timeline.stability + stability_delta))
        
        flap_id = f"KALSHI_{timeline.id}_{uuid.uuid4().hex[:8]}"
        # Convert to naive datetime for database (column is TIMESTAMP WITHOUT TIME ZONE)
        flap_timestamp = datetime.now(timezone.utc).replace(tzinfo=None)
        flap = WingFlap(
            id=flap_id,
            timeline_id=timeline.id,
            agent_id="SYSTEM",
            flap_type=WingFlapType.TRADE,
            action=f"Kalshi: {count} {side} @ ${price_decimal:.2f}",
            stability_delta=stability_delta,
            direction="ANCHOR" if stability_delta > 0 else "DESTABILISE",
            volume_usd=volume_usd,
            timeline_stability=new_stability,
            timeline_price=price_decimal,
            timestamp=flap_timestamp,
        )
        session.add(flap)
        
        # Update timeline stability and volume
        # Note: updated_at is auto-updated by SQLAlchemy
        current_volume = timeline.total_volume_usd or 0.0
        await session.execute(
            update(Timeline)
            .where(Timeline.id == timeline.id)
            .values(
                stability=new_stability,
                total_volume_usd=current_volume + volume_usd
            )
        )
