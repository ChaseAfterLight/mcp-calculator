import logging
import os
import threading
import uuid
from pathlib import Path
from typing import Any, Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, field_validator

from mcp_servers.species_card_email_service import send_species_card_email
from mcp_servers.species_card_generator import generate_species_card
from mcp_servers.species_encyclopedia_mcp import (
    get_my_stats,
    get_species_detail,
    register_species,
    search_species,
)


load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("API_GATEWAY")

_TOOL_LOCK = threading.RLock()
_DEFAULT_CORS = "http://localhost:5173,http://localhost:8080"
_MAX_SEARCH_LIMIT = int(os.getenv("GATEWAY_MAX_SEARCH_LIMIT", "100"))


def _is_true(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _parse_cors_origins(raw_origins: str) -> list[str]:
    origins = [item.strip() for item in raw_origins.split(",") if item.strip()]
    return origins or ["*"]


def _error(status_code: int, code: str, message: str, details: Any = None) -> None:
    raise HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message, "details": details},
    )


def _ok(request: Request, data: Any) -> dict[str, Any]:
    return {"success": True, "trace_id": request.state.trace_id, "data": data}


def _run_locked(func, **kwargs):
    with _TOOL_LOCK:
        return func(**kwargs)


def _raise_if_tool_error(result: Any, code: str) -> None:
    if not isinstance(result, dict):
        _error(502, "MCP_DOWNSTREAM_ERROR", "MCP tool returned invalid result shape")

    error_msg = result.get("error")
    if error_msg:
        _error(400, code, str(error_msg), result)

    if result.get("success") is False:
        _error(400, code, str(result.get("message") or "Operation failed"), result)


class RegisterSpeciesRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    chinese_name: str = Field(..., min_length=1)
    latin_name: str = Field(..., min_length=1)
    features: list[str] = Field(..., min_length=1)
    category: Literal["plant", "animal", "mineral"] = "plant"
    habitat: str = ""
    observation_season: str = ""
    protection_level: str = ""
    fun_fact: str = ""
    rarity: int = Field(default=3, ge=1, le=5)
    user_id: str = "default"

    @field_validator("features")
    @classmethod
    def validate_features(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if isinstance(item, str) and item.strip()]
        if not cleaned:
            raise ValueError("features must contain at least one non-empty item")
        return cleaned


class GenerateCardRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    card_id: str | None = None
    chinese_name: str = Field(..., min_length=1)
    latin_name: str = Field(..., min_length=1)
    features: list[str] = Field(..., min_length=1)
    category: Literal["plant", "animal", "mineral"] = "plant"
    classification: dict[str, Any] | None = None
    habitat: str = ""
    observation_season: str = ""
    protection_level: str = ""
    fun_fact: str = ""
    image_path: str | None = None
    rarity: int = Field(default=3, ge=1, le=5)

    @field_validator("features")
    @classmethod
    def validate_features(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if isinstance(item, str) and item.strip()]
        if not cleaned:
            raise ValueError("features must contain at least one non-empty item")
        return cleaned


class SendCardEmailRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    card_id: str = Field(..., min_length=1)
    to_email: str = "13640292241@qq.com"
    email_subject: str | None = None
    email_body: str | None = None


class SendCardEmailByPathRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    to_email: str = "13640292241@qq.com"
    email_subject: str | None = None
    email_body: str | None = None


app = FastAPI(
    title="Species Encyclopedia API Gateway",
    description="Expose MCP abilities via HTTP APIs for frontend integration",
    version="0.1.0",
)

cards_dir = Path(__file__).parent / "cards"
cards_dir.mkdir(parents=True, exist_ok=True)
app.mount("/cards", StaticFiles(directory=str(cards_dir)), name="cards")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_cors_origins(os.getenv("GATEWAY_CORS_ORIGINS", _DEFAULT_CORS)),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def trace_middleware(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-Id") or uuid.uuid4().hex
    request.state.trace_id = trace_id
    response = await call_next(request)
    response.headers["X-Trace-Id"] = trace_id
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    trace_id = getattr(request.state, "trace_id", uuid.uuid4().hex)
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail and "message" in detail:
        error = detail
    else:
        error = {"code": "HTTP_ERROR", "message": str(detail), "details": None}
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "trace_id": trace_id, "error": error},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    trace_id = getattr(request.state, "trace_id", uuid.uuid4().hex)
    logger.exception("[%s] unhandled error: %s", trace_id, exc)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "trace_id": trace_id,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Unexpected server error",
                "details": None,
            },
        },
    )


@app.get("/health")
def health(request: Request):
    return _ok(request, {"status": "ok"})


@app.post("/api/species/register")
def api_register_species(payload: RegisterSpeciesRequest, request: Request):
    result = _run_locked(register_species, **payload.model_dump())
    _raise_if_tool_error(result, "MCP_REGISTER_ERROR")
    return _ok(request, result)


@app.post("/api/species/generate")
@app.post("/api/species/generate-card")
def api_generate_species_card(payload: GenerateCardRequest, request: Request):
    result = _run_locked(generate_species_card, **payload.model_dump())
    _raise_if_tool_error(result, "MCP_GENERATE_CARD_ERROR")
    return _ok(request, result)


@app.get("/api/species/search")
def api_search_species(
    request: Request,
    keyword: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=_MAX_SEARCH_LIMIT),
):
    result = _run_locked(search_species, keyword=keyword, limit=limit)
    _raise_if_tool_error(result, "MCP_SEARCH_ERROR")
    return _ok(request, result)


@app.get("/api/species/{card_id}")
def api_get_species_detail(card_id: str, request: Request):
    if not card_id.strip():
        _error(400, "INVALID_CARD_ID", "card_id cannot be empty")
    result = _run_locked(get_species_detail, card_id=card_id.strip())
    _raise_if_tool_error(result, "MCP_SPECIES_DETAIL_ERROR")
    return _ok(request, result)


@app.get("/api/users/{user_id}/stats")
def api_get_user_stats(user_id: str, request: Request):
    if not user_id.strip():
        _error(400, "INVALID_USER_ID", "user_id cannot be empty")
    result = _run_locked(get_my_stats, user_id=user_id.strip())
    _raise_if_tool_error(result, "MCP_STATS_ERROR")
    return _ok(request, result)


@app.post("/api/species/email")
def api_send_species_card_email(payload: SendCardEmailRequest, request: Request):
    result = _run_locked(send_species_card_email, **payload.model_dump())
    _raise_if_tool_error(result, "MCP_EMAIL_ERROR")
    return _ok(request, result)


@app.post("/api/species/{card_id}/email")
def api_send_species_card_email_by_path(
    card_id: str,
    payload: SendCardEmailByPathRequest,
    request: Request,
):
    if not card_id.strip():
        _error(400, "INVALID_CARD_ID", "card_id cannot be empty")
    result = _run_locked(
        send_species_card_email,
        card_id=card_id.strip(),
        to_email=payload.to_email,
        email_subject=payload.email_subject,
        email_body=payload.email_body,
    )
    _raise_if_tool_error(result, "MCP_EMAIL_ERROR")
    return _ok(request, result)


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("GATEWAY_HOST", "0.0.0.0")
    port = int(os.getenv("GATEWAY_PORT", "8000"))
    reload = _is_true(os.getenv("GATEWAY_RELOAD", "0"))
    uvicorn.run("api_gateway:app", host=host, port=port, reload=reload)
