from pathlib import Path

import app.db as db_module
from fastapi.testclient import TestClient

from app.main import create_app


def create_client(tmp_path: Path) -> TestClient:
    db_module.DEFAULT_DB_PATH = tmp_path / "pm.sqlite3"
    frontend_out = tmp_path / "out"
    frontend_out.mkdir(parents=True, exist_ok=True)
    (frontend_out / "index.html").write_text(
        "<html><body><h1>Kanban Studio</h1></body></html>",
        encoding="utf-8",
    )
    return TestClient(create_app(frontend_out))


def test_api_hello_returns_json() -> None:
    app = create_app()
    client = TestClient(app)
    response = client.get("/api/hello")
    assert response.status_code == 200
    assert response.json() == {"message": "hello world"}


def test_root_serves_exported_index(tmp_path: Path) -> None:
    client = create_client(tmp_path)

    unauth_resp = client.get("/", follow_redirects=False)
    assert unauth_resp.status_code in (302, 307)
    assert unauth_resp.headers["location"] == "/login"

    login_resp = client.post(
        "/api/login",
        data={"username": "user", "password": "password"},
        follow_redirects=False,
    )
    assert login_resp.status_code in (302, 307)

    authed_resp = client.get("/", follow_redirects=False)
    assert authed_resp.status_code == 200
    assert "Kanban Studio" in authed_resp.text

    logout_resp = client.get("/logout", follow_redirects=False)
    assert logout_resp.status_code in (302, 307)
    assert logout_resp.headers["location"] == "/login"

    after_logout_resp = client.get("/", follow_redirects=False)
    assert after_logout_resp.status_code in (302, 307)
    assert after_logout_resp.headers["location"] == "/login"


def test_root_returns_503_when_frontend_missing(tmp_path: Path) -> None:
    db_module.DEFAULT_DB_PATH = tmp_path / "pm.sqlite3"
    app = create_app(tmp_path / "does-not-exist")
    client = TestClient(app)

    login_resp = client.post(
        "/api/login",
        data={"username": "user", "password": "password"},
        follow_redirects=False,
    )
    assert login_resp.status_code in (302, 307)

    response = client.get("/", follow_redirects=False)
    assert response.status_code == 503
    assert response.json()["error"] == "frontend build missing"


def test_login_rejects_invalid_credentials(tmp_path: Path) -> None:
    client = create_client(tmp_path)

    resp = client.post(
        "/api/login",
        data={"username": "user", "password": "wrong"},
        follow_redirects=False,
    )
    assert resp.status_code == 401
    assert "Sign in" in resp.text


def test_api_board_requires_authentication(tmp_path: Path) -> None:
    client = create_client(tmp_path)

    get_response = client.get("/api/board")
    assert get_response.status_code == 401
    assert get_response.json() == {"detail": "Authentication required"}

    put_response = client.put("/api/board", json={"columns": [], "cards": {}})
    assert put_response.status_code == 401
    assert put_response.json() == {"detail": "Authentication required"}


def test_api_board_returns_default_board_after_login(tmp_path: Path) -> None:
    client = create_client(tmp_path)
    login_response = client.post(
        "/api/login",
        data={"username": "user", "password": "password"},
        follow_redirects=False,
    )
    assert login_response.status_code in (302, 307)

    response = client.get("/api/board")
    assert response.status_code == 200
    body = response.json()
    assert body["board"]["columns"][0]["title"] == "Backlog"
    assert body["board"]["cards"]["card-1"]["title"] == "Align roadmap themes"


def test_api_board_replaces_board(tmp_path: Path) -> None:
    client = create_client(tmp_path)
    login_response = client.post(
        "/api/login",
        data={"username": "user", "password": "password"},
        follow_redirects=False,
    )
    assert login_response.status_code in (302, 307)

    board = {
        "columns": [{"id": "col-backlog", "title": "Custom", "cardIds": ["card-1"]}],
        "cards": {
            "card-1": {"id": "card-1", "title": "Updated", "details": "Persist me."}
        },
    }
    response = client.put("/api/board", json=board)

    assert response.status_code == 200
    assert response.json() == {"board": board}

    saved = client.get("/api/board")
    assert saved.status_code == 200
    assert saved.json() == {"board": board}


def test_api_board_rejects_invalid_payload(tmp_path: Path) -> None:
    client = create_client(tmp_path)
    login_response = client.post(
        "/api/login",
        data={"username": "user", "password": "password"},
        follow_redirects=False,
    )
    assert login_response.status_code in (302, 307)

    invalid_board = {
        "columns": [{"id": "col-backlog", "title": "Backlog", "cardIds": ["card-9"]}],
        "cards": {},
    }
    response = client.put("/api/board", json=invalid_board)

    assert response.status_code == 422
    assert "missing cards" in response.text
