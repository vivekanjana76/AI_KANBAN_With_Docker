from pathlib import Path

from app.db import get_board, init_db, upsert_board


def test_init_db_creates_table(tmp_path: Path) -> None:
    db_path = tmp_path / "pm.sqlite3"
    assert not db_path.exists()

    init_db(db_path)
    assert db_path.exists()

    assert get_board("user", db_path) is None


def test_get_board_when_db_missing_returns_none(tmp_path: Path) -> None:
    db_path = tmp_path / "missing.sqlite3"
    assert not db_path.exists()
    assert get_board("user", db_path) is None


def test_upsert_and_load_round_trip(tmp_path: Path) -> None:
    db_path = tmp_path / "pm.sqlite3"
    board = {
        "columns": [
            {"id": "col-backlog", "title": "Backlog", "cardIds": ["card-1"]},
        ],
        "cards": {"card-1": {"id": "card-1", "title": "T", "details": "D"}},
    }

    upsert_board("user", board, db_path)
    loaded = get_board("user", db_path)
    assert loaded == board


def test_upsert_updates_existing_row(tmp_path: Path) -> None:
    db_path = tmp_path / "pm.sqlite3"

    board_1 = {
        "columns": [{"id": "col-backlog", "title": "Backlog", "cardIds": []}],
        "cards": {},
    }
    board_2 = {
        "columns": [{"id": "col-backlog", "title": "Backlog", "cardIds": ["card-1"]}],
        "cards": {"card-1": {"id": "card-1", "title": "T2", "details": "D2"}},
    }

    upsert_board("user", board_1, db_path)
    assert get_board("user", db_path) == board_1

    upsert_board("user", board_2, db_path)
    assert get_board("user", db_path) == board_2

