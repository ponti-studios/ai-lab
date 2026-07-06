import uuid
from datetime import UTC, datetime, timedelta
from typing import Optional

from sqlalchemy import UUID, Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from src.data.db import Base
from src.utils.security import REFRESH_TOKEN_EXPIRE_DAYS


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        index=True,
        unique=True,
    )
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    profile = relationship("Profile", back_populates="user")
    refresh_tokens = relationship("RefreshToken", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, name={self.name})>"


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        unique=True,
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    user = relationship("User", back_populates="refresh_tokens")
    token = Column(String, unique=True, nullable=False)
    revoked = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now(UTC))
    expires_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )

    def __repr__(self):
        return f"<RefreshToken(id={self.id}, user_id={self.user_id})>"


class Profile(Base):
    __tablename__ = "profiles"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        unique=True,
    )
    full_name: Mapped[str | None] = mapped_column(String, nullable=True)
    provider: Mapped[str] = mapped_column(String, nullable=False)

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="profile")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC)
    )

    def __repr__(self):
        return f"<Profile(id={self.id}, full_name={self.full_name})>"


Profile.actions = relationship("Action", back_populates="profile")
Profile.chats = relationship("Chat", back_populates="profile")
Profile.entities = relationship("Entity", back_populates="profile")
Profile.queues = relationship("Queue", back_populates="profile")
Profile.memories = relationship("Memory", back_populates="profile")
Profile.notes = relationship("Note", back_populates="profile")
Profile.tags = relationship("Tag", back_populates="profile")

# State
Profile.contexts = relationship("Context", back_populates="profile")
Profile.system_state = relationship("SystemState", back_populates="profile")


def create_user(
    session: Session, user_id: str, email: str, name: Optional[str] = None, provider: Optional[str] = None
) -> User:
    user = User(
        id=user_id,
        email=email,
        name=name,
        provider=provider,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def create_profile(
    session: Session, user_id: uuid.UUID, name: Optional[str] = None, provider: Optional[str] = "apple"
) -> Profile:
    profile = Profile(full_name=name, provider=provider, user_id=user_id)
    session.add(profile)
    session.commit()
    return profile


def get_user_by_user_id(session: Session, user_id: uuid.UUID) -> User | None:
    user = session.query(User).filter(User.id == user_id).first()
    return user


def get_profile_by_user_id(session: Session, user_id: uuid.UUID) -> Profile | None:
    profile = session.query(Profile).filter(Profile.user_id == user_id).first()
    return profile


def migrate_profile_to_user(session: Session, user: User, profile: Profile) -> User:
    user.name = profile.full_name
    user.provider = profile.provider
    session.add(user)
    session.commit()
    return user
