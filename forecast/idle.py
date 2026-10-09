"""
내일부터 7일간 유휴 인력·손실 예보 → docs/interface.md 3번 JSON

- 입력: data/weekly_rain.csv (kma_api.py 결과), forecast/demand.py 의 필요 인원
    · --demo 이면 날씨만 data/demo_rain.csv (day 1~7 → rain_day) 고정값 사용 — 시연 날 비가 안 올 때 대비
- 날짜별: demand(반올림), supply = SUPPLY, idle = max(0, supply - demand), loss_krw = idle × DAILY_WAGE
- weather: rain_day 이면 '비', 아니면 '맑음'
- 출력: data/idle_forecast.json

사용법 (레포 루트에서):
    python forecast/idle.py [시작일 YYYY-MM-DD]   (생략 시 한국시간 기준 내일)
    python forecast/idle.py --demo                (날짜는 내일부터 7일, 날씨는 demo_rain.csv)
"""
import sys, json
from pathlib import Path
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
import pandas as pd
from demand import daily_demand

ROOT = Path(__file__).resolve().parents[1]      # 레포 루트 (ilson-ai/)
RAIN = ROOT / "data" / "weekly_rain.csv"
DEMO_RAIN = ROOT / "data" / "demo_rain.csv"
OUT = ROOT / "data" / "idle_forecast.json"
KST = ZoneInfo("Asia/Seoul")

# ---- 설정 ----
SUPPLY = 20                 # 보유 근로자 수 (명)
DAILY_WAGE = 100_000        # 1인 일당 (원) — 유휴 1명당 손실


def tomorrow():
    return datetime.now(KST).date() + timedelta(days=1)


def load_rain(week_start, demo):
    """7일치 날짜 → rain_day(bool) dict"""
    dates = [(week_start + timedelta(days=i)).isoformat() for i in range(7)]
    if demo:
        rain = pd.read_csv(DEMO_RAIN, encoding="utf-8-sig").set_index("day").rain_day
        return {d: bool(rain[i + 1]) for i, d in enumerate(dates)}
    rain = pd.read_csv(RAIN, encoding="utf-8-sig").set_index("date").rain_day
    for d in dates:
        if d not in rain.index:
            sys.exit(f"{RAIN.name} 에 {d} 예보가 없습니다. python forecast/kma_api.py 를 먼저 실행하세요.")
    return {d: bool(rain[d]) for d in dates}


def main():
    args = sys.argv[1:]
    demo = "--demo" in args
    args = [a for a in args if a != "--demo"]
    week_start = tomorrow() if demo or not args else date.fromisoformat(args[0])
    if demo:
        print(f"⚠ 데모 데이터 모드 ({DEMO_RAIN.name})\n")
    days = []
    for d, is_rain in load_rain(week_start, demo).items():
        demand = round(daily_demand(d, is_rain))
        idle = max(0, SUPPLY - demand)
        days.append(dict(date=d, weather="비" if is_rain else "맑음", demand=demand,
                         supply=SUPPLY, idle=idle, loss_krw=idle * DAILY_WAGE))
    result = dict(week_start=week_start.isoformat(), days=days,
                  week_total=dict(idle=sum(x["idle"] for x in days),
                                  loss_krw=sum(x["loss_krw"] for x in days)))
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(pd.DataFrame(days).to_string(index=False))
    print(f"\n주간 합계: 유휴 {result['week_total']['idle']}명·일, 손실 {result['week_total']['loss_krw']:,}원")
    print(f"→ {OUT} 저장")
    if demo:
        print("\n" + "=" * 60)
        print(f"⚠ 데모 데이터: 날씨는 실제 예보가 아닌 {DEMO_RAIN.name} 고정값입니다")
        print("=" * 60)


if __name__ == "__main__":
    main()
