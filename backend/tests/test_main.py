from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def test_api_hello_returns_json() -> None:
    app = create_app()
    client = TestClient(app)
    response = client.get("/api/hello")
    assert response.status_code == 200
    assert response.json() == {"message": "hello world"}


def test_root_serves_exported_index(tmp_path: Path) -> None:
    frontend_out = tmp_path / "out"
    frontend_out.mkdir(parents=True, exist_ok=True)
    (frontend_out / "index.html").write_text(
        "<html><body><h1>Kanban Studio</h1></body></html>",
        encoding="utf-8",
    )
    app = create_app(frontend_out)
    client = TestClient(app)

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
    frontend_out = tmp_path / "out"
    frontend_out.mkdir(parents=True, exist_ok=True)
    (frontend_out / "index.html").write_text(
        "<html><body><h1>Kanban Studio</h1></body></html>",
        encoding="utf-8",
    )
    app = create_app(frontend_out)
    client = TestClient(app)

    resp = client.post(
        "/api/login",
        data={"username": "user", "password": "wrong"},
        follow_redirects=False,
    )
    assert resp.status_code == 401
    assert "Sign in" in resp.text
