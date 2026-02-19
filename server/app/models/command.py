"""Command model for agent-miner actions."""
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Text, func
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base


class CommandType(str, enum.Enum):
    RESTART = "restart"
    UPDATE_WORKER = "update_worker"
    GET_REALTIME = "get_realtime"
    POWER_OFF = "power_off"
    POWER_ON = "power_on"
    RESCAN = "rescan"


class CommandStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Command(Base):
    """Command - queued action for agent to execute on miner."""

    __tablename__ = "commands"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    miner_id: Mapped[int | None] = mapped_column(ForeignKey("miners.id", ondelete="SET NULL"), nullable=True)  # null for rescan
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    params: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default=CommandStatus.PENDING.value)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    agent: Mapped["Agent"] = relationship("Agent", back_populates="commands")
    miner: Mapped["Miner | None"] = relationship("Miner", back_populates="commands")
