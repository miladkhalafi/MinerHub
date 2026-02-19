"""Miner model."""
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Miner(Base):
    """Miner - WhatsMiner device, identified by MAC."""

    __tablename__ = "miners"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    mac: Mapped[str] = mapped_column(String(17), unique=True, nullable=False, index=True)  # xx:xx:xx:xx:xx:xx
    ip: Mapped[str] = mapped_column(String(45), nullable=True)  # IPv4 or IPv6
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    worker1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    worker2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    worker3: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    added_by_scan_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    agent: Mapped["Agent"] = relationship("Agent", back_populates="miners")
    commands: Mapped[list["Command"]] = relationship("Command", back_populates="miner", cascade="all, delete-orphan")
