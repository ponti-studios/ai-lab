import datetime
import enum
import traceback
import uuid

from pydantic import BaseModel
from sqlalchemy import ARRAY, UUID, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from src.data.db import Base
from src.data.models import focus


class MessageRole(enum.Enum):
    SYSTEM = "system"
    ASSISTANT = "assistant"
    USER = "user"


class ChatState(enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ENDED = "ENDED"


class Chat(Base):
    __tablename__ = "chats"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        unique=True,
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id"))
    state: Mapped[str] = mapped_column(String, nullable=False, default=ChatState.ACTIVE.value)

    # Metadata
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.now(datetime.UTC)
    )

    def to_json(self):
        return {
            "id": self.id,
            "title": self.title,
            "profile_id": self.profile_id,
            "state": self.state,
            "created_at": self.created_at,
        }

    def __repr__(self):
        return f"<Chat(id={self.id}, title={self.title})>"


class MessageOutput(BaseModel):
    id: uuid.UUID
    message: str
    role: str
    chat_id: uuid.UUID
    profile_id: uuid.UUID
    created_at: datetime.datetime
    focus_ids: list[int] | None
    focus_items: list[focus.FocusItem] | None


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        unique=True,
    )
    message: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String, nullable=False)
    chat_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("chats.id"))
    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id"))
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.now(datetime.UTC)
    )

    focus_ids: Mapped[list[int]] = mapped_column(ARRAY(Integer), nullable=True)

    def get_focus_items(self, session) -> list[focus.FocusItem]:
        if self.focus_ids:
            focus_items = session.query(focus.Focus).filter(focus.Focus.id.in_(self.focus_ids)).all()
            return [item.to_model() for item in focus_items]
        return []

    def to_model(self, session: Session) -> MessageOutput:
        if self.focus_ids:
            focus_items = self.get_focus_items(session)
        else:
            focus_items = []

        try:
            return MessageOutput(
                id=self.id,
                message=self.message,
                role=self.role,
                chat_id=self.chat_id,
                profile_id=self.profile_id,
                created_at=self.created_at,
                focus_ids=self.focus_ids,
                focus_items=focus_items,
            )
        except Exception as e:
            traceback.print_exc()
            raise ValueError(f"Error converting Message to pydantic model: {e}")

    def __repr__(self):
        return f"<Message(id={self.id}, message={self.message})>"


Chat.messages = relationship("Message", back_populates="chat")
Chat.profile = relationship("Profile", back_populates="chats")
Message.chat = relationship("Chat", back_populates="messages")
