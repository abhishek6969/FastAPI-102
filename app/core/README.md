# Core Internals: Security & Configuration 🛡️⚙️

This directory contains the "Nerve Center" of the application. In **FastAPI-102**, we've transitioned from hardcoded defaults to a production-hardened, environment-driven architecture.

## 🧱 The SQL "LEGO" System (`database.py` & `config.py`)
Standard database connection strings (e.g., `postgresql://...`) can fail if your password contains special characters like `@` or `%`. 

We implemented a **LEGO-style builder**:
1. We store `POSTGRES_USER`, `POSTGRES_PASSWORD`, etc., as individual "bricks" in `.env`.
2. `database.py` uses `sqlalchemy.engine.URL.create()` to safely assemble these bricks.
3. This ensures that the URL is properly escaped, preventing any "Invalid Interpolation" errors.

## 🔐 Intermediate Security (`security.py`)
- **Argon2 Hashing**: We've upgraded from standard bcrypt to **Argon2** (via `passlib`), providing better resistance against GPU-based brute-force attacks.
- **JWT Claims**: Tokens include a `sub` (Subject) claim containing the user's UUID.
- **The Wristband Analogy**: Think of the JWT as a signed wristband. The server verified your ID once, gave you the wristband, and now every other part of the app just checks the wristband's signature and expiration.

## 🛡️ The Dependency Handshake (`deps.py`)
We use FastAPI's `Depends()` system to create a "Security Handshake":
1. **`get_current_user`**: Decodes the wristband and verifies the user is still active in the DB.
2. **`require_role`**: A **Factory Pattern** that creates a bouncer for specific roles (e.g., `Depends(require_role(UserRole.admin))`). This is immutable and impossible to bypass from the client side.
