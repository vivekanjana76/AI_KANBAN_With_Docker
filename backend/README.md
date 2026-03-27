# Backend

FastAPI backend for the Project Management MVP.

## Local development (without Docker)

```bash
uv sync --directory backend --group dev
uv run --directory backend uvicorn app.main:app --reload
```

## Tests

```bash
uv run --directory backend pytest
```
