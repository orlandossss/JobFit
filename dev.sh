#!/usr/bin/env bash
# dev.sh — Start both JobFit servers concurrently (macOS / Linux)
#
# Usage: bash dev.sh
#
# Requirements:
#   - Python 3.10+ with FastAPI and uvicorn installed (see backend/requirements.txt)
#   - Node 20+ with dependencies installed (run `npm install` once inside frontend/)

set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

# Start backend in background
echo "Starting backend on http://localhost:8000 ..."
(cd "$ROOT/backend" && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000) &
BACKEND_PID=$!

# Start frontend in background
echo "Starting frontend on http://localhost:5173 ..."
(cd "$ROOT/frontend" && npm run dev) &
FRONTEND_PID=$!

echo ""
echo "JobFit dev servers running:"
echo "  Backend  -> http://localhost:8000"
echo "  Frontend -> http://localhost:5173"
echo ""
echo "Health check: http://localhost:8000/health"
echo "Press Ctrl+C to stop both servers."

# Wait for both; kill both on exit
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
