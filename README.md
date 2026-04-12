# FastAPI-102: Production-Ready Shopping API 🚀🛍️

Welcome to **FastAPI-102**. This repository is an intermediate-level project designed to bridge the gap between simple CRUD prototypes and production-grade Cloud applications. 

> [!IMPORTANT]
> **DEMO MODE NOTICE**: This is a learning repository. Unlike a standard production repo, we have **INTENTIONALLY INCLUDED THE `.env` FILE** to provide a "Plug and Play" experience. No configuration is required to get started!

---

## 🛠️ Key Technical Concepts (FastAPI-102 Level)

This project skips the basics to focus on advanced patterns required for real-world reliability and security.

### 🛡️ 1. The RBAC "Bouncer Factory"
We implemented an **Immutable Role-Based Access Control (RBAC)** system using a dependency factory pattern. 
- **Pattern**: `Depends(require_role(UserRole.admin))`
- **Internal**: This uses a nested function closure to encapsulate role logic, making our authorization layer impossible to manipulate from client-side requests.

### 🛒 2. Price Snapshotting (Data Integrity)
In e-commerce, linking an Order to a Product is not enough. We implemented **Historical Integrity**:
- The API snapshots the product price into the `unit_price` column of the `OrderItem` at the moment of sale.
- This ensures that future catalog changes never alter the financial history of past orders.

### 🧱 3. The SQL LEGO System
Standard connection strings are brittle. We use a **Centralized URL Builder** in `app/core/database.py`:
- It treats DB credentials as individual "LEGO bricks" (`HOST`, `PORT`, `USER`, `PASS`).
- It uses `sqlalchemy.engine.URL.create()` to safely assemble the final string, preventing the common "Invalid Interpolation Syntax" errors caused by special characters like `@` or `%`.

### 🐳 4. The Production Infrastructure Deck
The `Dockerfile.prod` and `entrypoint.sh` are configured for **Azure App Service**:
- **Port 2222 Persistence**: Pre-configured SSH maintenance tunnel with the "Docker!" handshake.
- **Process Orchestration**: Uses **Gunicorn with Uvicorn Workers** for multi-process concurrency, ensuring the API stays responsive under load.
- **PID 1 Signal Handling**: Uses `exec` to ensure the container responds properly to Docker stop/restart commands.

---

## 🚀 Quick Start (Plug & Play)

Since the `.env` is already provided, you can launch the entire stack with one command:

```bash
# Launch the API and PostgreSQL Database
docker compose up --build
```

### 🔐 Initial Setup
1. **Seed the Admin**: Once the containers are running, run the following to create your master admin account:
   ```bash
   docker exec -it shopping-api python seed_admin.py
   ```
2. **Access the Docs**: Open [http://localhost:8000/docs](http://localhost:8000/docs) to start exploring the protected endpoints!

---

## 📂 Learning More
I've placed supplementary **README.md** files in key directories to explain folder-specific intermediate patterns:
- [**The Technical Deep-Dive**](./README_technical.md) - **The "Mechanical Handshakes" (OAuth, Pydantic, SQL).**
- [`/alembic`](./alembic/README.md) - The PostgreSQL Enum Fix.
- [`/app/core`](./app/core/README.md) - Security & Managed Configuration.
- [`/app/services`](./app/services/README.md) - Service Layer Philosophy.

---

## 📜 Projects & Timeline
This project was evolved through a series of technical hurdles including Azure SSH configuration, async-driver URL escaping, and RBAC implementation. It serves as a comprehensive snapshot of intermediate FastAPI development.
