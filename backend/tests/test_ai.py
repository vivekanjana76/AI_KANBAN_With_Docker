from pathlib import Path

import app.db as db_module
from fastapi.testclient import TestClient

from app.ai import (
    AIModelResponse,
    AIServiceError,
    _coerce_json_text,
    _parse_structured_response,
    _require_openrouter_api_key,
    request_openrouter_structured_response,
)
from app.board import default_board
from app.main import create_app


def create_authed_client(tmp_path: Path) -> TestClient:
    db_module.DEFAULT_DB_PATH = tmp_path / "pm.sqlite3"
    frontend_out = tmp_path / "out"
    frontend_out.mkdir(parents=True, exist_ok=True)
    (frontend_out / "index.html").write_text("<html></html>", encoding="utf-8")
    client = TestClient(create_app(frontend_out))
    login_response = client.post(
        "/api/login",
        data={"username": "user", "password": "password"},
        follow_redirects=False,
    )
    assert login_response.status_code in (302, 307)
    return client


def test_ai_model_response_accepts_valid_board_update() -> None:
    parsed = AIModelResponse.model_validate(
        {
            "assistant_message": "Created the task.",
            "board_update": default_board(),
        }
    )

    assert parsed.assistant_message == "Created the task."
    assert parsed.board_update is not None
    assert parsed.board_update.columns[0].title == "Backlog"


def test_parse_structured_response_rejects_invalid_board() -> None:
    invalid_payload = """
    {
      "assistant_message": "Done.",
      "board_update": {
        "columns": [{"id": "col-backlog", "title": "Backlog", "cardIds": ["card-9"]}],
        "cards": {}
      }
    }
    """

    try:
        _parse_structured_response(invalid_payload)
    except AIServiceError as exc:
        assert exc.message == "AI returned invalid structured output"
    else:
        raise AssertionError("Expected invalid structured output to fail")


def test_coerce_json_text_extracts_json_from_markdown() -> None:
    content = '```json\\n{"assistant_message":"Done.","board_update":null}\\n```'
    assert _coerce_json_text(content) == '{"assistant_message":"Done.","board_update":null}'


