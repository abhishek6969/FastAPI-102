# ---- Stage 1: Base Image ----
# python:3.12-slim is a Debian-based image with only the minimal packages.
# "slim" means ~45MB instead of ~350MB for the full image.
# Under the hood: This pulls a pre-built filesystem layer from Docker Hub.
FROM python:3.12-slim

# ---- Stage 2: Set Working Directory ----
# WORKDIR changes the "current directory" inside the container's filesystem.
# If /app doesn't exist, Docker creates it. All subsequent commands run from here.
WORKDIR /app

# ---- Stage 3: Install Dependencies First (Layer Caching) ----
# WHY copy requirements.txt BEFORE copying the rest of the code?
# Docker caches each layer. If your code changes but requirements.txt doesn't,
# Docker reuses the cached "pip install" layer — saving minutes on rebuilds.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
# --no-cache-dir: Tells pip NOT to store downloaded .whl files.
#   Inside a container, caching wastes space — the container IS the cache.

# ---- Stage 4: Copy Application Code ----
# This layer changes every time you edit code, but the pip layer above is cached.
COPY . .

# ---- Stage 5: Expose Port ----
# EXPOSE is documentation — it tells humans and orchestrators which port the app uses.
# It does NOT actually publish the port. That's done in docker-compose.yml.
EXPOSE 8000

# ---- Stage 6: Run the Application ----
# CMD is the default command when the container starts.
# uvicorn: The ASGI server that translates HTTP bytes → Python async calls.
# app.main:app → "In the app/ package, find main.py, use the 'app' object"
# --host 0.0.0.0: Listen on ALL network interfaces inside the container.
#   If you used 127.0.0.1, the app would only be reachable from INSIDE the container.
# --reload: Watch for file changes and restart. ONLY for development.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
