import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import List, Optional

import pydantic
from langchain.pydantic_v1 import BaseModel, Field
from sqlalchemy import UUID, Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, Session, mapped_column
from sqlalchemy.types import DateTime

from src.data.db import Base
from src.utils.date_tools import date_to_iso


class FocusState(Enum):
    backlog = "backlog"
    active = "active"
    completed = "completed"
    deleted = "deleted"


class ItemType(str, Enum):
    event = "event"
    task = "task"
    goal = "goal"
    reminder = "reminder"


class TaskSize(str, Enum):
    small = "small"
    medium = "medium"
    large = "large"
    epic = "epic"


class Category(str, Enum):
    career = "career"
    personal_development = "personal_development"
    physical_health = "physical_health"
    mental_health = "mental_health"
    finance = "finance"
    education = "education"
    relationships = "relationships"
    home = "home"
    shopping = "shopping"
    interests = "interests"
    adventure = "adventure"
    technology = "technology"
    spirituality = "spirituality"
    productivity = "productivity"
    creativity = "creativity"
    culture = "culture"
    legal = "legal"
    events = "events"
    projects = "projects"


class Sentiment(str, Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"


class UserIntentTask(BaseModel):
    id: str
    category: str = Field(description="The category of the life management task.")
    due_date: Optional[str] = Field(
        None,
        description="The deadline for completing the item in YYYY-MM-DDTHH:MM format. Example: due_date: 2023-01-01T12:00",
    )
    priority: int = Field(
        description="The priority of the item. 1 is the highest priority and 5 is the lowest priority.",
        ge=1,
        le=5,
    )
    state: FocusState = Field(description="Whether the user has done this task.")
    location: Optional[str] = Field(description="The location associated with the item.")
    keywords: List[str] = Field(description="The keywords associated with the item.")
    sentiment: Sentiment
    task_size: TaskSize
    text: str
    type: ItemType


class FocusItemBase(pydantic.BaseModel):
    category: str
    due_date: Optional[str] = None
    priority: int
    sentiment: str
    task_size: str
    text: str
    type: str


class FocusItem(FocusItemBase):
    id: int
    state: FocusState
    profile_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class Focus(Base):
    __tablename__ = "focus"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String, nullable=False, default="general")
    due_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    sentiment: Mapped[str] = mapped_column(String, nullable=False, default="neutral")
    state: Mapped[FocusState] = mapped_column(String, nullable=False, default=FocusState.backlog.value)
    task_size: Mapped[str] = mapped_column(String, nullable=False, default="medium")
    text: Mapped[str] = mapped_column(nullable=False)
    type: Mapped[str] = mapped_column(nullable=False, default="task")
    in_vector_store: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    profile_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("profiles.id"), nullable=False)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(UTC))

    def to_model(self) -> FocusItem:
        return FocusItem(
            id=self.id,
            text=self.text,
            type=self.type,
            task_size=self.task_size,
            category=self.category,
            priority=self.priority,
            sentiment=self.sentiment,
            due_date=date_to_iso(self.due_date),
            profile_id=self.profile_id,
            state=self.state,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    def to_json(self):
        return {
            key: value
            for key, value in {
                "id": str(self.id),
                "text": self.text,
                "type": self.type,
                "task_size": self.task_size,
                "category": self.category,
                "priority": self.priority,
                "profile_id": str(self.profile_id) if self.profile_id else None,
                "sentiment": self.sentiment,
                "state": str(self.state) if self.state else None,
                "due_date": date_to_iso(self.due_date),
                "created_at": date_to_iso(self.created_at),
                "updated_at": date_to_iso(self.updated_at),
            }.items()
            if value is not None
        }


def get_focus_by_profile_id(session: Session, profile_id: uuid.UUID):
    return session.query(Focus).filter(Focus.profile_id == profile_id).all()


def get_focus_by_id(session: Session, focus_id: int) -> Focus | None:
    return session.query(Focus).filter(Focus.id == focus_id).first()


def create_focus(session: Session, text: str, profile_id: uuid.UUID) -> Focus:
    focus = Focus(text=text, profile_id=profile_id)
    session.add(focus)
    session.commit()
    session.flush()
    return focus


def complete_focus(session: Session, focus_id: int) -> Focus:
    focus = get_focus_by_id(session, focus_id)
    focus.state = FocusState.completed.value  # type: ignore
    session.commit()
    session.flush()
    return focus
