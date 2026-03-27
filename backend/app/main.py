from contextlib import asynccontextmanager
from pathlib import Path
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response
from starlette.middleware.sessions import SessionMiddleware

from app.ai import (
    AIChatRequest,
    AIChatResponse,
    AIServiceError,
    AITestResponse,
    request_openrouter_structured_response,
    request_openrouter_test_response,
)
from app.board import BoardPayload, BoardResponse, default_board
from app.db import get_board, init_db, upsert_board

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


def require_authenticated_username(request: Request) -> str:
    if not request.session.get("authed"):
        raise HTTPException(status_code=401, detail="Authentication required")

    username = request.session.get("username")
    if not isinstance(username, str) or not username:
        raise HTTPException(status_code=401, detail="Authentication required")

    return username


def load_or_create_board(username: str) -> dict:
    board = get_board(username)
    if board is not None:
        return board

    board = default_board()
    upsert_board(username, board)
    return board


def create_app(frontend_dist: Path | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI):
        init_db()
        yield

    app = FastAPI(title="Project Management MVP API", lifespan=lifespan)
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
            request.session["username"] = username
            return RedirectResponse(url="/", status_code=302)

        return render_login_page("Invalid username/password", status_code=401)

    @app.get("/logout")
    def do_logout(request: Request) -> Response:
        request.session.clear()
        return RedirectResponse(url="/login", status_code=302)

    @app.get("/api/hello")
    def hello() -> dict[str, str]:
        return {"message": "hello world"}

    @app.get("/api/board", response_model=BoardResponse)
    def read_board(request: Request) -> BoardResponse:
        username = require_authenticated_username(request)
        return BoardResponse(board=BoardPayload.model_validate(load_or_create_board(username)))

    @app.put("/api/board", response_model=BoardResponse)
    def replace_board(payload: BoardPayload, request: Request) -> BoardResponse:
        username = require_authenticated_username(request)
        board = payload.model_dump(mode="python")
        upsert_board(username, board)
        return BoardResponse(board=payload)

    @app.get("/api/ai/test", response_model=AITestResponse)
    async def ai_test(request: Request, prompt: str = "2+2") -> AITestResponse:
        require_authenticated_username(request)
        try:
            assistant_message = await request_openrouter_test_response(prompt)
        except AIServiceError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

        return AITestResponse(
            assistant_message=assistant_message,
            model="openai/gpt-oss-120b:free",
        )

    @app.post("/api/ai/chat", response_model=AIChatResponse)
    async def ai_chat(payload: AIChatRequest, request: Request) -> AIChatResponse:
        username = require_authenticated_username(request)
        if payload.board is not None:
            current_board = payload.board.model_dump(mode="python")
            upsert_board(username, current_board)
        else:
            current_board = load_or_create_board(username)

        try:
            ai_response = await request_openrouter_structured_response(
                payload.message,
                payload.history,
                current_board,
            )
        except AIServiceError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

        next_board = (
            ai_response.board_update.model_dump(mode="python")
            if ai_response.board_update is not None
            else current_board
        )

        if ai_response.board_update is not None:
            upsert_board(username, next_board)

        return AIChatResponse(
            assistant_message=ai_response.assistant_message,
            board=BoardPayload.model_validate(next_board),
            board_updated=ai_response.board_update is not None,
        )

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
