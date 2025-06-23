from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import os
import pytest
from jose import jwt
from PIL import Image
from io import BytesIO

from core.config import settings
from tests.utils import random_lower_string
from features.users.crud import user as crud_user


# --- Registration and Login Tests ---


def test_create_user_success(client: TestClient):
    username = f"testuser_{random_lower_string()}"
    password = "testpassword123"
    response = client.post(
        "/api/v1/users/register", json={"username": username, "password": password}
    )
    assert response.status_code == 200, response.text
    created_user = response.json()
    assert created_user["username"] == username
    assert created_user["is_default_avatar"] is True
    assert "id" in created_user
    avatar_path = created_user["avatar_url"].lstrip("/")
    assert os.path.exists(avatar_path)
    os.remove(avatar_path)


def test_create_user_existing_username(client: TestClient, authorized_client):
    user_data = authorized_client["user_data"]
    password = authorized_client["password"]
    data = {"username": user_data["username"], "password": password}
    response = client.post("/api/v1/users/register", json=data)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


@pytest.mark.parametrize(
    "username, password",
    [
        ("", "password123"),
        ("user", ""),
        ("a" * 21, "password123"),
        ("a" * 2, "password123"),
        ("user-name", "password123"),
        ("user", "short"),
    ],
)
def test_create_user_invalid_input(client: TestClient, username, password):
    response = client.post(
        "/api/v1/users/register", json={"username": username, "password": password}
    )
    assert response.status_code == 422


def test_login_access_token(client: TestClient):
    username = f"login_{random_lower_string()}"
    password = "testpassword123"
    reg_response = client.post(
        "/api/v1/users/register", json={"username": username, "password": password}
    )
    assert reg_response.status_code == 200, reg_response.text
    user_data = reg_response.json()
    response = client.post(
        "/api/v1/users/login/access-token",
        data={"username": username, "password": password},
    )
    assert response.status_code == 200, response.text
    token_data = response.json()
    assert "access_token" in token_data
    decoded_token = jwt.decode(
        token_data["access_token"], settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )
    assert decoded_token["sub"] == str(user_data["id"])
    os.remove(user_data["avatar_url"].lstrip("/"))


