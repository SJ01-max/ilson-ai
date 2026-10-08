"""
양주시 날짜별 필요 인원(demand) 계산 — 유휴 예보 입력용

- 면적: data/KOSIS/ 2025 농림어업총조사 양주시 작목 통계 (ha → 10a 로 환산, 1ha = 10 × 10a)
    · vegetable.csv : 노지 작목. 읍면 구분 없음 → '양주시(읍면 미구분)' 한 덩어리
    · facility.csv  : 시설 작목. 읍면별 행 사용
    · fruit.csv     : 과수. 읍면별 행 사용, 노지로 간주
- 작업 강도: forecast/crop_calendar.csv (작목·월별 10a당 하루 필요 인원. 현재 전부 '가정값')
- 필요 인원 = Σ(작목 면적[10a] × 그 달 10a당 필요 인원) × 담당 비율
    담당 비율 = PUBLIC_FARMS ÷ 양주시 해당 농가 수 (달력에 있는 작목들의 농가 수 합)
- 비 오는 날: 노지 작목(과수 포함) 0, 시설 작목은 그대로

사용법 (레포 루트에서):  python forecast/demand.py [YYYY-MM-DD]   → 작목·읍면별 내역 출력
"""
import sys
from pathlib import Path
from datetime import date
from functools import lru_cache
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]      # 레포 루트 (ilson-ai/)
KOSIS = ROOT / "data" / "KOSIS"
CALENDAR = Path(__file__).resolve().parent / "crop_calendar.csv"

# ---- 설정 ----
PUBLIC_FARMS = 50           # 공공형 계절근로 담당 농가 수

CITY = "양주시"
NO_TOWN = "양주시(읍면 미구분)"
SOURCES = [("vegetable.csv", "노지"), ("facility.csv", "시설"), ("fruit.csv", "노지")]


@lru_cache
def load_calendar():
    return pd.read_csv(CALENDAR)


@lru_cache
def load_areas():
    """KOSIS 3개 파일 → township, crop, field_type, area_10a, city_farms 표 (달력에 있는 작목만)."""
    cal = load_calendar()
    wanted = set(zip(cal.crop, cal.field_type))
    rows = []
    for fname, ftype in SOURCES:
        df = pd.read_csv(KOSIS / fname, header=1)                  # 1행은 연도(2025)뿐이라 건너뜀
        df = df[df["특성별"] == "계"].set_index("행정구역별").drop(columns="특성별")
        df = df.replace("-", 0).astype(int)                         # '-' = 0 또는 표시단위(1ha) 미만
        towns = [t for t in df.index if t not in ("경기도", CITY)]
        cols = list(df.columns)
        for farm_col, area_col in zip(cols[::2], cols[1::2]):      # (농가, 면적) 열이 쌍으로 나옴
            if "_면적" not in area_col:                             # 과수 전체 합계 열은 제외
                continue
            crop = area_col.split("_면적")[0]
            if (crop, ftype) not in wanted:
                continue
            for t in towns or [CITY]:
                rows.append(dict(township=t if towns else NO_TOWN, crop=crop, field_type=ftype,
                                 area_10a=df.loc[t, area_col] * 10,
                                 city_farms=df.loc[CITY, farm_col]))
    areas = pd.DataFrame(rows)
    missing = wanted - set(zip(areas.crop, areas.field_type))
    if missing:
        sys.exit(f"crop_calendar.csv 작목이 KOSIS 파일에 없음: {sorted(missing)}")
    return areas


def share_ratio():
    """담당 비율 = PUBLIC_FARMS ÷ 양주시 해당 농가 수. (비율, 농가 수) 반환."""
    farms = load_areas().drop_duplicates(["crop", "field_type"]).city_farms.sum()
    return PUBLIC_FARMS / farms, int(farms)


def demand_breakdown(day, rain):
    """읍면·작목별 필요 인원 표. day: 'YYYY-MM-DD', rain: 비 오는 날 여부."""
    month = date.fromisoformat(day).month
    cal = load_calendar()
    cal = cal[cal.month == month][["crop", "field_type", "workers_per_10a"]]
    df = load_areas().merge(cal, on=["crop", "field_type"])
    df["need"] = df.area_10a * df.workers_per_10a * share_ratio()[0]
    if rain:
        df.loc[df.field_type == "노지", "need"] = 0.0
    return df


def daily_demand(day, rain):
    """그날 공공형 담당분 필요 인원 (소수). 반올림은 호출하는 쪽에서."""
    return float(demand_breakdown(day, rain).need.sum())


def main():
    day = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()
    ratio, farms = share_ratio()
    print(f"{day} | 담당 비율 = {PUBLIC_FARMS} ÷ {farms} = {ratio:.4f}\n")
    sunny, rainy = demand_breakdown(day, False), demand_breakdown(day, True)
    by_crop = sunny.groupby(["crop", "field_type"]).agg(
        area_10a=("area_10a", "sum"), workers_per_10a=("workers_per_10a", "first"),
        need_sunny=("need", "sum")).sort_values("need_sunny", ascending=False)
    print(by_crop.round(2).to_string())
    print("\n읍면별 (맑은 날):")
    print(sunny.groupby("township").need.sum().sort_values(ascending=False).round(2).to_string())
    print(f"\n합계: 맑은 날 {sunny.need.sum():.1f}명 / 비 오는 날 {rainy.need.sum():.1f}명")


if __name__ == "__main__":
    main()
