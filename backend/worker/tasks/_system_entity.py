"""Shared SYSTEM user + agent entity helper.

Eliminates the ~30-line boilerplate duplicated across entropy.py,
paradox.py, and market_sync.py. Idempotent — safe to call every tick.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Agent, AgentArchetype, User
from backend.auth.password import hash_password


_SYSTEM_ID = "SYSTEM"
_SYSTEM_EMAIL = "system@echelon.io"
_SYSTEM_WALLET = "0x0000000000000000000000000000000000000000"


async def ensure_system_entities(session: AsyncSession) -> tuple[User, Agent]:
    """Return (system_user, system_agent), creating them if absent.

    Both entities use id="SYSTEM". The function is idempotent and safe to
    call from multiple task paths within the same session.
    """
    # --- User ---
    result = await session.execute(
        select(User).where(User.id == _SYSTEM_ID)
    )
    system_user = result.scalar_one_or_none()

    if not system_user:
        system_user = User(
            id=_SYSTEM_ID,
            username=_SYSTEM_ID,
            email=_SYSTEM_EMAIL,
            password_hash=hash_password("system"),
            tier="system",
        )
        session.add(system_user)
        await session.flush()

    # --- Agent ---
    result = await session.execute(
        select(Agent).where(Agent.id == _SYSTEM_ID)
    )
    system_agent = result.scalar_one_or_none()

    if not system_agent:
        system_agent = Agent(
            id=_SYSTEM_ID,
            name=_SYSTEM_ID,
            archetype=AgentArchetype.DEGEN,
            owner_id=_SYSTEM_ID,
            wallet_address=_SYSTEM_WALLET,
            is_alive=True,
        )
        session.add(system_agent)
        await session.flush()

    return system_user, system_agent
