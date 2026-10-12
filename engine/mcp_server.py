"""MCP 서버 (stdio) — 계산은 engine 모듈 호출만."""

import json
from pathlib import Path

from mcp.server.mcpserver import MCPServer

from assigner import assign
from scenario import compare

# forecast 모듈(forecast/idle.py) 산출물 — 기상청 API 키 의존을 피하려고 JSON만 읽는다
IDLE_FORECAST = Path(__file__).resolve().parent.parent / "data" / "idle_forecast.json"

mcp = MCPServer("ilson-ai")


@mcp.tool()
def get_idle_forecast() -> dict:
    """이번 주 유휴 인력 예보를 조회한다.

    날짜별 날씨·필요 인력(demand)·보유 인력(supply)·유휴 인원(idle)·유휴 인건비 환산액(loss_krw,
    idle × 일당 10만 원)과 주간 합계가 필요할 때 사용한다. 응답 형식: docs/interface.md §3.
    """
    if not IDLE_FORECAST.exists():
        return {"error": "forecast 미생성 — python3 forecast/idle.py 먼저 실행"}
    return json.loads(IDLE_FORECAST.read_text(encoding="utf-8"))


@mcp.tool()
def get_assignments(date: str) -> dict:
    """특정 날짜의 근로자-농가 배정안을 생성한다.

    어떤 근로자를 어느 농가에 몇 점 근거로 보낼지, 미배정 인력과 인력 부족 농가가
    궁금할 때 사용한다. date는 YYYY-MM-DD 형식. 응답 형식: docs/interface.md §2.
    """
    return assign(date)


@mcp.tool()
def compare_scenario(workers: int, start: str | None = None) -> dict:
    """입국 인원·시기를 바꿨을 때 유휴·부족·유휴 인건비 환산액 변화를 비교한다.

    workers는 입국 인원(명, 5~50), start는 추가 투입 시작일(YYYY-MM-DD) 또는 생략.
    수요는 §3 예보 보정값을 재사용한다. unmet>0이면 수요 미충족(utilization과 함께 확인).
    응답 형식: docs/interface.md §5.
    """
    return compare(workers, start)


if __name__ == "__main__":
    mcp.run()
