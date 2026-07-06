from sqlalchemy import Column, ForeignKey, UUID, Table

from src.data.db import Base

note_tags = Table(
    "note_tags",
    Base.metadata,
    Column("note_id", UUID(as_uuid=True), ForeignKey("notes.id")),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("tags.id")),
)
