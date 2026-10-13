"""FastAPI 서버 — 계산은 engine 모듈 호출만, 응답 형식은 docs/interface.md §2·§3·§5.

/forecast·/scenario의 loss_krw는 유휴 인건비 환산액(유휴 인일 × 일당 10만 원)이다.
"""

import base64
import hashlib
import json
import secrets
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from assigner import assign
from scenario import compare as compare_scenario
from chat_server import build_router as build_chat_router

IDLE_FORECAST = Path(__file__).resolve().parent.parent / "data" / "idle_forecast.json"
IDLE_FORECAST_DEMO = Path(__file__).resolve().parent.parent / "data" / "idle_forecast_demo.json"
AUTH_MOCK = Path(__file__).resolve().parent / "auth_mock.json"
ITERATIONS = 260_000


def _forecast_path(mode: str | None) -> Path:
    """mode=demo면 시연용 강수 주간(54인일), 아니면 실데이터(42인일)."""
    return IDLE_FORECAST_DEMO if mode == "demo" else IDLE_FORECAST

app = FastAPI(title="일손배정 AI API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 메모리 세션 저장소: token -> display_name
_sessions: dict[str, str] = {}
_bearer = HTTPBearer(auto_error=False)


def _load_account() -> dict:
    return json.loads(AUTH_MOCK.read_text(encoding="utf-8"))


def require_auth(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> str:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="인증이 필요합니다.")
    token = credentials.credentials
    if token not in _sessions:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 토큰입니다.")
    return _sessions[token]


class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/login")
def login(req: LoginRequest):
    account = _load_account()
    if req.username != account["username"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="아이디 또는 비밀번호가 올바르지 않습니다.")
    salt = base64.b64decode(account["salt"])
    dk = hashlib.pbkdf2_hmac("sha256", req.password.encode(), salt, ITERATIONS)
    if dk.hex() != account["password_hash"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="아이디 또는 비밀번호가 올바르지 않습니다.")
    token = secrets.token_urlsafe()
    _sessions[token] = account["display_name"]
    return {"token": token, "display_name": account["display_name"]}


@app.post("/logout")
def logout(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]):
    if credentials:
        _sessions.pop(credentials.credentials, None)
    return {"message": "로그아웃 완료"}


@app.get("/forecast")
def get_forecast(
    _: Annotated[str, Depends(require_auth)],
    mode: str | None = None,
):
    path = _forecast_path(mode)
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail=f"forecast 미생성 — python3 forecast/idle.py{' --demo' if mode == 'demo' else ''} 먼저 실행",
        )
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/assignments")
def get_assignments(
    date: str,
    _: Annotated[str, Depends(require_auth)],
    mode: str | None = None,  # 수용만 (배정은 requests.csv 기반이라 mode 무영향 — 일관성 유지용)
    fair: int = 0,  # 1 이면 요청 농가 최소 1명 보장 (QA-10, 실 데이터에선 효과 0 — docs/fairness-test.md)
):
    return assign(date, fair=bool(fair))


@app.get("/scenario")
def get_scenario(
    workers: int,
    _: Annotated[str, Depends(require_auth)],
    start: str | None = None,
    mode: str | None = None,
):
    try:
        return compare_scenario(workers, start, forecast_path=_forecast_path(mode))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# 애드온: ANTHROPIC_API_KEY 없으면 /chat 요청만 503, 나머지 기능 무영향
app.include_router(build_chat_router(require_auth))
