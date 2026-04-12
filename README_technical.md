# Technical Deep-Dive: The Mechanical Handshakes 🔍🏗️

This document explains the technical "Plumbing" of the **FastAPI-102** project—the precise connection points where different technologies handshake to create a secure, scalable system.

---

## 🔐 1. The Security Pipeline (OAuth2 & JWT)

Authentication in this project isn't just a login button; it's a multi-stage security pipeline.

1. **The Request**: The client sends credentials to `/auth/login`. 
   - **Handshake**: We use `OAuth2PasswordRequestForm`. This is a standard FastAPI dependency that mandates `application/x-www-form-urlencoded` (Form Data). 
2. **The Verification**: `user_service` uses **Argon2** (via `passlib`) to verify the password against the `hashed_password` in the DB.
3. **The Wristband (JWT)**: `security.create_access_token` generates a signed JWT.
   - **The Payload**: Includes the user's UUID as the `sub` (Subject) claim. This is the global standard for identity tokens.
4. **The Access**: In subsequent requests, the client sends `Authorization: Bearer <token>`.
   - **The Bouncer**: `deps.get_current_user` decodes the token, extracts the `sub`, and performs a database lookup to ensure the user is still active.

---

## 🌉 2. The Data Bridge (Pydantic <-> SQLAlchemy)

The most common hurdle in FastAPI is moving data between "Data Models" (DB) and "Schemas" (API).

### The Contractual Filter
We use **Pydantic Schemas** (`app/schemas/`) as the single source of truth for our API contract. 
- **Validation**: Incoming data is validated by Pydantic (e.g., `EmailStr`, `min_length`) before it ever reaches a Service.
- **Filtering**: Outgoing data (e.g., `UserResponse`) automatically strips sensitive fields like `hashed_password`.

### `from_attributes=True`
SQLAlchemy objects (`models/*.py`) are class instances with properties (e.g., `user.id`). Pydantic usually expects dictionaries (`user["id"]`).
- **Connecting Block**: By setting `model_config = ConfigDict(from_attributes=True)`, we tell Pydantic: *"It's okay to read attributes from a class object."* This allows us to return SQLAlchemy model instances directly from our services.

---

## 🏗️ 3. The Migration Handshake (Models <-> Alembic)

How does Alembic know what your database should look like?

1. **Metadata Centrally Hosted**: All models inherit from `Base` in `app/core/database.py`.
2. **The Discovery Link**: In `alembic/env.py`, we import our models:
   ```python
   from app.core.database import Base
   from app.models.user import User  # Must be imported to be "seen"
   target_metadata = Base.metadata
   ```
3. **PostgreSQL Enums**: We handle the technical disparity between Python Enums and PostgreSQL Enum Types by manually injecting `sa.Enum(...).create(op.get_bind())` into migration scripts.

---

## 🐳 4. The Production Orchestrator (Docker <-> FastAPI)

The connection between your local code and the cloud is managed by the Docker stack.

- **Injection**: Docker (via `docker-compose`) injects `.env` variables into the OS environment.
- **Verification**: `app/core/config.py` (using Pydantic `BaseSettings`) reads these OS variables, validates their types (e.g., ensuring `PORT` is an `int`), and provides them to the app.
- **PID 1 Signal**: We use `exec gunicorn` in `entrypoint.sh`. This replaces the shell process with the application process, ensuring that when Docker sends a "STOP" signal, it reaches FastAPI directly.
- **The Foreman Workers**: Gunicorn acts as the "Foreman," managing multiple **Uvicorn Workers** to handle concurrent async requests efficiently.
