# Frontend Guide

## Purpose

`frontend/` contains the Next.js Kanban MVP UI. It loads and saves board state through the FastAPI backend and includes an AI chat sidebar for board-aware assistance.

## Tech Stack

- Next.js 16 (App Router) with React 19 and TypeScript.
- Tailwind CSS v4 with custom CSS variables for project colors.
- Drag-and-drop powered by `@dnd-kit`.
- Unit tests with Vitest + Testing Library.
- End-to-end tests with Playwright.

## Current App Structure

- `src/app/page.tsx`: App entry point that renders `KanbanBoard`.
- `src/components/KanbanBoard.tsx`: Main board container and state owner.
- `src/components/KanbanColumn.tsx`: Column rendering, rename, and per-column add-card entry.
- `src/components/KanbanCard.tsx`: Sortable card item with remove action.
- `src/components/NewCardForm.tsx`: Inline card creation form.
- `src/lib/kanban.ts`: Board types, initial demo data, move logic, and ID creation.

## Implemented Behavior

- Five-column Kanban board loads from backend API on page open.
- Column titles are editable inline.
- Cards can be added and removed.
- Cards can be reordered within a column and moved across columns via drag-and-drop.
- Board changes persist through backend API saves.
- Loading, save, and error states are surfaced in the UI.
- AI sidebar sends conversation history plus current board state to the backend and applies returned board updates immediately.

## Styling and Design Notes

- Color variables in `src/app/globals.css` match project palette from root `AGENTS.md`.
- Display/body fonts are configured in `src/app/layout.tsx`.
- The UI favors a clean, single-board layout with minimal controls.

## Testing Setup

- Unit tests are colocated under `src/` (`*.test.tsx`, `*.test.ts`).
- E2E specs live in `tests/`.
- Scripts in `package.json`:
  - `npm run test:unit`
  - `npm run test:e2e`
  - `npm run test:all`

## Notes

- Playwright e2e now runs against the real FastAPI-served static build, not `next dev`.
- The frontend stays client-rendered so the static export can call backend APIs at runtime.
- Server-originated board updates from initial load and AI responses intentionally skip the debounced save echo.
