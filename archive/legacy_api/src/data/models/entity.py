import uuid
from datetime import datetime

from sqlalchemy import UUID, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.data.db import Base


class Entity(Base):
    __tablename__ = "entities"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        unique=True,
    )
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    attributes = Column(String)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Entity(id={self.id}, name={self.name})>"


Entity.profile = relationship("Profile", back_populates="entities")
Entity.memories = relationship("EntityMemory", back_populates="entity")
