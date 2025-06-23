import sys
import os
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from core.config import settings
from db.base import Base
from db.session import get_db
from tests.utils import random_lower_string


engine = create_engine(
    settings.TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def create_test_upload_dir():
    """Create the upload directory for test avatars before tests run and clean up after."""
    # Ensure the base uploads directory and avatars subdir exist
    avatars_dir = os.path.join(settings.UPLOADS_DIR, "avatars")
    if not os.path.exists(avatars_dir):
        os.makedirs(avatars_dir)

    yield

    # Teardown: Clean up the entire uploads directory
    if os.path.exists(settings.UPLOADS_DIR):
        shutil.rmtree(settings.UPLOADS_DIR)


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
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
def authorized_client(client: TestClient):
    """
    Fixture to create a new user via API, log in, and return an authorized client.
    This is preferred over creating a user directly in the DB.
    Also returns the user's data and password for further use in tests.
    """
    username = "test_" + random_lower_string()
    password = "testpassword123"

    # 1. Register user
    reg_response = client.post(
        "/api/v1/users/register",
        json={"username": username, "password": password},
    )
    assert reg_response.status_code == 200
    user_data = reg_response.json()

    # 2. Log in
    login_data = {"username": username, "password": password}
    login_response = client.post("/api/v1/users/login/access-token", data=login_data)
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # 3. Set authorization header and yield client
    client.headers = {"Authorization": f"Bearer {token}"}

    yield {"client": client, "user_data": user_data, "password": password}

    # Teardown: clean up the created avatar
    avatar_path = user_data["avatar_url"].lstrip("/")
    if os.path.exists(avatar_path):
        os.remove(avatar_path)
