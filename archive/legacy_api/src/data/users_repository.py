import json
import uuid
from dataclasses import dataclass
from typing import List
from uuid import UUID

import jwt
from fastapi import HTTPException, status
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from src.data.chat_repository import get_user_chat_messages
from src.data.models.focus import get_focus_by_profile_id
from src.data.models.user import (
    User,
    create_profile,
    create_user,
    get_user_by_user_id,
)
from src.services.supabase import supabase_client
from src.utils import security
from src.utils.config import settings
from src.utils.logger import logger
from src.utils.security import AccessTokenSubject, TokenService


class AuthPayload(BaseModel):
    user_id: uuid.UUID
    access_token: str
    refresh_token: str


def get_user_by_token(session: Session, token: str) -> User:
    try:
        if settings.ENVIRONMENT == "test":
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[security.JWT_ALGORITHM])
            sub = json.loads(payload["sub"])
            email = sub["email"]
            user = session.query(User).filter(User.email == email).first()
        else:
            response = supabase_client.auth.get_user(token)
            if response is None or response.user is None:
                raise HTTPException(status_code=403, detail="Invalid authentication credentials")
            user_id = response.user.id
            user = get_user_by_user_id(session, uuid.UUID(user_id))
            # If the user has Supabase auth but not a local user, create a local user and profile
            if not user and response.user.email is not None:
                user = create_user(session, user_id=user_id, email=response.user.email)
                profile = create_profile(session, user_id=user.id, provider="apple")

        if not user:
            raise HTTPException(status_code=400, detail="User not found")
        elif not user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")

        return user
    except (Exception, HTTPException, jwt.InvalidTokenError, ValidationError) as e:
        if isinstance(e, HTTPException):
            raise e
        elif isinstance(e, jwt.InvalidTokenError):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authentication credentials",
            )
        elif isinstance(e, ValidationError):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Invalid authentication credentials: {str(e)}",
            )
        elif isinstance(e, IndexError):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        else:
            logger.error(f"Error getting user: {str(e)}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Unauthorized: {str(e)}")


async def refresh_token(db: Session, refresh_token: str) -> AuthPayload:
    payload = TokenService.decode_access_token(refresh_token)

    user = db.query(User).filter(User.id == payload.sub.id).first()

    if user is None:
        raise ValueError("User not found")

    subject = AccessTokenSubject(id=str(user.id), email=user.email, name=user.name)
    access_token = TokenService.create_access_token(subject=subject)
    new_refresh_token = TokenService.create_refresh_token(subject)

    return AuthPayload(user_id=user.id, access_token=access_token, refresh_token=new_refresh_token)


@dataclass(frozen=True)
class UserContext:
    chat_history: List[str]
    focus_items: List[str]


def get_user_context(session: Session, profile_id: UUID) -> UserContext:
    chat_history = get_user_chat_messages(session, profile_id=profile_id)
    focus_items = get_focus_by_profile_id(profile_id=profile_id, session=session)
    chat_history_contents = [str(message.message) for message in chat_history]

    return UserContext(
        chat_history=chat_history_contents,
        focus_items=[f"{str(item.text)} - State: {str(item.state)}" for item in focus_items],
    )
