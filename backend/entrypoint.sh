#!/bin/bash
set -e

echo "Running area seed..."
# python -m app.seed_areas

echo "Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
