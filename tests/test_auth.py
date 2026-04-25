# tests/test_auth.py
import pytest

# ── Block 1: Happy Path ──────────────────────────────────────────────
# create_test_user gives us a real user in the DB.
# We log in with their correct credentials.
async def test_login_success(client, create_test_user):
    response = await client.post(
        "/auth/login",
        data={
            "username": create_test_user.email,
            "password": create_test_user.password,   # plain-text, stored on fixture
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


# ── Block 2: Wrong Password ──────────────────────────────────────────
async def test_login_wrong_password(client, create_test_user):
    response = await client.post(
        "/auth/login",
        data={
            "username": create_test_user.email,
            "password": "WrongPassword999",          # deliberately wrong
        }
    )
    assert response.status_code == 401


# ── Block 3: Non-Existent User ───────────────────────────────────────
async def test_login_nonexistent_user(client):
    # NOTE: no create_test_user fixture — DB is empty
    response = await client.post(
        "/auth/login",
        data={
            "username": "ghost@nowhere.com",         # nobody with this email
            "password": "DoesntMatter1",
        }
    )
    assert response.status_code == 401
