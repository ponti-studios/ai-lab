import uuid
from datetime import datetime

from sqlalchemy import UUID, Column, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.data.db import Base


class Memory(Base):
    __tablename__ = "memories"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        unique=True,
    )
    content = Column(String, nullable=False)
    importance = Column(Float)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"))
    last_accessed = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Memory(id={self.id}, content={self.content})>"


Memory.profile = relationship("Profile", back_populates="memories")
Memory.entities = relationship("EntityMemory", back_populates="memory")
Memory.tags = relationship("Tag", secondary="memory_tags", back_populates="memories")
