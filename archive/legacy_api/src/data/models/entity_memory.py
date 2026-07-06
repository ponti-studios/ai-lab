import uuid

from sqlalchemy import UUID, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.data.db import Base


class EntityMemory(Base):
    __tablename__ = "entity_memories"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        unique=True,
    )
    entity_id = Column(UUID(as_uuid=True), ForeignKey("entities.id"))
    memory_id = Column(UUID(as_uuid=True), ForeignKey("memories.id"))

    def __repr__(self):
        return f"<EntityMemory(id={self.id}, entity_id={self.entity_id}, memory_id={self.memory_id})>"


EntityMemory.entity = relationship("Entity", back_populates="memories")
EntityMemory.memory = relationship("Memory", back_populates="entities")
