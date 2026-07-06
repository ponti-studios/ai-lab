import uuid
from datetime import UTC, datetime

from sqlalchemy import UUID, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.data.db import Base


class Context(Base):
    __tablename__ = "context"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        unique=True,
    )
    name = Column(String, nullable=False)
    content = Column(String, nullable=False)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"))
    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, default=datetime.now(UTC))

    def __repr__(self):
        return f"<Context(id={self.id}, name={self.name})>"


class SystemState(Base):
    __tablename__ = "system_state"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        unique=True,
    )
    current_focus = Column(String)
    mood = Column(String)
    parameters = Column(String)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"))
    updated_at = Column(DateTime, default=datetime.now(UTC))

    def __repr__(self):
        return f"<SystemState(id={self.id}, current_focus={self.current_focus})>"


Context.profile = relationship("Profile", back_populates="contexts")
SystemState.profile = relationship("Profile", back_populates="system_state")
