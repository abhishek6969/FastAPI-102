# tests/test_products.py

PRODUCT_PAYLOAD = {
    "name": "Test Widget",
    "description": "A widget for testing",
    "price": 9.99,
    "stock": 100,
    "category": "Electronics",
}


# ── Block 1: Public Access ────────────────────────────────────────────
# client has NO auth header — proves the route truly needs no token
async def test_list_products_is_public(client):
    response = await client.get("/products/")
    print("test_list_products_is_public response : " , response.json())
    assert response.status_code == 200


# ── Block 2: Customer Cannot Create Product ───────────────────────────
async def test_create_product_forbidden_for_customer(authorized_client):
    response = await authorized_client.post("/products/", json=PRODUCT_PAYLOAD)
    print("test_create_product_forbidden_for_customer response: ", response.json())
    assert response.status_code == 403



# ── Block 3: Admin Can Create Product ─────────────────────────────────
async def test_create_product_as_admin(client, admin_token):
    response = await client.post("/products/", json=PRODUCT_PAYLOAD, headers={"Authorization": f"Bearer {admin_token}"})
    print("test_create_product_as_admin response: ", response.json())

    assert response.status_code == 201
    assert response.json()["name"] == PRODUCT_PAYLOAD["name"]
    assert response.json()["price"] == PRODUCT_PAYLOAD["price"]


# ── Block 4: Get Product By ID ────────────────────────────────────────
async def test_get_product_by_id(client, create_test_product):
    product_id = create_test_product.id
    response = await client.get(f"/products/{product_id}")
    print("test_get_product_by_id response: ", response.json())
    assert response.status_code == 200
    assert response.json()["id"] == product_id


# ── Block 5: Get Non-Existent Product ────────────────────────────────
async def test_get_product_not_found(client):
    import uuid
    fake_id = uuid.uuid4()
    response = await client.get(f"/products/{fake_id}")
    print("test_get_product_not_found response: ", response.json())
    assert response.status_code == 404

# ── Block 6: Update Product — Customer Forbidden ──────────────────────
async def test_update_product_forbidden_for_customer(authorized_client, create_test_product):
    response = await authorized_client.patch(
        f"/products/{create_test_product.id}",
        json={"price": 1.99}
    )
    print("test_update_product_forbidden_for_customer response: ", response.json())
    assert response.status_code == 403


# ── Block 7: Update Product — Admin Success ───────────────────────────
async def test_update_product_as_admin(client, admin_token, create_test_product):
    update_data = {"price": 19.99, "stock": 50}
    response = await client.patch(
        f"/products/{create_test_product.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    print("test_update_product_as_admin response: ", response.json())
    assert response.status_code == 200
    assert response.json()["price"] == 19.99
    assert response.json()["stock"] == 50
    assert response.json()["name"] == create_test_product.name  # unchanged field


# ── Block 8: Delete Product — Customer Forbidden ──────────────────────
async def test_delete_product_forbidden_for_customer(authorized_client, create_test_product):
    response = await authorized_client.delete(f"/products/{create_test_product.id}")
    print("test_delete_product_forbidden_for_customer response: ", response.json())
    assert response.status_code == 403


# ── Block 9: Delete Product — Admin Success ───────────────────────────
async def test_delete_product_as_admin(client, admin_token, create_test_product):
    # Step 1: Delete it
    del_response = await client.delete(f"/products/{create_test_product.id}", headers={"Authorization": f"Bearer {admin_token}"})
    print("test_delete_product_as_admin del_response: ", del_response.json())
    assert del_response.status_code == 200

    # Step 2: Try to GET the same product — soft delete means it's "gone" not "missing"
    get_response = await client.get(f"/products/{create_test_product.id}")
    print("test_delete_product_as_admin get_response: ", get_response.json())
    assert get_response.status_code == 410  # 410 Gone, not 404 Not Found

