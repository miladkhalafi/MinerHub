"""Agent model."""
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Agent(Base):
    """Agent - Raspberry Pi process that scans LAN and manages miners."""

    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.id", ondelete="CASCADE"), nullable=False)
    token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), default="Agent")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    farm: Mapped["Farm"] = relationship("Farm", back_populates="agents")
    miners: Mapped[list["Miner"]] = relationship("Miner", back_populates="agent", cascade="all, delete-orphan")
    commands: Mapped[list["Command"]] = relationship("Command", back_populates="agent", cascade="all, delete-orphan")
