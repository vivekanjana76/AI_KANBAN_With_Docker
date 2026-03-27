# Project Plan Checklist

This document is the execution checklist for the MVP. Work proceeds in order. Each part includes implementation tasks, tests, and success criteria.

## Part 1: Planning and Project Documentation

### Tasks
- [x] Expand this plan into detailed execution steps.
- [x] Add explicit test plan and success criteria per part.
- [x] Create `frontend/AGENTS.md` documenting existing frontend code and conventions.
- [ ] Keep this checklist updated as work is completed.

### Tests
- [ ] Manual review that all parts include actionable tasks, tests, and success criteria.

### Success Criteria
- Plan is concrete enough to execute with minimal ambiguity.
- Frontend documentation exists and reflects the current codebase.

## Part 2: Scaffolding (Docker + FastAPI + Scripts)

### Tasks
- [x] Create `backend/` FastAPI app scaffold using modern structure.
- [x] Add Docker setup to run backend and serve app from one container.
- [x] Add cross-platform start/stop scripts in `scripts/` for Mac, Linux, and Windows.
- [x] Add temporary scaffold routes:
  - [x] `/` returns simple static Hello World HTML.
  - [x] `/api/hello` returns JSON payload.
- [x] Ensure Python dependencies use `uv` in container build/runtime flow.
- [x] Add minimal backend test scaffold.

### Tests
- [x] Container build succeeds from clean environment.
- [ ] Start scripts launch app successfully on supported OS (Windows validated; Mac/Linux pending runtime check).
- [x] `GET /` returns expected scaffold page.
- [x] `GET /api/hello` returns expected JSON.
- [x] Backend unit test command passes.

### Success Criteria
- Dockerized app starts locally with one command/script.
- Static HTML and API route are reachable and validated.
- Temporary scaffold is in place and ready to be replaced by real frontend in Part 3.

## Part 3: Integrate Existing Frontend Build

### Tasks
- [x] Build Next.js frontend as static output.
- [x] Configure backend to serve built frontend assets at `/`.
- [x] Replace temporary Hello World page with the Kanban UI.
- [x] Keep backend API namespace available under `/api/*`.
- [x] Add/adjust integration tests for static serving behavior.

### Tests
- [x] Frontend unit tests pass.
- [x] Frontend e2e tests pass against served app.
- [x] Containerized app serves Kanban page at `/`.
- [x] Core static assets load without 404 errors.

### Success Criteria
- Visiting `/` shows demo Kanban board from existing frontend.
- App runs from FastAPI server within Docker using built frontend assets.

## Part 4: Dummy Authentication Flow

### Tasks
- [x] Add login screen at entry when unauthenticated.
- [x] Validate hardcoded credentials: `user` / `password`.
- [x] Implement logout action that clears session and returns to login.
- [x] Use simple cookie-based server session appropriate for local MVP.
- [x] Protect board route so Kanban is only visible when signed in.

### Tests
- [x] Unit tests for credential validation and session helpers.
- [x] Integration tests for protected routes and redirect behavior.
- [ ] e2e tests for successful login, failed login, and logout.

### Success Criteria
- Unauthenticated users cannot access Kanban board.
- Valid dummy credentials consistently unlock the app.
- Logout fully returns to unauthenticated state.

## Part 5: Database Modeling (SQLite + JSON Board Storage)

### Tasks
- [ ] Document schema choice in `docs/` before implementation details expand.
- [ ] Implement SQLite schema with one board record per user.
- [ ] Store board state as JSON text/blob for MVP simplicity.
- [ ] Include fields needed for future multi-user support.
- [ ] Add migration/init logic so DB and tables are created if missing.

### Tests
- [ ] Unit tests for DB initialization and schema creation.
- [ ] Unit tests for save/load board JSON round trips.
- [ ] Tests for behavior when DB file does not exist.

### Success Criteria
- Schema supports current MVP and future multi-user extension.
- Kanban JSON persists and reloads accurately per user.

## Part 6: Backend Kanban API

### Tasks
- [ ] Add API routes for authenticated user board operations:
  - [ ] Read board.
  - [ ] Replace/update board.
  - [ ] Optional targeted card/column operations if needed by UI.
- [ ] Validate payload shapes with clear errors.
- [ ] Keep API responses stable and documented.
- [ ] Ensure DB file/tables auto-create on first run.

### Tests
- [ ] Backend unit tests for service and data layer logic.
- [ ] API tests for success and failure cases.
- [ ] Auth tests to ensure unauthorized requests are blocked.

### Success Criteria
- API can reliably read and persist Kanban state.
- Invalid requests fail with clear, consistent responses.

## Part 7: Connect Frontend to Backend Persistence

### Tasks
- [ ] Replace frontend local-only state initialization with API-backed load.
- [ ] Persist board changes via backend API after edits/moves.
- [ ] Handle loading, save, and error states simply and clearly.
- [ ] Keep drag/drop and editing UX responsive.

### Tests
- [ ] Frontend unit tests for API client/state orchestration.
- [ ] Integration tests with mocked API responses.
- [ ] e2e tests proving persistence across page reloads.

### Success Criteria
- User changes survive refresh and restart.
- UI remains stable when API errors occur.

## Part 8: OpenRouter Connectivity

### Tasks
- [ ] Add backend OpenRouter client using `OPENROUTER_API_KEY` from `.env`.
- [ ] Configure model: `OpenAI: gpt-oss-120b (free)`.
- [ ] Add simple test endpoint/service call for connectivity.
- [ ] Implement request timeout and user-safe error handling.

### Tests
- [ ] Integration test path for successful AI call (mocked for CI).
- [ ] Manual/local smoke test using prompt `2+2`.
- [ ] Tests for missing/invalid API key behavior.

### Success Criteria
- Backend can complete a basic OpenRouter request in local environment.
- Failures are surfaced clearly without crashing app.

## Part 9: Structured AI Responses With Board Context

### Tasks
- [ ] Define structured response schema in backend:
  - [ ] `assistant_message` (required string).
  - [ ] `board_update` (optional full board JSON patch/replacement).
- [ ] Send current board JSON + user message + conversation history to AI.
- [ ] Validate AI output against schema before applying.
- [ ] Persist accepted board updates through existing backend path.

### Tests
- [ ] Unit tests for schema validation and parsing.
- [ ] Tests for valid update, no update, and invalid output fallback.
- [ ] Integration tests ensuring data consistency after AI-assisted updates.

### Success Criteria
- AI responses are machine-parseable and safe to apply.
- Board updates only occur when structured output validates.

## Part 10: AI Sidebar UX

### Tasks
- [ ] Add sidebar chat widget in frontend UI.
- [ ] Show conversation history and submit user prompts.
- [ ] Call backend AI endpoint and render assistant responses.
- [ ] Apply board updates returned by AI and refresh board state immediately.
- [ ] Preserve clean, minimal visual design aligned with project color scheme.

### Tests
- [ ] Component tests for chat widget interactions.
- [ ] Integration tests for AI request lifecycle (loading, success, error).
- [ ] e2e test covering: ask AI -> receives response -> board updates when provided.

### Success Criteria
- Chat sidebar is intuitive and stable.
- AI can answer questions and optionally modify Kanban board in-app.
- Board UI refresh reflects AI updates without manual reload.