"""User service."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.auth import hash_password


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Get user by email."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    """Get user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def list_users(db: AsyncSession) -> list[User]:
    """List all users."""
    result = await db.execute(select(User).order_by(User.email))
    return list(result.scalars().all())


async def create_user(
    db: AsyncSession,
    email: str,
    password: str,
    role: str = "user",
) -> User:
    """Create a new user."""
    user = User(
        email=email.strip().lower(),
        password_hash=hash_password(password),
        role=role,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def update_user(
    db: AsyncSession,
    user: User,
    email: str | None = None,
    password: str | None = None,
    role: str | None = None,
) -> User:
    """Update user."""
    if email is not None:
        user.email = email.strip().lower()
    if password is not None and password:
        user.password_hash = hash_password(password)
    if role is not None:
        user.role = role
    await db.flush()
    await db.refresh(user)
    return user


async def count_users(db: AsyncSession) -> int:
    """Count total users."""
    from sqlalchemy import func
    result = await db.execute(select(func.count()).select_from(User))
    return result.scalar() or 0
