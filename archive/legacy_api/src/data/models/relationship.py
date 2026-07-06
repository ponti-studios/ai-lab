import uuid

from sqlalchemy import UUID, Column, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.data.db import Base


class Relationship(Base):
    __tablename__ = "relationships"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        unique=True,
    )
    entity1_id = Column(UUID(as_uuid=True), ForeignKey("entities.id"))
    entity2_id = Column(UUID(as_uuid=True), ForeignKey("entities.id"))
    relationship_type = Column(String, nullable=False)
    strength = Column(Float)

    def __repr__(self):
        return f"<Relationship(id={self.id}, entity1_id={self.entity1_id}, entity2_id={self.entity2_id})>"
