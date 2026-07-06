from typing import Annotated

from fastapi import HTTPException, Request, status
from fastapi.params import Depends
from sqlalchemy.orm import Session

from src.data.db import get_db
from src.data.models.user import Profile, User
from src.data.users_repository import get_user_by_token
from src.utils.config import settings

SessionDep = Annotated[Session, Depends(get_db)]
# TokenDep = Annotated[str, Depends(reusable_oauth2)]


def get_current_user(db: SessionDep, request: Request) -> User:
    if settings.ENVIRONMENT == "local" and request.query_params.get("dev"):
        user = db.query(User).first()
        if not user:
            raise HTTPException(status_code=400, detail="User not found")
        return user

    authorization = request.headers.get("Authorization")
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ")[1]

    user = get_user_by_token(db, token)
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_active_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges")
    return current_user


def get_profile(db: SessionDep, user: CurrentUser) -> Profile:
    profile = db.query(Profile).filter(Profile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


ProfileDepends = Depends(get_profile)
CurrentProfile = Annotated[Profile, ProfileDepends]
