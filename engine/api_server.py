"""FastAPI 서버 — 계산은 engine 모듈 호출만, 응답 형식은 docs/interface.md §2·§3."""

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from assigner import assign

# forecast 모듈(forecast/idle.py) 산출물 — 기상청 API 키 의존을 피하려고 JSON만 읽는다
IDLE_FORECAST = Path(__file__).resolve().parent.parent / "data" / "idle_forecast.json"

app = FastAPI(title="일손배정 AI API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/forecast")
def get_forecast():
    if not IDLE_FORECAST.exists():
        raise HTTPException(
            status_code=503,
            detail="forecast 미생성 — python3 forecast/idle.py 먼저 실행",
        )
    return json.loads(IDLE_FORECAST.read_text(encoding="utf-8"))


@app.get("/assignments")
def get_assignments(date: str):
    return assign(date)
