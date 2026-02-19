"""Farm CRUD endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.services import farm_service

router = APIRouter(prefix="/farms", tags=["farms"])


class FarmCreate(BaseModel):
    name: str


class FarmUpdate(BaseModel):
    name: str


class FarmResponse(BaseModel):
    id: int
    name: str
    created_at: str

    class Config:
        from_attributes = True


@router.get("", response_model=list[FarmResponse])
async def list_farms(db: AsyncSession = Depends(get_db)):
    """List all farms."""
    farms = await farm_service.list_farms(db)
    return [
        FarmResponse(
            id=f.id,
            name=f.name,
            created_at=f.created_at.isoformat() if f.created_at else "",
        )
        for f in farms
    ]


@router.post("", response_model=FarmResponse, status_code=201)
async def create_farm(data: FarmCreate, db: AsyncSession = Depends(get_db)):
    """Create a new farm."""
    farm = await farm_service.create_farm(db, data.name)
    return FarmResponse(
        id=farm.id,
        name=farm.name,
        created_at=farm.created_at.isoformat() if farm.created_at else "",
    )


@router.get("/{farm_id}")
async def get_farm(farm_id: int, db: AsyncSession = Depends(get_db)):
    """Get farm detail with agent and miners."""
    from app.services import agent_service

    farm = await farm_service.get_farm(db, farm_id)
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    agent = await agent_service.get_agent_for_farm(db, farm_id)
    agent_data = None
    if agent:
        agent_data = {
            "id": agent.id,
            "token": agent.token,
            "name": agent.name,
            "last_seen": agent.last_seen.isoformat() if agent.last_seen else None,
            "miners": [
                {
                    "id": m.id,
                    "mac": m.mac,
                    "ip": m.ip,
                    "model": m.model,
                    "worker1": m.worker1,
                    "worker2": m.worker2,
                    "worker3": m.worker3,
                }
                for m in agent.miners
            ],
        }

    return {
        "id": farm.id,
        "name": farm.name,
        "created_at": farm.created_at.isoformat() if farm.created_at else "",
        "agent": agent_data,
    }


@router.patch("/{farm_id}", response_model=FarmResponse)
async def update_farm(farm_id: int, data: FarmUpdate, db: AsyncSession = Depends(get_db)):
    """Update farm name."""
    farm = await farm_service.get_farm(db, farm_id)
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    farm = await farm_service.update_farm(db, farm, data.name)
    return FarmResponse(
        id=farm.id,
        name=farm.name,
        created_at=farm.created_at.isoformat() if farm.created_at else "",
    )


@router.delete("/{farm_id}", status_code=204)
async def delete_farm(farm_id: int, db: AsyncSession = Depends(get_db)):
    """Delete farm and cascade to agents/miners."""
    farm = await farm_service.get_farm(db, farm_id)
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    await farm_service.delete_farm(db, farm)
