"""시나리오 비교 — 입국 인원·시기 변경 시 주간 유휴·손실 변화.

응답 형식: docs/interface.md §5.
수요는 forecast(§3)의 보정값을 그대로 재사용 — 이중 계산 금지.
"""

import json
from pathlib import Path

IDLE_FORECAST = Path(__file__).resolve().parent.parent / "data" / "idle_forecast.json"
BASE_WORKERS = 20
WAGE_KRW = 100_000
WORKERS_MIN = 5
WORKERS_MAX = 50


def _load_forecast() -> dict:
    if not IDLE_FORECAST.exists():
        raise FileNotFoundError(
            "forecast 미생성 — python3 forecast/idle.py 먼저 실행",
        )
    return json.loads(IDLE_FORECAST.read_text(encoding="utf-8"))


def _week_totals(days: list[dict], workers_by_date: dict[str, int]) -> dict:
    """일별 공급을 받아 주간 idle·loss·utilization 집계."""
    idle_total = 0
    supply_total = 0
    used_total = 0  # 투입인일 = min(supply, demand)
    for d in days:
        supply = workers_by_date[d["date"]]
        demand = d["demand"]
        idle_total += max(supply - demand, 0)
        supply_total += supply
        used_total += min(supply, demand)
    utilization = round(used_total / supply_total, 2) if supply_total else 0.0
    return {
        "idle": idle_total,
        "loss_krw": idle_total * WAGE_KRW,
        "utilization": utilization,
    }


def _supply_per_day(days: list[dict], workers: int, start: str | None) -> dict[str, int]:
    """start 규칙에 따라 날짜별 공급(명) 매핑.

    - start=None 또는 주 시작 이전 → 전 날짜 workers.
    - start가 주 중간 → start 이후(포함) workers, 이전은 BASE_WORKERS.
    - start가 주 끝 이후 → 전 날짜 BASE_WORKERS (주간 영향 없음).
    """
    dates = [d["date"] for d in days]
    if start is None or start <= dates[0]:
        return {date: workers for date in dates}
    if start > dates[-1]:
        return {date: BASE_WORKERS for date in dates}
    return {date: (workers if date >= start else BASE_WORKERS) for date in dates}


def compare(workers: int, start: str | None) -> dict:
    """입국 인원·시기 변경 시나리오를 base(20명)와 비교.

    workers: 시나리오 공급 인원 (5~50).
    start: 추가 투입 시작일 YYYY-MM-DD 또는 None. None이면 주 전체 workers 적용.

    반환: docs/interface.md §5 형식.
    """
    if not isinstance(workers, int) or workers < WORKERS_MIN or workers > WORKERS_MAX:
        raise ValueError(
            f"workers는 {WORKERS_MIN}~{WORKERS_MAX} 범위여야 합니다 (받은 값: {workers})",
        )

    forecast = _load_forecast()
    days = forecast["days"]

    base_supply = {d["date"]: BASE_WORKERS for d in days}
    scenario_supply = _supply_per_day(days, workers, start)

    base_totals = _week_totals(days, base_supply)
    scenario_totals = _week_totals(days, scenario_supply)

    return {
        "base": {
            "workers": BASE_WORKERS,
            "start": None,
            **base_totals,
        },
        "scenario": {
            "workers": workers,
            "start": start,
            **scenario_totals,
        },
        "diff": {
            "idle": scenario_totals["idle"] - base_totals["idle"],
            "loss_krw": scenario_totals["loss_krw"] - base_totals["loss_krw"],
        },
    }
