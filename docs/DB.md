# Database Model (MVP)

## Goal

Persist a single Kanban board per signed-in user.

## MVP Storage Choice

Store the entire board state as JSON in SQLite (one row per user). This keeps the backend simple and makes it easy for the AI to return structured board updates that we can persist as a single document.

## Table Schema

`boards`

- `username` (TEXT, PRIMARY KEY): signed-in user identifier
- `board_json` (TEXT NOT NULL): full Kanban board document serialized as JSON
- `updated_at` (TEXT NOT NULL): last update timestamp (SQLite `CURRENT_TIMESTAMP`)

## Board JSON Shape

The stored `board_json` matches the frontend `BoardData` shape:

```json
{
  "columns": [
    { "id": "col-backlog", "title": "Backlog", "cardIds": ["card-1", "card-2"] }
  ],
  "cards": {
    "card-1": { "id": "card-1", "title": "Align roadmap themes", "details": "..." }
  }
}
```

## Future Extension (No Migration Needed for MVP)

When multi-user boards and additional operations are added later, this schema can be extended by:

- changing `username` to `user_id`
- normalizing columns/cards into separate tables (optional)
- keeping the JSON column for rapid AI integration
