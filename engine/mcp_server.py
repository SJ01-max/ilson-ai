"""MCP 서버 (stdio) — 계산은 engine 모듈 호출만."""

import json
from pathlib import Path

from mcp.server.mcpserver import MCPServer

from assigner import assign

MOCK_FORECAST = Path(__file__).resolve().parent.parent / "dashboard" / "src" / "mock" / "forecast.json"

mcp = MCPServer("ilson-ai")


# 통합일(10/12)에 forecast 모듈 호출로 교체
@mcp.tool()
def get_idle_forecast() -> dict:
    """이번 주 유휴 인력 예보를 조회한다.

    날짜별 날씨·필요 인력(demand)·보유 인력(supply)·유휴 인원(idle)·예상 손실액(loss_krw)과
    주간 합계가 필요할 때 사용한다. 응답 형식: docs/interface.md §3.
    """
    return json.loads(MOCK_FORECAST.read_text(encoding="utf-8"))


@mcp.tool()
def get_assignments(date: str) -> dict:
    """특정 날짜의 근로자-농가 배정안을 생성한다.

    어떤 근로자를 어느 농가에 몇 점 근거로 보낼지, 미배정 인력과 인력 부족 농가가
    궁금할 때 사용한다. date는 YYYY-MM-DD 형식. 응답 형식: docs/interface.md §2.
    """
    return assign(date)


@mcp.tool()
def compare_scenario(workers: int, start: str) -> dict:
    """입국 인원·추가 투입 시기를 바꿨을 때의 유휴·손실 변화를 비교한다.

    workers는 입국 인원(명), start는 투입 시작일(YYYY-MM-DD).
    """
    return {"status": "엔진 준비 중", "workers": workers, "start": start}


if __name__ == "__main__":
    mcp.run()
