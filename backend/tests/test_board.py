from pathlib import Path

import app.db as db_module
from app.board import BoardPayload, default_board
from app.main import load_or_create_board


def test_default_board_is_valid() -> None:
    payload = BoardPayload.model_validate(default_board())
    assert len(payload.columns) == 5
    assert len(payload.cards) == 8


def test_default_board_returns_fresh_copy() -> None:
    board_a = default_board()
    board_b = default_board()

    board_a["columns"][0]["title"] = "Changed"

    assert board_b["columns"][0]["title"] == "Backlog"


def test_board_payload_rejects_missing_card_reference() -> None:
    board = default_board()
    board["columns"][0]["cardIds"].append("card-missing")

    try:
        BoardPayload.model_validate(board)
    except Exception as exc:
        assert "missing cards" in str(exc)
    else:
        raise AssertionError("Expected board validation to fail")


def test_load_or_create_board_persists_default_board(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "pm.sqlite3"
    monkeypatch.setattr(db_module, "DEFAULT_DB_PATH", db_path)

    board = load_or_create_board("user")

    assert board == default_board()
    assert db_module.get_board("user", db_path) == default_board()
