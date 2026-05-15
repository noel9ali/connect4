#!/usr/bin/env bash
set -e

echo "Starting Flask backend on :5000..."
python api.py &
BACKEND_PID=$!

echo "Starting Vite frontend on :5173..."
cd frontend && npm run dev &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT INT TERM
wait
