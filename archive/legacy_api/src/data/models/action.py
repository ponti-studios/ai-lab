import uuid
from datetime import datetime

from sqlalchemy import UUID, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.data.db import Base


class Action(Base):
    __tablename__ = "actions"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        unique=True,
    )
    queue_id = Column(UUID(as_uuid=True), ForeignKey("queues.id"))
    type = Column(String, nullable=False)
    content = Column(String, nullable=False)
    status = Column(String, nullable=False)
    priority = Column(Integer)
    deadline = Column(DateTime)
    result = Column(String)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Action(id={self.id}, type={self.type})>"


Action.profile = relationship("Profile", back_populates="actions")
Action.queue = relationship("Queue", back_populates="actions")