def test_require_openrouter_api_key_raises_when_missing(monkeypatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    try:
        _require_openrouter_api_key()
    except AIServiceError as exc:
        assert exc.status_code == 503
        assert exc.message == "OPENROUTER_API_KEY is not configured"
    else:
        raise AssertionError("Expected missing API key to fail")


def test_request_openrouter_structured_response_falls_back_to_json_object(monkeypatch) -> None:
    calls: list[dict] = []

    async def fake_post(body: dict) -> dict:
        calls.append(body)
        if len(calls) == 1:
            raise AIServiceError(
                "No endpoints found that can handle the requested parameters.",
                status_code=502,
            )
        return {
            "choices": [
                {
                    "message": {
                        "content": '{"assistant_message":"Done.","board_update":null}'
                    }
                }
            ]
        }

    monkeypatch.setattr("app.ai._post_openrouter_completion", fake_post)

    import asyncio

    result = asyncio.run(
        request_openrouter_structured_response(
            "Summarize the board",
            [],
            default_board(),
        )
    )

    assert result.assistant_message == "Done."
    assert result.board_update is None
    assert calls[0]["response_format"]["type"] == "json_schema"
    assert calls[1]["response_format"]["type"] == "json_object"


def test_request_openrouter_structured_response_retries_after_invalid_output(monkeypatch) -> None:
    calls: list[dict] = []

    async def fake_post(body: dict) -> dict:
        calls.append(body)
        if len(calls) == 1:
            return {"choices": [{"message": {"content": "not valid json"}}]}
        return {
            "choices": [
                {
                    "message": {
                        "content": '{"assistant_message":"Done.","board_update":null}'
                    }
                }
            ]
        }

    monkeypatch.setattr("app.ai._post_openrouter_completion", fake_post)

    import asyncio

    result = asyncio.run(
        request_openrouter_structured_response(
            "Summarize the board",
            [],
            default_board(),
        )
    )

    assert result.assistant_message == "Done."
    assert len(calls) == 2


def test_ai_chat_returns_board_update_and_persists(tmp_path: Path, monkeypatch) -> None:
    async def fake_ai_response(*args, **kwargs):
        board = default_board()
        board["columns"][0]["title"] = "AI Planned"
        return AIModelResponse.model_validate(
            {
                "assistant_message": "I renamed the first column.",
                "board_update": board,
            }
        )

    monkeypatch.setattr("app.main.request_openrouter_structured_response", fake_ai_response)
    client = create_authed_client(tmp_path)

    response = client.post(
        "/api/ai/chat",
        json={"message": "Rename the first column", "history": []},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["assistant_message"] == "I renamed the first column."
    assert body["board_updated"] is True
    assert body["board"]["columns"][0]["title"] == "AI Planned"

    saved_board = client.get("/api/board")
    assert saved_board.status_code == 200
    assert saved_board.json()["board"]["columns"][0]["title"] == "AI Planned"


def test_ai_chat_keeps_current_board_when_no_update_returned(tmp_path: Path, monkeypatch) -> None:
    async def fake_ai_response(*args, **kwargs):
        return AIModelResponse.model_validate(
            {"assistant_message": "No board changes needed.", "board_update": None}
        )

    monkeypatch.setattr("app.main.request_openrouter_structured_response", fake_ai_response)
    client = create_authed_client(tmp_path)

    response = client.post(
        "/api/ai/chat",
        json={"message": "Summarize the board", "history": []},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["assistant_message"] == "No board changes needed."
    assert body["board_updated"] is False
    assert body["board"]["columns"][0]["title"] == "Backlog"


def test_ai_chat_does_not_persist_client_board_when_ai_returns_no_update(
    tmp_path: Path, monkeypatch
) -> None:
    async def fake_ai_response(*args, **kwargs):
        return AIModelResponse.model_validate(
            {"assistant_message": "No board changes needed.", "board_update": None}
        )

    monkeypatch.setattr("app.main.request_openrouter_structured_response", fake_ai_response)
    client = create_authed_client(tmp_path)

    latest_board = default_board()
    latest_board["columns"][0]["title"] = "Latest Server Title"
    save_response = client.put("/api/board", json=latest_board)
    assert save_response.status_code == 200

    stale_board = default_board()
    response = client.post(
        "/api/ai/chat",
        json={"message": "Summarize the board", "history": [], "board": stale_board},
    )

    assert response.status_code == 200
    assert response.json()["board"]["columns"][0]["title"] == "Backlog"

    saved_board = client.get("/api/board")
    assert saved_board.status_code == 200
    assert saved_board.json()["board"]["columns"][0]["title"] == "Latest Server Title"


def test_ai_chat_does_not_persist_client_board_when_ai_errors(
    tmp_path: Path, monkeypatch
) -> None:
    async def fake_ai_response(*args, **kwargs):
        raise AIServiceError("Upstream unavailable", status_code=502)

    monkeypatch.setattr("app.main.request_openrouter_structured_response", fake_ai_response)
    client = create_authed_client(tmp_path)

    latest_board = default_board()
    latest_board["columns"][0]["title"] = "Latest Server Title"
    save_response = client.put("/api/board", json=latest_board)
    assert save_response.status_code == 200

    stale_board = default_board()
    response = client.post(
        "/api/ai/chat",
        json={"message": "Summarize the board", "history": [], "board": stale_board},
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "Upstream unavailable"}

    saved_board = client.get("/api/board")
    assert saved_board.status_code == 200
    assert saved_board.json()["board"]["columns"][0]["title"] == "Latest Server Title"


def test_ai_chat_requires_authentication(tmp_path: Path) -> None:
    db_module.DEFAULT_DB_PATH = tmp_path / "pm.sqlite3"
    frontend_out = tmp_path / "out"
    frontend_out.mkdir(parents=True, exist_ok=True)
    (frontend_out / "index.html").write_text("<html></html>", encoding="utf-8")
    client = TestClient(create_app(frontend_out))

    response = client.post(
        "/api/ai/chat",
        json={"message": "Hello", "history": []},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}


def test_ai_chat_returns_service_errors_cleanly(tmp_path: Path, monkeypatch) -> None:
    async def fake_ai_response(*args, **kwargs):
        raise AIServiceError("Upstream unavailable", status_code=502)

    monkeypatch.setattr("app.main.request_openrouter_structured_response", fake_ai_response)
    client = create_authed_client(tmp_path)

    response = client.post(
        "/api/ai/chat",
        json={"message": "Hello", "history": []},
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "Upstream unavailable"}


def test_ai_test_endpoint_returns_mocked_result(tmp_path: Path, monkeypatch) -> None:
    async def fake_test_response(prompt: str) -> str:
        assert prompt == "2+2"
        return "4"

    monkeypatch.setattr("app.main.request_openrouter_test_response", fake_test_response)
    client = create_authed_client(tmp_path)

    response = client.get("/api/ai/test")

    assert response.status_code == 200
    assert response.json() == {
        "assistant_message": "4",
        "model": "openai/gpt-oss-120b:free",
    }
