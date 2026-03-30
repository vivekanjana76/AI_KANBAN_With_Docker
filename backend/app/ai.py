import json
import os
from pathlib import Path
from typing import Literal

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.board import BoardPayload

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "openai/gpt-oss-120b:free"
OPENROUTER_TIMEOUT_SECONDS = 30.0


class AIServiceError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ChatHistoryMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)


class AIChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1)
    history: list[ChatHistoryMessage] = Field(default_factory=list)
    board: BoardPayload | None = None


class AIModelResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assistant_message: str = Field(min_length=1)
    board_update: BoardPayload | None = None


class AIChatResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assistant_message: str
    board: BoardPayload
    board_updated: bool


class AITestResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assistant_message: str
    model: str


def _require_openrouter_api_key() -> str:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise AIServiceError("OPENROUTER_API_KEY is not configured", status_code=503)
    return api_key


def _json_schema_payload() -> dict:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "pm_ai_response",
            "strict": True,
            "schema": AIModelResponse.model_json_schema(),
        },
    }


def _json_object_payload() -> dict:
    return {"type": "json_object"}


def _build_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_require_openrouter_api_key()}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-OpenRouter-Title": "Project Management MVP",
    }


def _build_structured_messages(
    prompt: str, history: list[ChatHistoryMessage], board: dict
) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": (
                "You are an assistant for a single-user kanban board. "
                "Always respond with valid JSON matching the requested schema. "
                "Keep assistant_message concise and practical. "
                "Cards can include metadata such as assignee, dueDate, priority, and labels. "
                "Only include board_update when the user explicitly asks to create, edit, rename, "
                "delete, or move cards/columns. When board_update is included, return the full "
                "replacement board document, not a patch."
            ),
        }
    ]
    messages.extend(message.model_dump(mode="python") for message in history)
    messages.append(
        {
            "role": "user",
            "content": (
                f"Current board JSON:\n{json.dumps(board, ensure_ascii=False)}\n\n"
                f"User request:\n{prompt}"
            ),
        }
    )
    return messages


def _extract_message_content(data: dict) -> str:
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise AIServiceError("OpenRouter returned an unexpected response shape") from exc

    if not isinstance(content, str) or not content.strip():
        raise AIServiceError("OpenRouter returned empty content")

    return content


def _coerce_json_text(content: str) -> str:
    stripped = content.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped

    if "```" in stripped:
        parts = stripped.split("```")
        for part in parts:
            candidate = part.strip()
            if candidate.startswith("json"):
                candidate = candidate[4:].strip()
            if candidate.startswith("{") and candidate.endswith("}"):
                return candidate

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1 and start < end:
        return stripped[start : end + 1]

    return stripped


def _parse_structured_response(content: str) -> AIModelResponse:
    try:
        return AIModelResponse.model_validate_json(_coerce_json_text(content))
    except ValidationError as exc:
        raise AIServiceError("AI returned invalid structured output") from exc


def _extract_upstream_error(response: httpx.Response) -> str:
    try:
        data = response.json()
    except ValueError:
        text = response.text.strip()
        return text or f"OpenRouter request failed with status {response.status_code}"

    error = data.get("error")
    if isinstance(error, dict) and isinstance(error.get("message"), str):
        return error["message"]
    if isinstance(error, str):
        return error

    return f"OpenRouter request failed with status {response.status_code}"


async def _post_openrouter_completion(body: dict) -> dict:
    try:
        async with httpx.AsyncClient(timeout=OPENROUTER_TIMEOUT_SECONDS) as client:
            response = await client.post(OPENROUTER_URL, headers=_build_headers(), json=body)
    except httpx.TimeoutException as exc:
        raise AIServiceError("AI request timed out", status_code=504) from exc
    except httpx.HTTPError as exc:
        raise AIServiceError("Unable to reach OpenRouter") from exc

    if response.status_code >= 400:
        raise AIServiceError(_extract_upstream_error(response), status_code=502)

    return response.json()


async def request_openrouter_structured_response(
    prompt: str, history: list[ChatHistoryMessage], board: dict
) -> AIModelResponse:
    messages = _build_structured_messages(prompt, history, board)
    request_bodies = [
        {
            "model": OPENROUTER_MODEL,
            "messages": messages,
            "response_format": _json_schema_payload(),
            "temperature": 0,
            "provider": {"require_parameters": True},
        },
        {
            "model": OPENROUTER_MODEL,
            "messages": messages,
            "response_format": _json_object_payload(),
            "temperature": 0,
            "plugins": [{"id": "response-healing"}],
        },
        {
            "model": OPENROUTER_MODEL,
            "messages": messages
            + [
                {
                    "role": "user",
                    "content": (
                        "Return only a valid JSON object with keys assistant_message and board_update. "
                        "Do not include markdown fences or any extra text."
                    ),
                }
            ],
            "response_format": _json_object_payload(),
            "temperature": 0,
            "plugins": [{"id": "response-healing"}],
        },
    ]

    last_error: AIServiceError | None = None
    for body in request_bodies:
        try:
            data = await _post_openrouter_completion(body)
        except AIServiceError as exc:
            last_error = exc
            if "No endpoints found" in exc.message:
                continue
            raise

        try:
            return _parse_structured_response(_extract_message_content(data))
        except AIServiceError as exc:
            last_error = exc
            continue

    if last_error is not None:
        raise last_error

    raise AIServiceError("AI request failed")


async def request_openrouter_test_response(prompt: str) -> str:
    body = {
        "model": OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 120,
    }

    return _extract_message_content(await _post_openrouter_completion(body))
