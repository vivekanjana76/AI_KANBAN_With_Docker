from pathlib import Path
import os

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response
from starlette.middleware.sessions import SessionMiddleware


def create_app(frontend_dist: Path | None = None) -> FastAPI:
    app = FastAPI(title="Project Management MVP API")
    root_dir = Path(__file__).resolve().parents[2]
    frontend_root = (frontend_dist or (root_dir / "frontend" / "out")).resolve()

    secret_key = os.environ.get("SESSION_SECRET", "dev-session-secret")
    app.add_middleware(
        SessionMiddleware,
        secret_key=secret_key,
        session_cookie="pm_session",
        same_site="lax",
        https_only=False,
    )

    def render_login_page(error_message: str | None = None, status_code: int = 200) -> HTMLResponse:
        error_html = (
            f"<p style='color:#b91c1c; font-weight:600; margin-top: 16px;'>{error_message}</p>"
            if error_message
            else ""
        )
        return HTMLResponse(
            f"""
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Sign in</title>
  </head>
  <body style="font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial; margin: 40px;">
    <h1>Sign in</h1>
    <form method="post" action="/api/login">
      <label>
        Username
        <input name="username" placeholder="user" />
      </label>
      <br />
      <br />
      <label>
        Password
        <input name="password" type="password" placeholder="password" />
      </label>
      <br />
      <br />
      <button type="submit">Login</button>
    </form>
    {error_html}
  </body>
</html>
""",
            status_code=status_code,
        )

    @app.get("/login")
    def login_page() -> HTMLResponse:
        return render_login_page()

    @app.post("/api/login")
    def do_login(request: Request, username: str = Form(...), password: str = Form(...)) -> Response:
        if username == "user" and password == "password":
            request.session["authed"] = True
            return RedirectResponse(url="/", status_code=302)

        return render_login_page("Invalid username/password", status_code=401)

    @app.get("/logout")
    def do_logout(request: Request) -> Response:
        request.session.clear()
        return RedirectResponse(url="/login", status_code=302)

    @app.get("/api/hello")
    def hello() -> dict[str, str]:
        return {"message": "hello world"}

    @app.get("/")
    def root(request: Request) -> Response:
        if not request.session.get("authed"):
            return RedirectResponse(url="/login", status_code=302)

        index_file = frontend_root / "index.html"
        if not index_file.exists():
            return JSONResponse(
                status_code=503,
                content={"error": "frontend build missing", "path": str(index_file)},
            )
        return FileResponse(index_file)

    @app.get("/{requested_path:path}")
    def frontend_assets(requested_path: str) -> Response:
        if requested_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")

        safe_path = (frontend_root / requested_path).resolve()
        if safe_path != frontend_root and frontend_root not in safe_path.parents:
            raise HTTPException(status_code=404, detail="Not Found")

        if safe_path.is_dir():
            safe_path = safe_path / "index.html"

        if safe_path.exists() and safe_path.is_file():
            return FileResponse(safe_path)

        fallback_index = frontend_root / "index.html"
        if fallback_index.exists():
            return FileResponse(fallback_index)

        raise HTTPException(status_code=404, detail="Not Found")

    return app


app = create_app()
