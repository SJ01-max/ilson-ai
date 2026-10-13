"""웹 채팅 API — Anthropic tool use로 engine 도구를 호출해 답한다.

애드온 분리 원칙: ANTHROPIC_API_KEY 없으면 /chat만 503, 나머지 기능 무영향.
숫자는 반드시 도구로 조회 — 모델이 지어내지 못하게 system prompt·tool schema로 유도.
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from scenario import compare as compare_scenario
from assigner import assign

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# 사용자 지시는 claude-sonnet-4-5였으나 현재 조직 모델 리스트에 없어(retire), 가장 가까운 상위 모델 사용
MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 1000
IDLE_FORECAST = Path(__file__).resolve().parent.parent / "data" / "idle_forecast.json"

def _system_prompt() -> str:
    from datetime import date

    today = date.today()
    weekday = "월화수목금토일"[today.weekday()]
    return (
        "너는 양주시 공공형 계절근로 배정 시스템의 안내 담당자다. "
        "숫자는 반드시 도구를 호출해 얻고, 도구 범위 밖 질문엔 "
        "'해당 정보는 시스템에 없습니다'라고 답한다. 간결한 한국어, 존댓말. "
        f"오늘은 {today.isoformat()}({weekday})이다. "
        "상대 날짜('내일'·'모레'·'다음 주 월요일' 등)는 오늘을 기준으로 해석해 YYYY-MM-DD로 환산한 뒤 도구에 넘긴다. "
        "연도 없이 '10월 14일' 같은 날짜가 주어지면 올해 또는 가장 가까운 미래 연도로 해석한다. "
        "유휴 예보 질문에는 먼저 get_idle_forecast를 호출하고, 질문의 기간 표현(다음 주/이번 주/이번 달 등)이 "
        "예보 기간과 달라도 거절하지 말 것. '현재 예보 기간은 M/D~M/D입니다'라고 밝힌 뒤 그 기간의 수치로 답할 것. "
        "출력은 플레인 텍스트로만. 마크다운 금지(별표 **, 샵 #, 백틱 `, 하이픈 글머리표 모두 쓰지 말 것). "
        "강조가 필요하면 숫자와 단위를 그대로 쓰고, 목록은 '1) 2) 3)' 또는 줄바꿈만 사용."
    )

TOOLS = [
    {
        "name": "get_idle_forecast",
        "description": (
            "이번 주 유휴 인력 예보를 조회한다. 날짜별 날씨·수요·공급·유휴·"
            "유휴 인건비 환산액과 주간 합계가 필요할 때 사용한다."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_assignments",
        "description": (
            "특정 날짜의 근로자-농가 배정안을 조회한다. 어느 농가에 누구를 몇 점으로 "
            "보낼지, 미배정·부족 농가가 궁금할 때 사용한다."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "YYYY-MM-DD"},
            },
            "required": ["date"],
        },
    },
    {
        "name": "compare_scenario",
        "description": (
            "입국 인원·시기를 바꿨을 때 유휴·수요 미충족(unmet)·유휴 인건비 환산액 변화를 비교한다. "
            "utilization이 1.00이어도 unmet>0이면 수요 미충족이다."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "workers": {"type": "integer", "description": "5~50"},
                "start": {
                    "type": ["string", "null"],
                    "description": "YYYY-MM-DD 또는 생략",
                },
            },
            "required": ["workers"],
        },
    },
]


def _tool_get_idle_forecast() -> dict:
    if not IDLE_FORECAST.exists():
        return {"error": "forecast 미생성"}
    return json.loads(IDLE_FORECAST.read_text(encoding="utf-8"))


def _run_tool(name: str, args: dict) -> dict:
    if name == "get_idle_forecast":
        return _tool_get_idle_forecast()
    if name == "get_assignments":
        return assign(args["date"])
    if name == "compare_scenario":
        return compare_scenario(args["workers"], args.get("start"))
    return {"error": f"알 수 없는 도구: {name}"}


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


def _get_client():
    """키 없으면 503. 가져올 때마다 환경을 확인해 키 제거/복원이 즉시 반영되게 한다."""
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise HTTPException(status_code=503, detail="AI 질의 기능이 설정되지 않았습니다")
    from anthropic import Anthropic

    return Anthropic(api_key=key)


def build_router(require_auth) -> APIRouter:
    router = APIRouter()

    @router.post("/chat")
    def chat(req: ChatRequest, _=Depends(require_auth)):
        client = _get_client()

        messages = [{"role": m.role, "content": m.content} for m in req.messages]
        tool_used: list[str] = []
        total_input = 0
        total_output = 0

        # tool use 루프 — 모델이 end_turn 할 때까지 반복
        for _loop in range(6):  # 안전장치 (최대 6라운드)
            resp = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=_system_prompt(),
                tools=TOOLS,
                messages=messages,
            )
            total_input += resp.usage.input_tokens
            total_output += resp.usage.output_tokens

            if resp.stop_reason == "end_turn":
                reply = "".join(b.text for b in resp.content if b.type == "text")
                return {
                    "reply": reply.strip(),
                    "tool_used": tool_used,
                    "usage": {
                        "input_tokens": total_input,
                        "output_tokens": total_output,
                    },
                }

            if resp.stop_reason != "tool_use":
                raise HTTPException(
                    status_code=502,
                    detail=f"예상치 못한 stop_reason: {resp.stop_reason}",
                )

            messages.append({"role": "assistant", "content": [b.model_dump() for b in resp.content]})
            tool_results = []
            for block in resp.content:
                if block.type != "tool_use":
                    continue
                tool_used.append(block.name)
                try:
                    result = _run_tool(block.name, block.input or {})
                    result_text = json.dumps(result, ensure_ascii=False)
                    is_error = False
                except Exception as e:
                    result_text = f"도구 실행 실패: {e}"
                    is_error = True
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_text,
                    "is_error": is_error,
                })
            messages.append({"role": "user", "content": tool_results})

        raise HTTPException(status_code=502, detail="도구 호출 루프 상한 초과")

    return router
