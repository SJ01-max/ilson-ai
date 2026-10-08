"""양주시 계절근로자 유휴 예보·배정 대시보드 (유정환) — docs/interface.md 2·3번 JSON 기준."""

import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

MOCK_DIR = Path(__file__).resolve().parent / "mock"

RED = "#d32f2f"


# 통합일(10/12)에 실제 모듈 호출로 교체
def load_forecast():
    return json.loads((MOCK_DIR / "forecast.json").read_text(encoding="utf-8"))


# 통합일(10/12)에 실제 모듈 호출로 교체
def load_assignments():
    return json.loads((MOCK_DIR / "assignments.json").read_text(encoding="utf-8"))


WEEKDAY = ["월", "화", "수", "목", "금", "토", "일"]


def page_forecast():
    data = load_forecast()
    st.title("유휴 예보")

    days = pd.DataFrame(data["days"])
    total = data["week_total"]
    loss_man = total["loss_krw"] // 10000

    rain = days[days["weather"] == "비"]
    if not rain.empty:
        rain_days = "·".join(WEEKDAY[pd.Timestamp(d).weekday()] for d in rain["date"])
        rain_idle = int(rain["idle"].sum())
        st.markdown(
            f"이번 주 유휴 :red[**{total['idle']}인일**] · 손실 :red[**{loss_man:,}만 원**] — "
            f"이 중 **{rain_days}요일** 강수로 {rain_idle}인일 발생"
        )
    st.caption(f"주 시작일: {data['week_start']}")

    col1, col2 = st.columns(2)
    col1.metric("이번 주 유휴", f"{total['idle']}인일")
    col2.metric("예상 손실", f"{loss_man:,}만 원")

    days["날짜"] = days.apply(
        lambda r: f"{r['date'][5:]} (비)" if r["weather"] == "비" else r["date"][5:],
        axis=1,
    )
    melted = days.melt(id_vars=["날짜"], value_vars=["demand", "idle"], var_name="구분", value_name="인원")
    melted["구분"] = melted["구분"].map({"demand": "투입", "idle": "유휴"})
    melted["순서"] = melted["구분"].map({"투입": 0, "유휴": 1})
    bars = (
        alt.Chart(melted)
        .mark_bar()
        .encode(
            x=alt.X("날짜:N", sort=None),
            y=alt.Y("인원:Q", title="인원(명)"),
            color=alt.Color("구분:N", scale=alt.Scale(domain=["투입", "유휴"], range=["#1f77b4", RED])),
            order=alt.Order("순서:Q"),
        )
    )
    # 비 오는 날 배경 음영 (보유 인력보다 살짝 높게 그려 스택 뒤에서도 보이게)
    shade_df = days[days["weather"] == "비"][["날짜"]].assign(높이=int(days["supply"].max()) + 2)
    shade = (
        alt.Chart(shade_df)
        .mark_bar(opacity=0.15, color="#607d8b")
        .encode(x=alt.X("날짜:N", sort=None), y="높이:Q")
    )
    st.altair_chart(shade + bars, width='stretch')

    table = pd.DataFrame(
        {
            "날짜": days["date"],
            "날씨": days["weather"],
            "필요 인력": days["demand"],
            "보유 인력": days["supply"],
            "유휴": days["idle"],
            "예상 손실": days["loss_krw"].map(lambda v: f"{v // 10000:,}만 원"),
        }
    )
    styled = table.style.set_properties(subset=["유휴", "예상 손실"], color=RED)
    st.dataframe(styled, hide_index=True, width='stretch')


def page_assignments():
    data = load_assignments()
    st.title("배정 보드")
    st.caption(f"배정일: {data['date']}")

    df = pd.DataFrame(data["assignments"])
    for (farm_id, farm_name), group in df.groupby(["farm_id", "farm_name"]):
        st.subheader(f"{farm_name} ({farm_id})")
        for _, row in group.iterrows():
            st.markdown(
                f"- **{row['worker_name']}** ({row['worker_id']}) · {row['task']} · "
                f"{row['score']}점 — {row['reason']}"
            )

    if data["unassigned_workers"]:
        st.warning("미배정 근로자: " + ", ".join(data["unassigned_workers"]))
    for req in data["unmet_requests"]:
        st.warning(f"인력 부족: {req['farm_id']} — {req['shortage']}명 부족")


def page_scenario():
    st.title("시나리오 비교")
    st.slider("입국 인원(명)", min_value=10, max_value=50, value=20)
    st.slider("추가 투입 시기(주 시작일 기준 N일 후)", min_value=1, max_value=30, value=7)
    st.info("엔진 연동 예정 — 통합일(10/12) 이후 시나리오 결과가 여기에 표시됩니다.")


PAGES = {
    "유휴 예보": page_forecast,
    "배정 보드": page_assignments,
    "시나리오 비교": page_scenario,
}

st.set_page_config(page_title="양주시 계절근로자 대시보드", layout="wide")
choice = st.sidebar.radio("화면", list(PAGES))
PAGES[choice]()
