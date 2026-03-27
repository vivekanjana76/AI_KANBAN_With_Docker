# Backend Guide

## Purpose

`backend/` contains the FastAPI service for the Project Management MVP.

## Current Scope

- Exposes dummy auth with session cookie login/logout.
- Exposes `GET /api/board` and `PUT /api/board` for authenticated board persistence.
- Auto-creates the SQLite DB and a default board for the signed-in user.
- Exposes `GET /api/ai/test` for simple OpenRouter connectivity checks.
- Exposes `POST /api/ai/chat` for structured assistant responses plus optional board updates.
- Serves statically built frontend assets from `frontend/out`.
- Returns a clear `503` error at `/` if frontend build output is missing.
- Includes backend unit and API tests for auth, persistence, and AI integration paths.

## Stack and Tooling

- Python 3.12+
- FastAPI + Uvicorn
- `uv` for dependency and command management
- `pytest` for tests

## Directory Layout

- `app/main.py`: FastAPI app and scaffold routes.
- `app/db.py`: SQLite JSON board persistence helpers.
- `app/board.py`: Board schema validation and default board seed.
- `app/ai.py`: OpenRouter client, AI request/response schemas, and error handling.
- `tests/test_main.py`: Route tests using `TestClient`.
- `tests/test_db.py`: Unit tests for DB init + JSON round trip.
- `tests/test_board.py`: Board validation and default-board tests.
- `tests/test_ai.py`: AI schema, fallback, and endpoint tests.
- `pyproject.toml`: Dependencies and project metadata.
- `uv.lock`: Locked Python dependencies for reproducible setup.

## Notes

- Frontend serving is static export based.
- The AI path validates model output before persisting any board changes.
- The backend loads `.env` from repo root for local runs, and Docker Compose injects the same file at runtime.
