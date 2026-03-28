# Code Review

## Findings

1. High: Manual card editing is not implemented, so the current app does not meet the MVP requirement that cards can be edited.
   Evidence:
   `frontend/src/components/KanbanBoard.tsx` only contains handlers for column rename, card add, card delete, drag/drop, and AI submission (`handleRenameColumn`, `handleAddCard`, `handleDeleteCard`, `handleDragEnd`, `handleAiSubmit`).
   `frontend/src/components/KanbanCard.tsx` renders the card title/details as read-only text and exposes only a `Remove` button.
   Impact:
   A signed-in user can move, add, and delete cards, but cannot directly edit an existing card's title or details in the UI.

2. High: `POST /api/ai/chat` persists the client-supplied board before the AI responds, so a stale tab can overwrite newer saved work even when the AI returns `board_update: null`.
   Evidence:
   In `backend/app/main.py`, lines 153-156 write `payload.board` with `upsert_board(username, current_board)` before `request_openrouter_structured_response(...)` is called.
   I reproduced this with `TestClient`: save a newer board through `PUT /api/board`, then send `/api/ai/chat` with an older board plus a mocked AI response that returns no update. The endpoint returned and re-saved the stale board.
   Impact:
   Read-only AI actions such as "summarize the board" can silently roll back newer changes from another tab or window. The same rollback also happens if the AI call fails after the pre-write.

3. Medium: The catch-all frontend route returns `index.html` for every missing non-API path, which both weakens auth routing and hides broken asset paths.
   Evidence:
   In `backend/app/main.py`, lines 196-213 return `index.html` whenever the requested file does not exist.
   I verified that unauthenticated `GET /anything` returns `200` with the app shell instead of redirecting to `/login`, and `GET /missing.js` also returns `200` with HTML instead of `404`.
   Impact:
   This breaks the expectation from the plan that unauthenticated users are kept off the board route, and it can turn missing static assets into hard-to-debug HTML responses in the browser.

4. Medium: The Docker build ignores `backend/uv.lock`, so container installs are not reproducible and can drift from the dependency set used in local testing.
   Evidence:
   `Dockerfile` copies only `backend/pyproject.toml` and `backend/README.md` before running `uv sync --directory /app/backend`.
   `backend/uv.lock` is copied only later as part of `COPY backend /app/backend`, after dependency resolution has already happened.
   Impact:
   A fresh Docker build can resolve newer package versions than the ones implicitly validated by local development and CI, which makes regressions harder to reproduce.

## Validation Performed

- `uv run --directory backend pytest`
- `npm run test:unit` in `frontend/`
- `npm run test:e2e` in `frontend/`
- Targeted repro scripts for:
  - stale-board overwrite through `/api/ai/chat`
  - unauthenticated `GET /anything`
  - missing asset `GET /missing.js`
