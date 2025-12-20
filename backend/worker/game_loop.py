"""
Echelon Game Loop - The Heartbeat of the Simulation

This runs continuously, ticking game mechanics:
- Entropy (stability decay)
- Paradox detection
- Polymarket market sync
- OSINT polling
- Agent decisions

Run with: python -m backend.worker.game_loop
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from backend.database.connection import async_session_maker, init_db
from backend.worker.tasks.entropy import EntropyTask
from backend.worker.tasks.paradox import ParadoxTask
from backend.worker.tasks.market_sync import MarketSyncTask
from backend.worker.tasks.agent_tick import AgentTickTask

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('echelon.gameloop')


class GameLoop:
    """
    The heartbeat of Echelon.
    
    Runs multiple tasks at different intervals:
    - Entropy: Every 60 seconds
    - Paradox scan: Every 30 seconds
    - Market sync: Every 10 seconds
    - Agent tick: Every 5 seconds
    """
    
    def __init__(self):
        self.running = False
        self.tick_count = 0
        self.start_time: Optional[datetime] = None
        
        # Task instances
        self.entropy_task = EntropyTask()
        self.paradox_task = ParadoxTask()
        self.market_task = MarketSyncTask()
        self.agent_task = AgentTickTask()
        
        # Task intervals (in seconds)
        self.intervals = {
            'entropy': 60,      # Decay stability every minute
            'paradox': 30,       # Check for breaches every 30s
            'market': 10,        # Sync prices every 10s
            'agent': 5,          # Agent decisions every 5s
        }
        
        # Last run times (timezone-aware)
        # Use epoch start instead of datetime.min to avoid timezone issues
        min_time = datetime(1970, 1, 1, tzinfo=timezone.utc)
        self.last_run = {
            'entropy': min_time,
            'paradox': min_time,
            'market': min_time,
            'agent': min_time,
        }
    
    async def start(self):
        """Start the game loop."""
        logger.info("=" * 60)
        logger.info("ECHELON GAME LOOP STARTING")
        logger.info("=" * 60)
        
        # Initialise database
        await init_db()
        logger.info("Database connection established")
        
        self.running = True
        self.start_time = datetime.now(timezone.utc)
        
        logger.info(f"Task intervals: {self.intervals}")
        logger.info("Game loop active. Press Ctrl+C to stop.")
        logger.info("-" * 60)
        
        try:
            await self._run_loop()
        except asyncio.CancelledError:
            logger.info("Game loop cancelled")
        except Exception as e:
            logger.error(f"Game loop error: {e}", exc_info=True)
        finally:
            self.running = False
            logger.info("Game loop stopped")
    
    async def _run_loop(self):
        """Main loop - runs forever until cancelled."""
        while self.running:
            self.tick_count += 1
            now = datetime.now(timezone.utc)
            
            # Create database session for this tick
            async with async_session_maker() as session:
                try:
                    # Run tasks that are due
                    await self._run_due_tasks(session, now)
                    await session.commit()
                except Exception as e:
                    logger.error(f"Tick {self.tick_count} error: {e}")
                    await session.rollback()
            
            # Sleep until next tick (1 second resolution)
            await asyncio.sleep(1)
    
    async def _run_due_tasks(self, session, now: datetime):
        """Run any tasks that are due based on their intervals."""
        
        # Entropy decay
        if self._is_due('entropy', now):
            await self._run_task('entropy', self.entropy_task.tick, session)
        
        # Paradox detection
        if self._is_due('paradox', now):
            await self._run_task('paradox', self.paradox_task.tick, session)
        
        # Market sync (Polymarket)
        if self._is_due('market', now):
            await self._run_task('market', self.market_task.tick, session)
        
        # Agent decisions
        if self._is_due('agent', now):
            await self._run_task('agent', self.agent_task.tick, session)
    
    def _is_due(self, task_name: str, now: datetime) -> bool:
        """Check if a task is due to run."""
        interval = timedelta(seconds=self.intervals[task_name])
        return now - self.last_run[task_name] >= interval
    
    async def _run_task(self, task_name: str, task_fn, session):
        """Run a task and update its last run time."""
        try:
            start = datetime.now(timezone.utc)
            result = await task_fn(session)
            elapsed = (datetime.now(timezone.utc) - start).total_seconds()
            
            self.last_run[task_name] = datetime.now(timezone.utc)
            
            if result:
                logger.info(f"[{task_name.upper():8}] {result} ({elapsed:.2f}s)")
            
        except Exception as e:
            logger.error(f"[{task_name.upper():8}] Failed: {e}")
    
    def stop(self):
        """Stop the game loop."""
        self.running = False


async def main():
    """Entry point for the game loop."""
    loop = GameLoop()
    
    try:
        await loop.start()
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
        loop.stop()


if __name__ == "__main__":
    asyncio.run(main())

