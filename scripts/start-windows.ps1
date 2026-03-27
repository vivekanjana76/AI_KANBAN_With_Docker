$ErrorActionPreference = "Stop"

docker compose up --build -d
docker compose ps
Write-Host "App is starting at http://localhost:8000"
