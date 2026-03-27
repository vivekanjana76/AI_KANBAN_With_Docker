import json
import os
import sqlite3
from pathlib import Path
from typing import Any

DEFAULT_DB_PATH = Path(os.environ.get("DB_PATH", "data/pm.sqlite3"))


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path | None = None) -> None:
    db_path = (db_path or DEFAULT_DB_PATH).resolve()
    with _connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS boards (
              username TEXT PRIMARY KEY,
              board_json TEXT NOT NULL,
              updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def get_board(username: str, db_path: Path | None = None) -> dict[str, Any] | None:
    db_path = (db_path or DEFAULT_DB_PATH).resolve()
    if not db_path.exists():
        return None

    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT board_json FROM boards WHERE username = ?",
            (username,),
        ).fetchone()
        if not row:
            return None
        return json.loads(row["board_json"])


def upsert_board(
    username: str, board: dict[str, Any], db_path: Path | None = None
) -> None:
    db_path = (db_path or DEFAULT_DB_PATH).resolve()
    init_db(db_path)

    board_json = json.dumps(board, separators=(",", ":"), ensure_ascii=False)
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO boards (username, board_json)
            VALUES (?, ?)
            ON CONFLICT(username) DO UPDATE SET
              board_json = excluded.board_json,
              updated_at = CURRENT_TIMESTAMP
            """,
            (username, board_json),
        )

