"""FastAPI 서버 — 계산은 engine 모듈 호출만, 응답 형식은 docs/interface.md §2·§3."""

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from assigner import assign

MOCK_FORECAST = Path(__file__).resolve().parent.parent / "dashboard" / "src" / "mock" / "forecast.json"

app = FastAPI(title="일손배정 AI API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# 통합일(10/12)에 forecast 모듈 호출로 교체
@app.get("/forecast")
def get_forecast():
    return json.loads(MOCK_FORECAST.read_text(encoding="utf-8"))


@app.get("/assignments")
def get_assignments(date: str):
    return assign(date)
