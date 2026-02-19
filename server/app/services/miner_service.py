"""Miner service."""
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Miner, Agent
from app.crypto_utils import encrypt_password, decrypt_password


async def get_miner_by_id(db: AsyncSession, miner_id: int) -> Miner | None:
    """Get miner by ID with agent."""
    result = await db.execute(
        select(Miner)
        .where(Miner.id == miner_id)
        .options(selectinload(Miner.agent))
    )
    return result.scalar_one_or_none()


async def get_miner_by_mac(db: AsyncSession, mac: str) -> Miner | None:
    """Get miner by MAC address."""
    result = await db.execute(
        select(Miner)
        .where(Miner.mac == mac)
        .options(selectinload(Miner.agent))
    )
    return result.scalar_one_or_none()


async def upsert_miner(
    db: AsyncSession,
    agent_id: int,
    mac: str,
    ip: str | None = None,
    model: str | None = None,
) -> Miner:
    """Upsert miner by MAC. Update IP if changed."""
    miner = await get_miner_by_mac(db, mac)
    if miner:
        if miner.agent_id != agent_id:
            miner.agent_id = agent_id
        miner.ip = ip or miner.ip
        if model:
            miner.model = model
        await db.flush()
        await db.refresh(miner)
        return miner

    miner = Miner(
        agent_id=agent_id,
        mac=mac,
        ip=ip,
        model=model,
        added_by_scan_at=datetime.utcnow(),
    )
    db.add(miner)
    await db.flush()
    await db.refresh(miner)
    return miner


async def list_miners(db: AsyncSession, farm_id: int | None = None, agent_id: int | None = None) -> list[Miner]:
    """List miners, optionally filtered by farm_id or agent_id."""
    q = select(Miner).options(selectinload(Miner.agent).selectinload(Agent.farm))
    if farm_id is not None:
        q = q.join(Agent).where(Agent.farm_id == farm_id)
    if agent_id is not None:
        q = q.where(Miner.agent_id == agent_id)
    q = q.order_by(Miner.id)
    result = await db.execute(q)
    return list(result.scalars().all())


async def update_miner(
    db: AsyncSession,
    miner: Miner,
    *,
    worker1: str | None = None,
    worker2: str | None = None,
    worker3: str | None = None,
    password: str | None = None,
) -> Miner:
    """Update miner config."""
    if worker1 is not None:
        miner.worker1 = worker1 or None
    if worker2 is not None:
        miner.worker2 = worker2 or None
    if worker3 is not None:
        miner.worker3 = worker3 or None
    if password is not None:
        miner.password_encrypted = encrypt_password(password) if password else None
    await db.flush()
    await db.refresh(miner)
    return miner


def get_miner_password(miner: Miner) -> str | None:
    """Get decrypted password for miner."""
    return decrypt_password(miner.password_encrypted)
