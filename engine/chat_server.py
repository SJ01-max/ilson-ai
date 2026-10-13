"""웹 채팅 API — Anthropic tool use로 engine 도구를 호출해 답한다.

애드온 분리 원칙: ANTHROPIC_API_KEY 없으면 /chat만 503, 나머지 기능 무영향.
숫자는 반드시 도구로 조회 — 모델이 지어내지 못하게 system prompt·tool schema로 유도.

mode 처리: 프론트가 ChatRequest.mode 로 'demo' 또는 None 을 보낸다. 서버가 파일을 결정하고
    도구가 실행될 때만 선택된 forecast JSON 을 쓴다 — 모델에게 파일 선택권을 주지 않는다.
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
IDLE_FORECAST_DEMO = Path(__file__).resolve().parent.parent / "data" / "idle_forecast_demo.json"


def _forecast_path(mode: str | None) -> Path:
    return IDLE_FORECAST_DEMO if mode == "demo" else IDLE_FORECAST

def _system_prompt(mode: str | None = None) -> str:
    from datetime import date

    today = date.today()
    weekday = "월화수목금토일"[today.weekday()]
    demo_note = (
        "현재 모드는 '시연 데이터 기준'이다. 답변의 어딘가에 '시연 데이터 기준' 이라는 표현을 자연스럽게 포함해, "
        "담당자가 실데이터가 아닌 시연용 수치를 보고 있다는 사실을 인지하게 하라. "
        if mode == "demo"
        else ""
    )
    return (
        "너는 양주시 공공형 계절근로 배정 시스템의 안내 담당자다. "
        "숫자는 반드시 도구를 호출해 얻고, 도구 범위 밖 질문엔 "
        "'해당 정보는 시스템에 없습니다'라고 답한다. 간결한 한국어, 존댓말. "
        f"오늘은 {today.isoformat()}({weekday})이다. "
        "상대 날짜('내일'·'모레'·'다음 주 월요일' 등)는 오늘을 기준으로 해석해 YYYY-MM-DD로 환산한 뒤 도구에 넘긴다. "
        "'명일' 대신 '내일' 을 사용한다. "
        "연도 없이 '10월 14일' 같은 날짜가 주어지면 올해 또는 가장 가까운 미래 연도로 해석한다. "
        "유휴 예보 질문에는 먼저 get_idle_forecast를 호출하고, 질문의 기간 표현(다음 주/이번 주/이번 달 등)이 "
        "예보 기간과 달라도 거절하지 말 것. '현재 예보 기간은 M/D~M/D입니다'라고 밝힌 뒤 그 기간의 수치로 답할 것. "
        + demo_note
        + "용어 규칙: '손실'·'절감' 금지(가치 환산 추정이라 과대해석됨), 대신 '유휴 인건비 환산액'을 사용한다. "
        "도구 이름(get_idle_forecast 등)·내부 식별자를 사용자에게 노출하지 말 것. "
        "시스템에 없는 부서·연락처·담당자 전화번호 등을 지어내 안내하지 말 것. "
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


def _tool_get_idle_forecast(mode: str | None) -> dict:
    path = _forecast_path(mode)
    if not path.exists():
        return {"error": "forecast 미생성"}
    return json.loads(path.read_text(encoding="utf-8"))


def _run_tool(name: str, args: dict, mode: str | None) -> dict:
    if name == "get_idle_forecast":
        return _tool_get_idle_forecast(mode)
    if name == "get_assignments":
        return assign(args["date"])
    if name == "compare_scenario":
        return compare_scenario(args["workers"], args.get("start"), forecast_path=_forecast_path(mode))
    return {"error": f"알 수 없는 도구: {name}"}


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    mode: str | None = None  # 'demo' 면 시연용 강수 주간 JSON 참조. 모델이 아니라 서버가 결정.


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
        mode = req.mode if req.mode == "demo" else None

        messages = [{"role": m.role, "content": m.content} for m in req.messages]
        tool_used: list[str] = []
        total_input = 0
        total_output = 0

        # tool use 루프 — 모델이 end_turn 할 때까지 반복
        for _loop in range(6):  # 안전장치 (최대 6라운드)
            resp = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=_system_prompt(mode),
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
                    result = _run_tool(block.name, block.input or {}, mode)
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
