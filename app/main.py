from fastapi import FastAPI
from app.core.config import get_settings
from app.routers import users , products , orders , auth
settings = get_settings()

# ---- The App Object ----
# FastAPI() creates an ASGI application instance.
#
# WHAT IS ASGI?
# ASGI = Asynchronous Server Gateway Interface.
# It's the PROTOCOL between the web server (uvicorn) and your app.
# The flow: Internet → uvicorn (HTTP parsing) → ASGI protocol → FastAPI → your code
#
# When uvicorn receives bytes off the wire, it:
# 1. Parses raw HTTP into a "scope" dict (method, path, headers, etc.)
# 2. Calls: await app(scope, receive, send)
# 3. FastAPI's router matches scope["path"] to your @app.get("/") decorator
# 4. Your handler runs, returns data
# 5. FastAPI serializes it to JSON, calls send() back to uvicorn
# 6. Uvicorn writes bytes back to the socket

app = FastAPI(
    title=settings.app_name,
    description="A professional shopping API — built to learn, engineered to scale.",
    version="0.1.0",
    docs_url="/docs",       # Swagger UI lives here
    redoc_url="/redoc",     # ReDoc alternative docs
)

app.include_router(users.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(auth.router)


# ---- Health Check Endpoint ----
# This is the FIRST endpoint you should always create.
# Load balancers, Kubernetes, Docker healthchecks — they all need this.
@app.get("/health", tags=["System"])
async def health_check():
    """
    Returns 200 OK if the service is alive.

    YOUR TASK: Later, extend this to also check:
    - Database connectivity (can we SELECT 1?)
    - Redis connectivity (if you add caching)
    - Disk space / memory usage
    """
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": "0.1.0",
    }


# ---- Root Endpoint ----
@app.get("/", tags=["System"])
async def root():
    return {
        "message": f"Welcome to {settings.app_name}",
        "docs": "/docs",
        "health": "/health",
    }


# ============================================================
# YOUR NEXT STEPS (in order):
# ============================================================
# 1. Run: docker-compose up --build
#    → Verify you can hit http://localhost:8000/docs
#
# 2. Create app/models/product.py
#    → Define a Product SQLAlchemy model (id, name, price, stock)
#
# 3. Create app/schemas/product.py
#    → Define Pydantic schemas for request/response validation
#
# 4. Create app/routers/products.py
#    → Wire up CRUD endpoints: GET, POST, PUT, DELETE
#
# 5. Create app/services/product_service.py
#    → Move business logic OUT of routers (keep routers thin)
# ============================================================
