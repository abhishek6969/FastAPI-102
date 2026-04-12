#!/bin/sh
set -e

# Start SSH service - ignore errors if already started
service ssh start || echo "SSH service failed to start or already running"

# Start our App
# exec: Replaces the shell with Gunicorn as Process #1 (important for Docker signals)
# -w 4: Spawns 4 worker processes (The "Assembly Line")
# -k uvicorn...: Tells Gunicorn to use Uvicorn for handling async FastAPI requests
exec gunicorn -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 app.main:app
