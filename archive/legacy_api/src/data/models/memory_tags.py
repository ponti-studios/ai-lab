from sqlalchemy import Column, ForeignKey, Table, UUID

from src.data.db import Base

# Association table for many-to-many relationship between Memory and Tag
memory_tags = Table(
    "memory_tags",
    Base.metadata,
    Column("memory_id", UUID(as_uuid=True), ForeignKey("memories.id")),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("tags.id")),
)
