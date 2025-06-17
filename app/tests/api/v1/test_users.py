import os
import shutil
from fastapi.testclient import TestClient
from PIL import Image
from io import BytesIO


# A new random string generator for usernames to avoid conflicts
def random_lower_string(length=10):
    import random
    import string

    return "".join(random.choices(string.ascii_lowercase, k=length))


def test_update_user_me_username(authorized_client: TestClient, test_user):
    """
    Test updating the current user's username.
    """
    new_username = random_lower_string()
    response = authorized_client.put(
        "/api/v1/users/me", json={"username": new_username}
    )
    assert response.status_code == 200
    updated_user = response.json()
    assert updated_user["username"] == new_username

    # Check that the default avatar was regenerated
    old_avatar_path = test_user["user"].avatar_url.lstrip("/")
    new_avatar_path = updated_user["avatar_url"].lstrip("/")

    assert old_avatar_path != new_avatar_path
    assert os.path.exists(new_avatar_path)
    # The old default avatar should be deleted by the server
    assert not os.path.exists(old_avatar_path)

    # Clean up the new avatar
    if os.path.exists(new_avatar_path):
        os.remove(new_avatar_path)


def test_update_user_me_password(client: TestClient, test_user):
    """
    Test updating the current user's password.
    """
    # Log in to get a token
    login_data = {
        "username": test_user["user"].username,
        "password": test_user["password"],
    }
    login_response = client.post("/api/v1/login/access-token", data=login_data)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Update password
    new_password = "newpassword123"
    response = client.put(
        "/api/v1/users/me", json={"password": new_password}, headers=headers
    )
    assert response.status_code == 200

    # Try to log in with the old password (should fail)
    old_login_response = client.post("/api/v1/login/access-token", data=login_data)
    assert old_login_response.status_code == 401

    # Try to log in with the new password (should succeed)
    new_login_data = {"username": test_user["user"].username, "password": new_password}
    new_login_response = client.post("/api/v1/login/access-token", data=new_login_data)
    assert new_login_response.status_code == 200
    assert "access_token" in new_login_response.json()


def test_auth_after_username_change(client: TestClient, test_user):
    """
    Test that authentication still works with the original token after a username change.
    """
    # Log in and get a token
    login_data = {
        "username": test_user["user"].username,
        "password": test_user["password"],
    }
    login_response = client.post("/api/v1/login/access-token", data=login_data)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Change the username
    new_username = random_lower_string()
    client.put("/api/v1/users/me", json={"username": new_username}, headers=headers)

    # Use the *original* token to access a protected route
    me_response = client.get("/api/v1/users/me", headers=headers)
    assert me_response.status_code == 200
    # The username in the response should be the new one
    assert me_response.json()["username"] == new_username
    # Clean up avatar
    avatar_path = me_response.json()["avatar_url"].lstrip("/")
    if os.path.exists(avatar_path):
        os.remove(avatar_path)


def test_upload_avatar(authorized_client: TestClient, test_user):
    """
    Test uploading a custom avatar.
    """
    # Create a dummy image file
    img = Image.new("RGB", (100, 100), color="red")
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_byte_arr.seek(0)

    # Note: the uploaded file is renamed to {username}.png, overwriting the default.
    # So the URL will be the same, but the content and is_default_avatar flag will change.
    files = {"file": ("test_avatar.png", img_byte_arr, "image/png")}
    response = authorized_client.put("/api/v1/users/me/avatar", files=files)

    assert response.status_code == 200
    new_avatar_url = response.json()["avatar_url"]

    # Check that the new file exists
    avatar_path = new_avatar_url.lstrip("/")
    assert os.path.exists(avatar_path)

    # Check that it's now marked as a custom avatar
    me_response = authorized_client.get("/api/v1/users/me")
    assert me_response.json()["is_default_avatar"] is False

    # Clean up
    if os.path.exists(avatar_path):
        os.remove(avatar_path)


def test_username_change_with_custom_avatar(authorized_client: TestClient, test_user):
    """
    Test that changing username does NOT affect a custom avatar.
    """
    # 1. Upload a custom avatar first
    img = Image.new("RGB", (100, 100), color="blue")
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format="JPEG")
    img_byte_arr.seek(0)
    files = {"file": ("custom.jpg", img_byte_arr, "image/jpeg")}
    upload_response = authorized_client.put("/api/v1/users/me/avatar", files=files)
    assert upload_response.status_code == 200
    custom_avatar_url_before_change = upload_response.json()["avatar_url"]

    # 2. Change username
    new_username = random_lower_string()
    update_response = authorized_client.put(
        "/api/v1/users/me", json={"username": new_username}
    )
    assert update_response.status_code == 200

    # 3. Check that the avatar URL did NOT change
    updated_user = update_response.json()
    assert updated_user["avatar_url"] == custom_avatar_url_before_change

    # The file should still exist at its original path
    final_avatar_path = updated_user["avatar_url"].lstrip("/")
    assert os.path.exists(final_avatar_path)

    # Clean up
    if os.path.exists(final_avatar_path):
        os.remove(final_avatar_path)


def test_update_username_to_taken_name(
    authorized_client: TestClient, client: TestClient, test_user
):
    """Test updating username to one that is already taken by another user."""
    # Create another user
    other_username = random_lower_string()
    other_password = "password123"
    client.post(
        "/api/v1/register",
        json={"username": other_username, "password": other_password},
    )

    # Try to update the first user's name to the second user's name
    response = authorized_client.put(
        "/api/v1/users/me", json={"username": other_username}
    )
    assert response.status_code == 400
    assert "Username already exists" in response.json()["detail"]


def test_update_username_to_same_name(authorized_client: TestClient, test_user):
    """Test 'updating' username to the same name, should not trigger changes."""
    current_username = test_user["user"].username
    current_avatar_url = test_user["user"].avatar_url

    response = authorized_client.put(
        "/api/v1/users/me", json={"username": current_username}
    )
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["username"] == current_username
    # Check that avatar was NOT regenerated
    assert user_data["avatar_url"] == current_avatar_url


def test_update_username_invalid_format(authorized_client: TestClient):
    """Test updating username to a name with an invalid format."""
    invalid_usernames = ["a", "user with space", "user@special", "a" * 21]
    for username in invalid_usernames:
        response = authorized_client.put(
            "/api/v1/users/me", json={"username": username}
        )
        assert response.status_code == 422
