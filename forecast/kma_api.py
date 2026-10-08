"""
양주시 주간 강수 예보 수집기 (유휴 예보 입력용)

- 단기예보 (VilageFcstInfoService_2.0 / getVilageFcst): 오늘 ~ 3일 후
- 중기육상예보 (MidFcstInfoService / getMidLandFcst): 단기예보에 없는 날 ~ 10일 후
- 같은 날짜는 단기예보 우선, 단기예보 강수확률이 비어 있는 날은 중기예보로 채움
- 출력: data/weekly_rain.csv  (date, source, pop_am, pop_pm, pop_max, rain_day)

위치: forecast/kma_api.py
사용법
  1) 레포 루트 .env 에  KMA_API_KEY=발급받은_인증키(Decoding)
  2) 터미널(레포 루트에서):  python forecast/kma_api.py
  3) 결과: data/weekly_rain.csv

※ 발표시각 계산은 서버 시간대와 관계없이 한국시간(Asia/Seoul) 기준.
※ API 오류(인증키 미등록, 트래픽 초과 등) 시 resultMsg 또는 응답 앞부분을 출력하고 종료.
"""
import os, sys
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import requests
import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]      # 레포 루트 (ilson-ai/)
load_dotenv(ROOT / ".env")                      # 루트의 .env 읽기
KEY = os.environ.get("KMA_API_KEY")
if not KEY or "여기에" in KEY:
    sys.exit("루트 .env 파일의 KMA_API_KEY 에 공공데이터포털 인증키(Decoding)를 넣어주세요.")
OUT = ROOT / "data" / "weekly_rain.csv"
KST = ZoneInfo("Asia/Seoul")

# ---- 양주시 설정 ----
NX, NY = 60, 132            # 양주시 백석읍 격자 (활용가이드 엑셀 2607판 기준)
REG_ID = "11B00000"         # 중기육상예보 구역: 서울·인천·경기도
RAIN_THRESHOLD = 60         # 강수확률 ≥ 60% 를 '비 오는 날'로 간주 (조정 가능)

BASE_SHORT = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
BASE_MID   = "https://apis.data.go.kr/1360000/MidFcstInfoService/getMidLandFcst"


def call_api(name, url, params):
    """API 호출 후 items 반환. HTTP 오류·JSON 아님·resultCode != '00' 이면 이유를 출력하고 종료.
    (오류 메시지에 URL을 넣지 않음: 쿼리에 인증키가 포함되어 있음)"""
    r = requests.get(url, params=params, timeout=20)
    if r.status_code != 200:
        sys.exit(f"[{name}] HTTP {r.status_code} 오류 (인증키·트래픽 확인):\n{r.text[:300]}")
    try:
        data = r.json()
    except ValueError:
        sys.exit(f"[{name}] JSON이 아닌 응답 (인증키·파라미터 확인):\n{r.text[:300]}")
    header = data.get("response", {}).get("header", {})
    code = header.get("resultCode")
    if code != "00":
        sys.exit(f"[{name}] API 오류 resultCode={code}: {header.get('resultMsg') or r.text[:300]}")
    return data["response"]["body"]["items"]["item"]


def latest_short_base():
    """단기예보 발표시각(02,05,08,11,14,17,20,23시, KST) 중 조회 가능한 가장 최근 것."""
    now = datetime.now(KST)
    for h in [23, 20, 17, 14, 11, 8, 5, 2]:
        cand = now.replace(hour=h, minute=0, second=0, microsecond=0)
        if now >= cand + timedelta(minutes=10):   # 발표 후 10분 지나야 조회 가능
            return cand.strftime("%Y%m%d"), f"{h:02d}00"
    y = now - timedelta(days=1)
    return y.strftime("%Y%m%d"), "2300"


def fetch_short():
    """단기예보 POP(강수확률)를 날짜별 오전(06~12시)·오후(12~18시) 최댓값으로 집계."""
    base_date, base_time = latest_short_base()
    params = dict(serviceKey=KEY, pageNo=1, numOfRows=1000, dataType="JSON",
                  base_date=base_date, base_time=base_time, nx=NX, ny=NY)
    df = pd.DataFrame(call_api("단기예보", BASE_SHORT, params))
    pop = df[df.category == "POP"].copy()
    pop["value"] = pop["fcstValue"].astype(int)
    pop["hour"] = pop["fcstTime"].str[:2].astype(int)
    rows = []
    for d, g in pop.groupby("fcstDate"):
        am = g[(g.hour >= 6) & (g.hour < 12)]["value"].max()
        pm = g[(g.hour >= 12) & (g.hour < 18)]["value"].max()
        rows.append(dict(date=d, source="short", pop_am=am, pop_pm=pm))
    return pd.DataFrame(rows)


def latest_mid_tmfc():
    """중기예보 발표시각(06시, 18시, KST) 중 조회 가능한 가장 최근 것. 발표 후 30분부터 조회."""
    now = datetime.now(KST) - timedelta(minutes=30)
    if now.hour >= 18:
        return now.strftime("%Y%m%d") + "1800"
    if now.hour >= 6:
        return now.strftime("%Y%m%d") + "0600"
    return (now - timedelta(days=1)).strftime("%Y%m%d") + "1800"


def fetch_mid():
    """중기육상예보 강수확률. 3~7일 후는 오전/오후, 8~10일 후는 하루 단위(오전=오후)."""
    tmfc = latest_mid_tmfc()
    params = dict(serviceKey=KEY, pageNo=1, numOfRows=10, dataType="JSON",
                  regId=REG_ID, tmFc=tmfc)
    item = call_api("중기예보", BASE_MID, params)[0]
    base = datetime.strptime(tmfc[:8], "%Y%m%d")
    rows = []
    for d in range(3, 11):                     # 발표일 기준 3일 후 ~ 10일 후
        date = (base + timedelta(days=d)).strftime("%Y%m%d")
        if d <= 7:
            am, pm = item.get(f"rnSt{d}Am"), item.get(f"rnSt{d}Pm")
        else:
            am = pm = item.get(f"rnSt{d}")
        rows.append(dict(date=date, source="mid", pop_am=am, pop_pm=pm))
    return pd.DataFrame(rows)


def main():
    short = fetch_short()
    mid = fetch_mid()
    # 오전·오후 강수확률이 모두 없는 단기 날짜(예: 그글피)는 버리고 중기로 채움
    short["pop_max"] = short[["pop_am", "pop_pm"]].max(axis=1)
    short = short.dropna(subset=["pop_max"])
    # 단기예보가 있는 날짜는 단기 우선, 나머지는 중기로 채움
    mid = mid[~mid.date.isin(short.date)]
    df = pd.concat([short, mid]).sort_values("date").reset_index(drop=True)
    df["pop_max"] = df[["pop_am", "pop_pm"]].max(axis=1)
    df["rain_day"] = df["pop_max"] >= RAIN_THRESHOLD
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    df.to_csv(OUT, index=False, encoding="utf-8-sig")
    print(df.to_string(index=False))
    print(f"\n→ {OUT} 저장. 비 오는 날(≥{RAIN_THRESHOLD}%): {int(df.rain_day.sum())}일")


if __name__ == "__main__":
    main()
