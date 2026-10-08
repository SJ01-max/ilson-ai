"""
다음 주(월~일) 유휴 인력·손실 예보 → docs/interface.md 3번 JSON

- 입력: data/weekly_rain.csv (kma_api.py 결과), forecast/demand.py 의 필요 인원
- 날짜별: demand(반올림), supply = SUPPLY, idle = max(0, supply - demand), loss_krw = idle × DAILY_WAGE
- weather: rain_day 이면 '비', 아니면 '맑음'
- 출력: data/idle_forecast.json

사용법 (레포 루트에서):  python forecast/idle.py [주 시작일 YYYY-MM-DD]   (생략 시 한국시간 기준 다음 주 월요일)
"""
import sys, json
from pathlib import Path
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
import pandas as pd
from demand import daily_demand

ROOT = Path(__file__).resolve().parents[1]      # 레포 루트 (ilson-ai/)
RAIN = ROOT / "data" / "weekly_rain.csv"
OUT = ROOT / "data" / "idle_forecast.json"
KST = ZoneInfo("Asia/Seoul")

# ---- 설정 ----
SUPPLY = 20                 # 보유 근로자 수 (명)
DAILY_WAGE = 100_000        # 1인 일당 (원) — 유휴 1명당 손실


def next_monday(today):
    return today + timedelta(days=7 - today.weekday())


def main():
    week_start = (date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1
                  else next_monday(datetime.now(KST).date()))
    rain = pd.read_csv(RAIN, encoding="utf-8-sig").set_index("date").rain_day
    days = []
    for i in range(7):
        d = (week_start + timedelta(days=i)).isoformat()
        if d not in rain.index:
            sys.exit(f"{RAIN.name} 에 {d} 예보가 없습니다. python forecast/kma_api.py 를 먼저 실행하세요.")
        is_rain = bool(rain[d])
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


if __name__ == "__main__":
    main()
