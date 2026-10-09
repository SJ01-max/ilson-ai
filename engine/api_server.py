"""FastAPI 서버 — 계산은 engine 모듈 호출만, 응답 형식은 docs/interface.md §2·§3."""

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

IDLE_FORECAST = Path(__file__).resolve().parent.parent / "data" / "idle_forecast.json"
AUTH_MOCK = Path(__file__).resolve().parent / "auth_mock.json"
ITERATIONS = 260_000

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
def get_forecast(_: Annotated[str, Depends(require_auth)]):
    if not IDLE_FORECAST.exists():
        raise HTTPException(
            status_code=503,
            detail="forecast 미생성 — python3 forecast/idle.py 먼저 실행",
        )
    return json.loads(IDLE_FORECAST.read_text(encoding="utf-8"))


@app.get("/assignments")
def get_assignments(date: str, _: Annotated[str, Depends(require_auth)]):
    return assign(date)
