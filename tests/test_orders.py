# tests/test_orders.py
from app.services import user_service  

# ── Helper: build order payload from a product fixture ───────────────
def make_order_payload(product, quantity=1):
    return {
        "items": [
            {"product_id": str(product.id), "quantity": quantity}
        ]
    }


# ── Block 1: Create Order — Success ──────────────────────────────────
async def test_create_order_success(authorized_client, create_test_product):
    payload = make_order_payload(create_test_product, quantity=2)
    response = await authorized_client.post("/orders/", json=payload)
    print("test_create_order_success response: ", response.json())
    assert response.status_code == 201
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 2

# ── Block 2: Unauthenticated Cannot Create ────────────────────────────
async def test_create_order_unauthenticated(client, create_test_product):
    payload = make_order_payload(create_test_product)
    response = await client.post("/orders/", json=payload)
    print("test_create_order_unauthenticated response: ", response.json())
    assert response.status_code == 401


# ── Block 3: THE BUSINESS LOGIC TEST — Price Snapshot ────────────────
async def test_unit_price_snapshot(
    authorized_client, client, admin_token, create_test_product
):
    original_price = create_test_product.price
    quantity = 1                                        # ← single source of truth
    payload = make_order_payload(create_test_product, quantity=quantity)
    create_resp = await authorized_client.post("/orders/", json=payload)
    assert create_resp.status_code == 201
    order_id = create_resp.json()["id"]
    await client.patch(
        f"/products/{create_test_product.id}",
        json={"price": 999.99},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    order_resp = await authorized_client.get(f"/orders/{order_id}")
    assert order_resp.status_code == 200
    assert order_resp.json()["items"][0]["unit_price"] == original_price
    assert order_resp.json()["items"][0]["subtotal"] == original_price * quantity  # ← uses variable


# ── Block 4: User Isolation ───────────────────────────────────────────
async def test_order_isolation(authorized_client, client, create_test_user, create_test_product , db_session):
    # User A (authorized_client = create_test_user) creates an order
    payload = make_order_payload(create_test_product)
    await authorized_client.post("/orders/", json=payload)

    # Register User B independently
    second_data = {"email": "second@example.com", "username": "seconduser", "password": "Second@123"}
    await client.post("/users/", json=second_data)
    login_resp = await client.post("/auth/login", data={"username": "second@example.com", "password": "Second@123"})
    second_token = login_resp.json()["access_token"]
    second_id = await user_service.get_user_by_email(db_session, "second@example.com")
    second_id = second_id.id

    # User B fetches their own orders — should be empty
    orders_resp = await client.get(
        f"/orders/user/{second_id}",
        headers={"Authorization": f"Bearer {second_token}"},
    )
    assert orders_resp.status_code == 200
    assert orders_resp.json() == []


# ── Block 5: Update Status — Forbidden for Customer ──────────────────
async def test_update_order_status_forbidden(authorized_client, create_test_product):
    order = await authorized_client.post("/orders/", json=make_order_payload(create_test_product))
    order_id = order.json()["id"]

    response = await authorized_client.patch(
        f"/orders/{order_id}/status",
        json={"status": "confirmed"},
    )
    assert response.status_code == 403


# ── Block 6: Update Status — Admin Succeeds ───────────────────────────
async def test_update_order_status_as_admin(authorized_client, client, admin_token, create_test_product):
    order = await authorized_client.post("/orders/", json=make_order_payload(create_test_product))
    order_id = order.json()["id"]

    response = await client.patch(
        f"/orders/{order_id}/status",
        json={"status": "confirmed"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"