def test_login_wrong_password(client: TestClient):
    username = f"login_fail_{random_lower_string(k=8)}"
    password = "testpassword123"
    reg_response = client.post(
        "/api/v1/users/register", json={"username": username, "password": password}
    )
    assert reg_response.status_code == 200, reg_response.text
    user_data = reg_response.json()
    response = client.post(
        "/api/v1/users/login/access-token",
        data={"username": username, "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert "Неверное имя пользователя или пароль" in response.json()["detail"]
    os.remove(user_data["avatar_url"].lstrip("/"))


# --- User "Me" Endpoint Tests ---


def test_read_current_user(authorized_client):
    client = authorized_client["client"]
    user_data = authorized_client["user_data"]
    response = client.get("/api/v1/users/me")
    assert response.status_code == 200, response.text
    current_user = response.json()
    assert current_user["username"] == user_data["username"]
    assert "id" in current_user


def test_check_username_exists(client: TestClient, authorized_client):
    user_data = authorized_client["user_data"]
    response = client.get(
        f"/api/v1/users/check-username?username={user_data['username']}"
    )
    assert response.status_code == 200
    assert response.json() == {"exists": True}


def test_check_username_not_exists(client: TestClient):
    username = random_lower_string()
    response = client.get(f"/api/v1/users/check-username?username={username}")
    assert response.status_code == 200
    assert response.json() == {"exists": False}


# --- Username Change Tests ---


def test_update_username_success(authorized_client):
    client = authorized_client["client"]
    new_username = random_lower_string()
    response = client.put("/api/v1/users/me/username", json={"username": new_username})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == new_username


def test_update_username_regenerates_default_avatar(authorized_client):
    client = authorized_client["client"]
    user_data = authorized_client["user_data"]
    old_avatar_path = user_data["avatar_url"]
    new_username = random_lower_string()
    response = client.put("/api/v1/users/me/username", json={"username": new_username})
    assert response.status_code == 200
    updated_user = response.json()
    assert updated_user["avatar_url"] != old_avatar_path
    assert os.path.exists(updated_user["avatar_url"].lstrip("/"))
    assert not os.path.exists(old_avatar_path.lstrip("/"))
    os.remove(updated_user["avatar_url"].lstrip("/"))


def test_update_username_preserves_custom_avatar(authorized_client):
    client = authorized_client["client"]
    img = Image.new("RGB", (100, 100), color="blue")
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format="JPEG")
    img_byte_arr.seek(0)
    files = {"file": ("custom.jpg", img_byte_arr, "image/jpeg")}
    upload_response = client.put("/api/v1/users/me/avatar", files=files)
    custom_avatar_url = upload_response.json()["avatar_url"]
    new_username = random_lower_string()
    update_response = client.put(
        "/api/v1/users/me/username", json={"username": new_username}
    )
    assert update_response.status_code == 200
    assert update_response.json()["avatar_url"] == custom_avatar_url
    os.remove(custom_avatar_url.lstrip("/"))


def test_update_username_to_taken_name(client: TestClient, authorized_client):
    auth_client = authorized_client["client"]
    other_username = f"otheruser_{random_lower_string()}"
    reg_response = client.post(
        "/api/v1/users/register",
        json={"username": other_username, "password": "password123"},
    )
    other_avatar_path = reg_response.json()["avatar_url"]
    response = auth_client.put(
        "/api/v1/users/me/username", json={"username": other_username}
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]
    os.remove(other_avatar_path.lstrip("/"))


def test_update_username_invalid_format(authorized_client):
    client = authorized_client["client"]
    invalid_usernames = ["a", "u with space", "u@s", "a" * 21]
    for username in invalid_usernames:
        response = client.put("/api/v1/users/me/username", json={"username": username})
        assert response.status_code == 422


# --- Password Change Tests ---


def test_update_password_success(authorized_client):
    client = authorized_client["client"]
    password = authorized_client["password"]
    new_password = "newValidPassword1"
    response = client.put(
        "/api/v1/users/me/password",
        json={"old_password": password, "new_password": new_password},
    )
    assert response.status_code == 204


def test_update_password_incorrect_old_password(authorized_client):
    client = authorized_client["client"]
    response = client.put(
        "/api/v1/users/me/password",
        json={"old_password": "wrongpassword", "new_password": "newValidPassword1"},
    )
    assert response.status_code == 400
    assert "Incorrect old password" in response.json()["detail"]


@pytest.mark.parametrize(
    "new_password, expected_status, expected_detail",
    [
        ("short", 422, "8 and 20 characters"),
        ("toolongpasswordtoolongpassword", 422, "8 and 20 characters"),
        ("nonumber", 422, "at least one number"),
        ("invalid-char!", 422, "alphanumeric characters"),
    ],
)
def test_update_password_invalid_new(
    authorized_client, new_password, expected_status, expected_detail
):
    client = authorized_client["client"]
    old_password = authorized_client["password"]
    response = client.put(
        "/api/v1/users/me/password",
        json={"old_password": old_password, "new_password": new_password},
    )
    assert response.status_code == expected_status
    assert expected_detail in response.json()["detail"]


# --- Avatar Tests ---


def test_upload_avatar_success(authorized_client):
    client = authorized_client["client"]
    img = Image.new("RGB", (100, 100), color="red")
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_byte_arr.seek(0)
    files = {"file": ("test.png", img_byte_arr, "image/png")}
    response = client.put("/api/v1/users/me/avatar", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["is_default_avatar"] is False
    avatar_path = data["avatar_url"].lstrip("/")
    assert os.path.exists(avatar_path)
    os.remove(avatar_path)


def test_upload_avatar_invalid_format(authorized_client):
    client = authorized_client["client"]
    files = {"file": ("test.txt", b"some text", "text/plain")}
    response = client.put("/api/v1/users/me/avatar", files=files)
    assert response.status_code == 400
    assert "Invalid image format" in response.json()["detail"]


def test_delete_avatar(authorized_client):
    client = authorized_client["client"]
    # First, upload a custom avatar to delete it
    img = Image.new("RGB", (100, 100), color="green")
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format="JPEG")
    img_byte_arr.seek(0)
    files = {"file": ("custom_to_delete.jpg", img_byte_arr, "image/jpeg")}
    upload_response = client.put("/api/v1/users/me/avatar", files=files)
    custom_avatar_url = upload_response.json()["avatar_url"]
    assert os.path.exists(custom_avatar_url.lstrip("/"))

    # Now, delete it
    delete_response = client.delete("/api/v1/users/me/avatar")
    assert delete_response.status_code == 200
    data = delete_response.json()
    assert data["is_default_avatar"] is True
    new_default_avatar_url = data["avatar_url"]
    assert new_default_avatar_url != custom_avatar_url
    assert not os.path.exists(custom_avatar_url.lstrip("/"))
    assert os.path.exists(new_default_avatar_url.lstrip("/"))
    os.remove(new_default_avatar_url.lstrip("/"))


def test_delete_default_avatar(authorized_client):
    client = authorized_client["client"]
    user_data = authorized_client["user_data"]
    default_avatar_url = user_data["avatar_url"]
    assert user_data["is_default_avatar"] is True

    response = client.delete("/api/v1/users/me/avatar")
    assert response.status_code == 200
    data = response.json()
    assert data["is_default_avatar"] is True
    # The URL might be the same if the username hasn't changed, but it should be a new file
    assert os.path.exists(data["avatar_url"].lstrip("/"))
    if default_avatar_url != data["avatar_url"]:
        assert not os.path.exists(default_avatar_url.lstrip("/"))
    os.remove(data["avatar_url"].lstrip("/"))


def test_register(client: TestClient):
    username = "testuser"
    password = "testpassword123"
    response = client.post(
        "/api/v1/users/register",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == username
    assert "id" in data
    # Clean up the created avatar
    avatar_path = data["avatar_url"].lstrip("/")
    if os.path.exists(avatar_path):
        os.remove(avatar_path)


def test_register_creates_default_avatar(client: TestClient):
    """
    Test that a default avatar is created on user registration.
    """
    username = "test_avatar_user"
    password = "testpassword123"
    response = client.post(
        "/api/v1/users/register",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    data = response.json()

    # Check that avatar URL is present and looks like a UUID-named file
    assert "avatar_url" in data
    assert data["avatar_url"].startswith("/uploads/avatars/")
    assert data["avatar_url"].endswith(".png")
    assert data["is_default_avatar"] is True

    # Check that the file actually exists
    avatar_path = data["avatar_url"].lstrip("/")
    assert os.path.exists(avatar_path)

    # Teardown: clean up the created avatar
    if os.path.exists(avatar_path):
        os.remove(avatar_path)


def test_get_existing_user(client: TestClient, db: Session):
    username = "test_existing_user"
