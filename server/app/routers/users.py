"""User management endpoints (admin only)."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import require_admin
from app.services import user_service
from app.models import User

router = APIRouter(prefix="/users", tags=["users"])


class UserCreate(BaseModel):
    email: str
    password: str
    role: str = "user"


class UserUpdate(BaseModel):
    email: str | None = None
    password: str | None = None
    role: str | None = None


class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    created_at: str

    class Config:
        from_attributes = True


@router.get("", response_model=list[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    """List all users (admin only)."""
    users = await user_service.list_users(db)
    return [
        UserResponse(
            id=u.id,
            email=u.email,
            role=u.role,
            created_at=u.created_at.isoformat() if u.created_at else "",
        )
        for u in users
    ]


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    """Create a new user (admin only)."""
    if data.role not in ("admin", "user"):
        raise HTTPException(status_code=400, detail="Role must be admin or user")
    existing = await user_service.get_user_by_email(db, data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    u = await user_service.create_user(db, data.email, data.password, data.role)
    return UserResponse(
        id=u.id,
        email=u.email,
        role=u.role,
        created_at=u.created_at.isoformat() if u.created_at else "",
    )


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(require_admin),
):
    """Update user (admin only)."""
    u = await user_service.get_user_by_id(db, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    if data.role is not None and data.role not in ("admin", "user"):
        raise HTTPException(status_code=400, detail="Role must be admin or user")
    if data.email is not None:
        existing = await user_service.get_user_by_email(db, data.email)
        if existing and existing.id != user_id:
            raise HTTPException(status_code=400, detail="Email already registered")
    u = await user_service.update_user(
        db, u,
        email=data.email,
        password=data.password,
        role=data.role,
    )
    return UserResponse(
        id=u.id,
        email=u.email,
        role=u.role,
        created_at=u.created_at.isoformat() if u.created_at else "",
    )


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(require_admin),
):
    """Delete user (admin only). Cannot delete self."""
    if user_id == current.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    u = await user_service.get_user_by_id(db, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(u)
