# Test Suite — Technical Documentation

> 27 async integration tests across 5 files.  
> Stack: `pytest-asyncio` · `httpx` · `SQLAlchemy async` · `asyncpg` · `PostgreSQL`

---

## Quick Start

```bash
# 1. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 2. Start the isolated test database container
docker compose up -d db_test

# 3. Run the full suite
pytest -v --disable-warnings

# 4. Run a specific file
pytest tests/test_products.py -v -s --disable-warnings
```

---

## Why an Isolated Test Database?

Tests run against a **separate PostgreSQL instance** (port `5433`) — not the development DB (port `5432`). This prevents:

- Test data polluting your dev database
- Port conflicts between environments
- Accidental writes to production-like state

The test DB is configured entirely via `pytest.ini` using `pytest-env`, which injects environment variables **before** pytest collects any tests:

```ini
[pytest]
asyncio_mode = auto
filterwarnings =
    ignore::pytest.PytestUnraisableExceptionWarning
env =
    DATABASE_PORT=5433
    DATABASE_NAME=shopping_db_test
    POSTGRES_DB=shopping_db_test
    SECRET_KEY=TEST_SECRET_KEY_FOR_SNAPSHOTS
    DATABASE_HOSTNAME=localhost
```

`get_settings()` is decorated with `@lru_cache`, so it reads these injected vars exactly once at startup — the rest of the app sees test config transparently.

---

## The Windows Event Loop Fix

**Root cause**: Python 3.8+ defaults to `ProactorEventLoop` on Windows. `asyncpg` is built for `SelectorEventLoop`. The mismatch causes:

```
RuntimeError: Task got Future attached to a different loop
```

**Fix** (top of `conftest.py`):

```python
import sys, asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
```

This is a no-op on Linux/macOS where `SelectorEventLoop` is already the default. The guard keeps `conftest.py` cross-platform.

---

## Why `NullPool` on the Engine?

```python
create_async_engine(TEST_URL, echo=False, poolclass=NullPool)
```

SQLAlchemy's default connection pool caches open connections. In an async test environment, a cached connection from Test A's event loop context can be handed to Test B — causing "wrong loop" errors.

`NullPool` disables caching entirely. Every request opens a fresh connection and closes it immediately after use. This is acceptable in tests (dozens of requests) but would be wasteful in production (millions of requests).

---

## Why `AsyncClient` (not `TestClient`)?

