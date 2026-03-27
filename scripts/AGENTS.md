# Scripts Guide

This folder contains start and stop scripts for Mac, Windows, and Linux.

## Scripts

- `start-mac.sh`: Builds and starts Docker stack in detached mode.
- `stop-mac.sh`: Stops and removes Docker stack.
- `start-linux.sh`: Builds and starts Docker stack in detached mode.
- `stop-linux.sh`: Stops and removes Docker stack.
- `start-windows.ps1`: Builds and starts Docker stack in detached mode.
- `stop-windows.ps1`: Stops and removes Docker stack.

## Notes

- All scripts run from repository root and target `docker-compose.yml`.
- Service is exposed at `http://localhost:8000`.