import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os

from main import app
from core.config import settings
from db.base_class import Base
from db.session import get_db
from services.avatar_service import generate_avatar


engine = create_engine(
    settings.TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db_session = TestingSessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
def test_user(db):
    from crud.crud_user import user as crud_user
    from schemas.user import UserCreate

    username = "testuser"
    password = "testpassword"
    user_in = UserCreate(username=username, password=password)
    user = crud_user.create(db, obj_in=user_in)

    # Generate and assign default avatar
    avatar_url = generate_avatar(user.username)
    user.avatar_url = avatar_url
    user.is_default_avatar = True
    db.add(user)
    db.commit()
    db.refresh(user)

    yield {"user": user, "password": password}

    # Clean up the created avatar
    avatar_path = avatar_url.lstrip("/")
    if os.path.exists(avatar_path):
        os.remove(avatar_path)


@pytest.fixture(scope="function")
def authorized_client(client, test_user):
    """
    Fixture for a client that is pre-authorized with a valid token.
    """
    login_data = {
        "username": test_user["user"].username,
        "password": test_user["password"],
    }
    response = client.post("/api/v1/login/access-token", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    client.headers = {"Authorization": f"Bearer {token}"}
    return client
