# Backend Guide

## Purpose

`backend/` contains the FastAPI service for the Project Management MVP.

## Current Scope (Part 3 Static Frontend Serving)

- Exposes `GET /api/hello` with JSON response.
- Serves statically built frontend assets from `frontend/out`.
- Serves `index.html` at `/` when frontend build exists.
- Returns a clear `503` error at `/` if frontend build output is missing.
- Includes backend unit tests for API and static serving behavior.

## Stack and Tooling

- Python 3.12+
- FastAPI + Uvicorn
- `uv` for dependency and command management
- `pytest` for tests

## Directory Layout

- `app/main.py`: FastAPI app and scaffold routes.
- `app/db.py`: SQLite JSON board persistence helpers.
- `tests/test_main.py`: Route tests using `TestClient`.
- `tests/test_db.py`: Unit tests for DB init + JSON round trip.
- `pyproject.toml`: Dependencies and project metadata.
- `uv.lock`: Locked Python dependencies for reproducible setup.

## Notes

- Frontend serving in this phase is static export based.
- More backend API and persistence features are added in later parts.