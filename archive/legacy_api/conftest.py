import uuid
from datetime import timedelta
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import tests.mocks.mock_chroma_service

from src.data.db import Base
from src.data.models.chat import Chat, ChatState
from src.data.models.user import Profile, User
from src.main import app

# Import the module you want to test
from src.utils.config import settings
from src.utils.context import get_db
from src.utils.security import ACCESS_TOKEN_EXPIRE_MINUTES, AccessTokenSubject, TokenService


# Patch the entire chroma_service module
@pytest.fixture(autouse=True)
def mock_chroma_service():
    with patch("src.services.chroma_service", tests.mocks.mock_chroma_service):
        yield


# You can add more tests as needed
# Test database URL
TEST_DATABASE_URL = "postgresql://postgres:postgres@localhost:5434/test_db"


@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = SessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.rollback()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def auth_headers():
    access_token = TokenService.create_access_token(
        subject=AccessTokenSubject(id="1234567890", email="test@example.com", name="Test User"),
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
def user(db_session):
    user = User(id=uuid.uuid4(), email="test@example.com", provider="apple")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Verify the user exists in the database
    queried_user = db_session.query(User).filter(User.email == "test@example.com").first()

    return queried_user


@pytest.fixture(scope="function")
def profile(db_session, user):
    profile = Profile(id=uuid.uuid4(), user_id=user.id, provider="google")
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)
    return profile


@pytest.fixture(scope="function")
def active_chat(db_session, profile):
    chat = Chat(profile_id=profile.id, state=ChatState.ACTIVE.value, title="Test Chat")
    db_session.add(chat)
    db_session.commit()
    db_session.refresh(chat)
    return chat
