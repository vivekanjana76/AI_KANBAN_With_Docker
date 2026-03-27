#!/usr/bin/env bash
set -euo pipefail

docker compose up --build -d
docker compose ps
echo "App is starting at http://localhost:8000"
