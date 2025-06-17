import os
from fastapi.testclient import TestClient
import random
import string

import pytest


def random_lower_string() -> str:
    return "".join(random.choices(string.ascii_lowercase, k=10))


def test_create_user_and_get_avatar(client: TestClient) -> None:
    """
    Test user registration and that the default avatar is immediately available.
    """
    username = random_lower_string()
    password = "password123"
    data = {"username": username, "password": password}

    # 1. Register user
    response = client.post("/api/v1/register", json=data)
    assert response.status_code == 200
    created_user = response.json()
    assert created_user["username"] == username
    assert "id" in created_user
    assert "avatar_url" in created_user

    avatar_url = created_user["avatar_url"]
    assert avatar_url is not None

    # 2. Check that the avatar file exists on the filesystem
    avatar_path = avatar_url.lstrip("/")
    assert os.path.exists(avatar_path)

    # 3. Check that the avatar is available via HTTP GET
    avatar_response = client.get(avatar_url)
    assert avatar_response.status_code == 200
    assert avatar_response.headers["content-type"] == "image/png"

    # Clean up the created avatar
    os.remove(avatar_path)


def test_create_user_existing_username(client: TestClient, test_user) -> None:
    """
    Test that creating a user with an existing username fails.
    """
    data = {"username": test_user["user"].username, "password": test_user["password"]}
    response = client.post("/api/v1/register", json=data)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


@pytest.mark.parametrize(
    "username, password, error_detail",
    [
        ("", "password123", "username"),  # Empty username
        ("testuser", "", "password"),  # Empty password
        (None, "password123", "username"),  # Missing username
        ("testuser", None, "password"),  # Missing password
    ],
)
def test_create_user_invalid_input(
    client: TestClient, username, password, error_detail
):
    """
    Test user creation with invalid data (empty or missing fields).
    FastAPI/Pydantic should return a 422 Unprocessable Entity error.
    """
    data = {}
    if username is not None:
        data["username"] = username
    if password is not None:
        data["password"] = password

    response = client.post("/api/v1/register", json=data)
    assert response.status_code == 422
    # Check that the error message points to the correct field
    assert error_detail in response.text


def test_login_access_token(client: TestClient, test_user) -> None:
    """
    Test user login and token generation.
    """
    login_data = {
        "username": test_user["user"].username,
        "password": test_user["password"],
    }
    response = client.post("/api/v1/login/access-token", data=login_data)
    assert response.status_code == 200
    token = response.json()
    assert "access_token" in token
    assert token["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient, test_user) -> None:
    """
    Test that login fails with an incorrect password.
    """
    login_data = {"username": test_user["user"].username, "password": "wrongpassword"}
    response = client.post("/api/v1/login/access-token", data=login_data)
    assert response.status_code == 401
    assert "Неверное имя пользователя или пароль" in response.json()["detail"]


def test_check_username_exists(client: TestClient, test_user) -> None:
    """
    Test that the username check endpoint correctly identifies an existing user.
    """
    response = client.get(
        f"/api/v1/users/check-username?username={test_user['user'].username}"
    )
    assert response.status_code == 200
    assert response.json() == {"exists": True}


def test_check_username_not_exists(client: TestClient) -> None:
    """
    Test that the username check endpoint correctly identifies a non-existing user.
    """
    username = random_lower_string()
    response = client.get(f"/api/v1/users/check-username?username={username}")
    assert response.status_code == 200
    assert response.json() == {"exists": False}


def test_read_current_user(authorized_client: TestClient, test_user) -> None:
    """
    Test that the /api/v1/users/me endpoint returns the current user.
    """
    response = authorized_client.get("/api/v1/users/me")
    assert response.status_code == 200
    current_user = response.json()
    assert current_user["username"] == test_user["user"].username
    assert "id" in current_user
