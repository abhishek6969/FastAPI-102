# tests/test_users.py





# ── Helper: promote a user to admin directly via DB ──────────────────
# We skip the API because no "make me admin" endpoint exists (by design).
# This is TEST SETUP only — not a route we're testing.



# ── Block 1: Create User ──────────────────────────────────────────────
async def test_create_user_success(client):
    payload = {
        "email": "newuser@example.com",
        "username": "newuser",
        "password": "Newpass@123",
    }
    response = await client.post("/users/", json=payload)
    assert response.status_code == 201
    assert response.json()["email"] == "newuser@example.com"
    assert "hashed_password" not in response.json()


# ── Block 2: Duplicate Email ──────────────────────────────────────────
async def test_create_user_duplicate_email(client, create_test_user):
    # create_test_user already created "testuser@example.com"
    payload = {
        "email": create_test_user.email,   # same email — should conflict
        "username": "otherusername",
        "password": "Newpass@123",
    }
    response = await client.post("/users/", json=payload)
    assert response.status_code == 409


# ── Block 3: Get User By ID (authenticated) ───────────────────────────
async def test_get_user_by_id(authorized_client, create_test_user):
    response = await authorized_client.get(f"/users/{create_test_user.id}")
    assert response.status_code == 200
    assert response.json()["id"] == str(create_test_user.id)


# ── Block 4: List Users — Regular User Gets 403 ───────────────────────
async def test_list_users_forbidden_for_customer(authorized_client):
    # authorized_client is a customer-role user (default from create_test_user)
    response = await authorized_client.get("/users/")
    assert response.status_code == 403


# ── Block 5: Delete — Regular User Gets 403 ──────────────────────────
async def test_delete_user_forbidden_for_customer(authorized_client, create_test_user):
    response = await authorized_client.delete(f"/users/{create_test_user.id}")
    assert response.status_code == 403


# ── Block 6: List Users — Admin Succeeds ─────────────────────────────
async def test_list_users_as_admin(client, admin_token):
    response = await client.get("/users/", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    data = response.json()
    print(f"Data: {data}")
    assert isinstance(data, list)
    assert len(data) >= 1


# ── Block 7: Delete User — Admin Succeeds ────────────────────────────
async def test_delete_user_as_admin(client, admin_token,create_test_user):

    response = await client.delete(f"/users/{create_test_user.id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    data = response.json()
    print(f"Data: {data}")
    assert data["detail"] == "User deactivated"
    assert data["user_id"] == str(create_test_user.id)