`TestClient` (Starlette's sync client) internally runs its own event loop. `asyncpg` also needs an event loop. **Two loops in the same process fight each other** → crashes.

`httpx.AsyncClient` with `ASGITransport` shares the **same** `pytest-asyncio` event loop — no conflict.

```python
async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
    yield ac
```

---

## Fixture Architecture

### Dependency Graph

```
engine  (session scope)
└── db_session  (function scope)  ← sets app.dependency_overrides[get_db]
    ├── client                    ← plain AsyncClient, no auth headers
    │   ├── create_test_user      ← POST /users/, returns SimpleNamespace
    │   │   └── token             ← create_access_token(user_id, email)
    │   │       ├── authorized_client   ← customer token in headers
    │   │       └── (used by admin_token)
    │   └── admin_token           ← separate admin user, returns JWT string
    │       └── create_test_product   ← POST /products/ with admin_token per-request
```

### Fixture Reference

| Fixture | Scope | Description |
|---|---|---|
| `engine` | **session** | Drops + recreates all tables once per test run. Disposes at end. |
| `db_session` | function | Opens a fresh `AsyncSession`. Sets and clears `app.dependency_overrides`. |
| `client` | function | Bare `AsyncClient`. No auth. |
| `create_test_user` | function | Creates `testuser@example.com` via API. Returns `SimpleNamespace` with `.password` attached. |
| `token` | function | JWT for `create_test_user`. Sync call — **never `await` it**. |
| `authorized_client` | function | `client` with `Authorization: Bearer <token>` header (customer role). |
| `admin_token` | function | Creates `admin_fixture@test.com`, promotes to admin in DB, returns JWT string. |
| `create_test_product` | function | POSTs to `/products/` using `admin_token` as a per-request header. |

### Why `scope="session"` on `engine` but `scope="function"` on `db_session`?

- **Schema creation** (`drop_all` + `create_all`) is expensive → do it **once per session**
- **Sessions** are cheap → create fresh **per test** for clean transaction state
- Each test starts with an empty database. Data from Test A never bleeds into Test B.

### Why `SimpleNamespace` for `create_test_user`?

Pydantic v2's `UserResponse` model uses `__setattr__` to block undeclared fields. Attaching `.password` (plain-text, needed by login tests) would raise `ValueError`.

`SimpleNamespace` is a plain Python object with no restrictions:

```python
result = SimpleNamespace(**response.json())
result.password = user_data["password"]   # works — no Pydantic guards
```

---

## The `admin_token` Design — Why a Separate User?

**The problem**: if `admin_token` promoted `create_test_user` to admin, then `authorized_client` (same person, same JWT) would also pass admin role checks — tests expecting `403` would silently return `200`.

**Why**: `require_role(admin)` queries the **DB**, not the token. Tokens carry only `user_id`. Role is looked up fresh on every request. Promoting the shared user makes both clients "admin" simultaneously.

**The fix**: `admin_token` creates a completely separate user (`admin_fixture@test.com`). `create_test_user` (`testuser@example.com`) is **never promoted** — it stays `customer` forever.

**Admin operation pattern** (per-request headers, never mutating client-level headers):

```python
response = await client.patch(
    f"/products/{product_id}",
    json={"price": 19.99},
    headers={"Authorization": f"Bearer {admin_token}"},  # per-request
)
```

This avoids fixture header mutation races where two fixtures fight over the same `client.headers` dict.

---

## How `get_db` Override Works

FastAPI resolves dependencies at request time. The app's production `get_db` opens a session to the production DB. To redirect all requests to the test DB session:

```python
# In db_session fixture:
async def override_get_db():
    yield session   # the test session

app.dependency_overrides[get_db] = override_get_db
# ↑ swaps the function reference entirely
# FastAPI now calls override_get_db() instead of get_db() for every request

# Teardown:
app.dependency_overrides.clear()
```

Changing the DB URL alone would not work — FastAPI has already resolved `get_db` as a reference and would call the original function regardless.

---

## Test Files — What Each Proves

### `test_health.py` (2 tests)
Verifies basic routing and DB connectivity. Serves as a sanity check that the plumbing works before any business logic runs.

### `test_auth.py` (3 tests)
- Login with valid credentials → `200` + access token
- Login with wrong password → `401`
- Login with non-existent email → `401`

> Login uses `application/x-www-form-urlencoded` (OAuth2 standard), not JSON.  
> Use `data={}` not `json={}` in the client call.

### `test_users.py` (7 tests)
Covers user creation, duplicate detection, authenticated GET, and RBAC:
- Customer → `GET /users/` → `403`
- Customer → `DELETE /users/{id}` → `403`
- Admin → `GET /users/` → `200`
- Admin → `DELETE /users/{id}` → `200` (soft delete, `is_active=False`)

### `test_products.py` (9 tests)
- `GET /products/` is fully public (no token required)
- `POST /products/` requires `seller` **or** `admin` role
- `PATCH /products/{id}` requires `seller` or `admin`
- `DELETE /products/{id}` → soft delete → subsequent `GET` returns `410 Gone` (not `404`)

### `test_orders.py` (6 tests)

The most business-logic-heavy file:

| Test | What it proves |
|---|---|
| `test_create_order_success` | POST /orders/ creates with correct items |
| `test_create_order_unauthenticated` | No token → 401 |
| `test_unit_price_snapshot` | `unit_price` is a stored copy, not a live reference |
| `test_order_isolation` | User B's order list is empty despite User A having orders |
| `test_update_order_status_forbidden` | Customer cannot change order status → 403 |
| `test_update_order_status_as_admin` | Admin can set status to `confirmed` → 200 |

#### The Price Snapshot Test — Why It Matters

`OrderItem.unit_price` is written once at order creation and never recomputed. This preserves historical receipts even if an admin later changes the product's price.

The test proves this by:
1. Creating an order at price `9.99`
2. Patching the product price to `999.99`
3. Re-fetching the order from DB
4. Asserting `unit_price == 9.99` (unchanged)

Re-fetching from the DB is essential — checking only the creation response would be meaningless because it predates the price change entirely.

---

## HTTP Status Code Reference

| Code | Meaning in This API |
|---|---|
| `200` | Success (GET, PATCH, DELETE soft-delete) |
| `201` | Resource created (POST) |
| `401` | No token or invalid/expired token |
| `403` | Valid token, but role not permitted |
| `404` | Resource does not exist |
| `409` | Conflict (e.g. duplicate email) |
| `410` | Resource existed but was soft-deleted (`is_active=False`) |
| `422` | Pydantic validation failed (e.g. `price=0` violates `gt=0`) |
