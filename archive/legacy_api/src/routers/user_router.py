import uuid

from fastapi import APIRouter, status
from fastapi.exceptions import HTTPException
from pydantic import BaseModel

from src.data.models.user import Profile, User, create_profile, create_user
from src.utils.context import CurrentProfile, SessionDep

user_router = APIRouter()


class CreateUserInput(BaseModel):
    email: str
    name: str
    user_id: str


class ProfileOutput(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    user_id: uuid.UUID
    # access_token: str
    # refresh_token: str


@user_router.get("/profile")
async def get_profile(profile: CurrentProfile) -> ProfileOutput:
    return ProfileOutput(
        id=profile.id,
        email=profile.user.email,
        full_name=profile.full_name,
        user_id=profile.user_id,
    )


class UpdateProfileInput(BaseModel):
    full_name: str


@user_router.put("/profile")
async def update_profile(profile: CurrentProfile, db: SessionDep, input: UpdateProfileInput) -> ProfileOutput:
    profile = db.query(Profile).filter(Profile.user_id == profile.user.id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile does not exist")

    if input.full_name:
        setattr(profile, "full_name", input.full_name)

    db.commit()

    return ProfileOutput(
        id=profile.id,
        email=profile.user.email,
        full_name=str(profile.full_name),
        user_id=profile.user_id,
    )


@user_router.post("/create")
def create_user_and_profile(db: SessionDep, input: CreateUserInput) -> ProfileOutput:
    user = db.query(User).filter(User.email == input.email).first()
    if user:
        profile = db.query(Profile).filter(Profile.user_id == user.id).first()
    else:
        user = create_user(
            session=db, user_id=input.user_id, email=input.email, name=input.name, provider="apple"
        )
        profile = create_profile(session=db, name=input.name, user_id=user.id, provider="apple")

    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile does not exist")

    # access_token_subject = AccessTokenSubject(
    #     id=str(user.id),
    #     email=user.email,
    #     name=user.name,
    # )
    # access_token = TokenService.create_access_token(subject=access_token_subject)
    # refresh_token = TokenService.create_refresh_token(access_token_subject)

    return ProfileOutput(
        id=profile.id,
        email=user.email,
        user_id=user.id,
        full_name=profile.full_name,
        # access_token=access_token,
        # refresh_token=refresh_token,
    )
