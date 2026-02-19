"""Agent service."""
import secrets
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Agent, Farm, Miner


def generate_agent_token() -> str:
    """Generate a secure random token for agent authentication."""
    return secrets.token_urlsafe(32)


async def create_agent(db: AsyncSession, farm_id: int) -> Agent:
    """Register a new agent for a farm."""
    agent = Agent(
        farm_id=farm_id,
        token=generate_agent_token(),
    )
    db.add(agent)
    await db.flush()
    await db.refresh(agent)
    return agent


async def get_agent_by_id(db: AsyncSession, agent_id: int) -> Agent | None:
    """Get agent by ID with farm and miners."""
    result = await db.execute(
        select(Agent)
        .where(Agent.id == agent_id)
        .options(selectinload(Agent.farm), selectinload(Agent.miners))
    )
    return result.scalar_one_or_none()


async def get_agent_by_token(db: AsyncSession, token: str) -> Agent | None:
    """Get agent by token."""
    result = await db.execute(
        select(Agent)
        .where(Agent.token == token)
        .options(selectinload(Agent.farm), selectinload(Agent.miners))
    )
    return result.scalar_one_or_none()


async def get_agent_for_farm(db: AsyncSession, farm_id: int) -> Agent | None:
    """Get the agent for a farm (one agent per farm)."""
    result = await db.execute(
        select(Agent)
        .where(Agent.farm_id == farm_id)
        .options(selectinload(Agent.farm), selectinload(Agent.miners))
    )
    return result.scalar_one_or_none()


async def list_agents(db: AsyncSession, farm_id: int | None = None) -> list[Agent]:
    """List agents, optionally filtered by farm_id."""
    q = select(Agent).options(selectinload(Agent.farm), selectinload(Agent.miners))
    if farm_id is not None:
        q = q.where(Agent.farm_id == farm_id)
    q = q.order_by(Agent.id)
    result = await db.execute(q)
    return list(result.scalars().all())


async def update_agent_last_seen(db: AsyncSession, agent: Agent | int) -> None:
    """Update agent last_seen timestamp. Accepts Agent or agent_id."""
    from datetime import datetime, timezone
    if isinstance(agent, int):
        agent = await get_agent_by_id(db, agent)
    if agent:
        agent.last_seen = datetime.now(timezone.utc)
        await db.flush()
