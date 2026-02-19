"""Farm service."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Farm


async def list_farms(db: AsyncSession) -> list[Farm]:
    """List all farms."""
    result = await db.execute(select(Farm).order_by(Farm.name))
    return list(result.scalars().all())


async def get_farm(db: AsyncSession, farm_id: int) -> Farm | None:
    """Get farm by ID."""
    result = await db.execute(select(Farm).where(Farm.id == farm_id))
    return result.scalar_one_or_none()


async def create_farm(db: AsyncSession, name: str) -> Farm:
    """Create a new farm."""
    farm = Farm(name=name)
    db.add(farm)
    await db.flush()
    await db.refresh(farm)
    return farm


async def update_farm(db: AsyncSession, farm: Farm, name: str) -> Farm:
    """Update farm name."""
    farm.name = name
    await db.flush()
    await db.refresh(farm)
    return farm


async def delete_farm(db: AsyncSession, farm: Farm) -> None:
    """Delete farm and cascade to agents/miners."""
    await db.delete(farm)
