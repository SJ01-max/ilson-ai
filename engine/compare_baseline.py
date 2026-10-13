"""기준선 비교 — (A) 요청 순서 단순 배정 vs (B) assigner(CP-SAT) 최적화.

측정 지표:
- 요청 충족률 = 배정 인원 ÷ 요청 headcount 합계
- 작목 경험 일치율 = 배정 중 작목 경험 보유자 비율
- 같은 읍면 배정률 = 배정 중 농가 읍면 == 근로자 거주 읍면 비율
- 평균 점수 = 배정의 scorer 점수 평균

비용 환산·금액 추정 금지 — 측정 가능한 지표만.
docs/baseline-comparison.md로 저장.
"""

import sys
from collections import defaultdict
from pathlib import Path

ENGINE = Path(__file__).resolve().parent
sys.path.insert(0, str(ENGINE))

from assigner import assign  # noqa: E402
from scorer import load_data, score  # noqa: E402

# 기준선 비교는 10/13~16 네 날짜로 고정 — 이후 추가되는 10/17+ 요청에 영향받지 않게.
# 다른 범위로 돌리고 싶으면 python3 engine/compare_baseline.py 2026-10-17 2026-10-23
DEFAULT_DATES = ["2026-10-13", "2026-10-14", "2026-10-15", "2026-10-16"]
OUTPUT = ENGINE.parent / "docs" / "baseline-comparison.md"


def _parse_date_args(argv: list[str]) -> list[str]:
    """CLI 인자: 시작일 종료일 (YYYY-MM-DD) 두 개. 생략 시 DEFAULT_DATES."""
    if len(argv) < 2:
        return DEFAULT_DATES
    from datetime import date, timedelta
    d0 = date.fromisoformat(argv[0])
    d1 = date.fromisoformat(argv[1])
    out = []
    cur = d0
    while cur <= d1:
        out.append(cur.isoformat())
        cur += timedelta(days=1)
    return out


def _naive_assign(date: str, workers, farms, requests) -> list[dict]:
    """A안: 요청을 req_id 순서로 보고, 아직 그날 미배정인 근로자를 등장 순서로 채운다.

    점수·경험·읍면·headcount 제약은 지키되(headcount 초과 금지, 1인 1배정),
    적합성 평가는 하지 않는다 — "먼저 온 요청·먼저 등장한 근로자" 전략.
    """
    day_reqs = requests[requests["date"] == date].sort_values("req_id")
    worker_order = workers.sort_values("worker_id").to_dict("records")
    assigned_wids: set[str] = set()
    out: list[dict] = []
    for _, req in day_reqs.iterrows():
        farm = farms[farms["farm_id"] == req["farm_id"]].iloc[0]
        taken = 0
        for w in worker_order:
            if taken >= int(req["headcount"]):
                break
            if w["worker_id"] in assigned_wids:
                continue
            assigned_wids.add(w["worker_id"])
            taken += 1
            out.append({
                "worker_id": w["worker_id"],
                "farm_id": farm["farm_id"],
                "farm_name": farm["name"],
                "farm_township": farm["township"],
                "worker_township": w["home_base"],
                "crop": req["crop"],
                "crops_exp": str(w["crops_exp"]).split(";"),
                "score": score(w, farm, req),
            })
    return out


def _opt_assign(date: str, farms, workers) -> list[dict]:
    """B안: assigner.assign() 결과를 비교 포맷으로 변환."""
    res = assign(date)
    farm_map = {f["farm_id"]: f for _, f in farms.iterrows()}
    worker_map = {w["worker_id"]: w for _, w in workers.iterrows()}
    out = []
    for a in res["assignments"]:
        farm = farm_map[a["farm_id"]]
        worker = worker_map[a["worker_id"]]
        out.append({
            "worker_id": a["worker_id"],
            "farm_id": a["farm_id"],
            "farm_name": farm["name"],
            "farm_township": farm["township"],
            "worker_township": worker["home_base"],
            "crop": a["task"] and str(a.get("crop") or ""),
            "crops_exp": str(worker["crops_exp"]).split(";"),
            "score": a["score"],
        })
    return out


def _metrics(assigned: list[dict], requested_headcount: int) -> dict:
    n = len(assigned)
    if n == 0:
        return {
            "assigned": 0,
            "requested": requested_headcount,
            "fulfill_rate": 0.0,
            "crop_match_rate": 0.0,
            "township_match_rate": 0.0,
            "avg_score": 0.0,
        }
    # 작목 경험 일치 = assigner는 req의 crop이 worker.crops_exp에 포함되는지.
    # naive는 각 레코드에 crop을 저장해 둠. assigner 결과도 farm.crops에서 유추 가능하나,
    # 공정 비교 위해 양쪽 모두 "배정 레코드.crop(= 요청의 crop)에 근로자가 경험 있는가" 기준.
    return {
        "assigned": n,
        "requested": requested_headcount,
        "fulfill_rate": round(n / requested_headcount, 2) if requested_headcount else 0.0,
        "crop_match_rate": round(sum(1 for a in assigned if a["crop"] in a["crops_exp"]) / n, 2),
        "township_match_rate": round(sum(1 for a in assigned if a["farm_township"] == a["worker_township"]) / n, 2),
        "avg_score": round(sum(a["score"] for a in assigned) / n, 1),
    }


def _opt_assigned_with_crop(date: str, farms, workers, requests) -> list[dict]:
    """B안의 'crop' 필드를 요청에서 끌어와 공정 비교."""
    res = assign(date)
    farm_map = {f["farm_id"]: f for _, f in farms.iterrows()}
    worker_map = {w["worker_id"]: w for _, w in workers.iterrows()}
    # 요청의 crop 매핑: (farm_id, task) → crop (해당 날짜 기준)
    req_crop = {
        (r["farm_id"], r["task"]): r["crop"]
        for _, r in requests[requests["date"] == date].iterrows()
    }
    out = []
    for a in res["assignments"]:
        farm = farm_map[a["farm_id"]]
        worker = worker_map[a["worker_id"]]
        crop = req_crop.get((a["farm_id"], a["task"]), "")
        out.append({
            "worker_id": a["worker_id"],
            "farm_id": a["farm_id"],
            "farm_name": farm["name"],
            "farm_township": farm["township"],
            "worker_township": worker["home_base"],
            "crop": crop,
            "crops_exp": str(worker["crops_exp"]).split(";"),
            "score": a["score"],
        })
    return out


def run(dates: list[str] | None = None) -> str:
    dates = dates or DEFAULT_DATES
    workers, farms, requests = load_data()
    rows: list[dict] = []
    totals_a: dict = defaultdict(int)
    totals_b: dict = defaultdict(int)
    scores_a: list[int] = []
    scores_b: list[int] = []
    crop_a = crop_b = town_a = town_b = 0

    for date in dates:
        day_reqs = requests[requests["date"] == date]
        requested = int(day_reqs["headcount"].sum())

        a = _naive_assign(date, workers, farms, requests)
        b = _opt_assigned_with_crop(date, farms, workers, requests)
        ma = _metrics(a, requested)
        mb = _metrics(b, requested)

        rows.append({"date": date, "A": ma, "B": mb})

        totals_a["assigned"] += ma["assigned"]
        totals_b["assigned"] += mb["assigned"]
        totals_a["requested"] += requested
        totals_b["requested"] += requested
        scores_a += [x["score"] for x in a]
        scores_b += [x["score"] for x in b]
        crop_a += sum(1 for x in a if x["crop"] in x["crops_exp"])
        crop_b += sum(1 for x in b if x["crop"] in x["crops_exp"])
        town_a += sum(1 for x in a if x["farm_township"] == x["worker_township"])
        town_b += sum(1 for x in b if x["farm_township"] == x["worker_township"])

    def _avg(xs):
        return round(sum(xs) / len(xs), 1) if xs else 0.0

    def _rate(num, den):
        return round(num / den, 2) if den else 0.0

    total_summary = {
        "A": {
            "assigned": totals_a["assigned"],
            "requested": totals_a["requested"],
            "fulfill_rate": _rate(totals_a["assigned"], totals_a["requested"]),
            "crop_match_rate": _rate(crop_a, totals_a["assigned"]),
            "township_match_rate": _rate(town_a, totals_a["assigned"]),
            "avg_score": _avg(scores_a),
        },
        "B": {
            "assigned": totals_b["assigned"],
            "requested": totals_b["requested"],
            "fulfill_rate": _rate(totals_b["assigned"], totals_b["requested"]),
            "crop_match_rate": _rate(crop_b, totals_b["assigned"]),
            "township_match_rate": _rate(town_b, totals_b["assigned"]),
            "avg_score": _avg(scores_b),
        },
    }

    md = _render_md(rows, total_summary)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(md, encoding="utf-8")
    return md


def _render_md(rows, total) -> str:
    def line(d, kind):
        m = d[kind]
        return (
            f"| {d['date']} | {kind} | {m['assigned']}/{m['requested']} | "
            f"{m['fulfill_rate']:.2f} | {m['crop_match_rate']:.2f} | "
            f"{m['township_match_rate']:.2f} | {m['avg_score']:.1f} |"
        )

    body = [
        "# 기준선 비교: 단순 배정(A) vs 최적화(B)",
        "",
        "데이터: `data/workers.csv`(20명)·`farms.csv`(10곳)·`requests.csv`(10/13~16 14건).",
        "",
        "- **A안 (단순 배정)**: 요청을 req_id 순서로 보고 아직 미배정인 근로자를 worker_id 순으로 채운다. 적합성 평가 없음.",
        "- **B안 (CP-SAT 최적화)**: `engine/assigner.py` 결과 — 작목·경력·한국어·재입국·운전·거주 가중치 합산 점수를 최대화.",
        "- 양쪽 모두 1인 1배정·headcount 상한 제약은 동일하게 적용.",
        "- 지표는 측정 가능한 수치만 — 금액·시간 환산은 하지 않는다.",
        "",
        "## 지표 정의",
        "- **요청 충족률** = 배정 인원 ÷ 요청 headcount 합계",
        "- **작목 경험 일치율** = 배정 중 요청 작목(crop)이 근로자 `crops_exp`에 포함된 비율",
        "- **같은 읍면 배정률** = 배정 중 농가 읍면 == 근로자 거주 읍면 비율",
        "- **평균 점수** = `engine/scorer.py` 점수(최대 ~110)의 평균",
        "",
        "## 날짜별",
        "",
        "| 날짜 | 방식 | 배정/요청 | 충족률 | 작목경험 일치율 | 읍면 일치율 | 평균 점수 |",
        "|---|---|---|---|---|---|---|",
    ]
    for d in rows:
        body.append(line(d, "A"))
        body.append(line(d, "B"))
    body += [
        "",
        "## 주간 합계",
        "",
        "| 지표 | A (단순) | B (최적화) | 차이 |",
        "|---|---|---|---|",
    ]
    diffs = {}
    for k in ("fulfill_rate", "crop_match_rate", "township_match_rate", "avg_score"):
        a = total["A"][k]
        b = total["B"][k]
        diffs[k] = round(b - a, 2 if k != "avg_score" else 1)
    body += [
        f"| 배정/요청 | {total['A']['assigned']}/{total['A']['requested']} | {total['B']['assigned']}/{total['B']['requested']} | — |",
        f"| 요청 충족률 | {total['A']['fulfill_rate']:.2f} | {total['B']['fulfill_rate']:.2f} | {diffs['fulfill_rate']:+.2f} |",
        f"| 작목경험 일치율 | {total['A']['crop_match_rate']:.2f} | {total['B']['crop_match_rate']:.2f} | {diffs['crop_match_rate']:+.2f} |",
        f"| 읍면 일치율 | {total['A']['township_match_rate']:.2f} | {total['B']['township_match_rate']:.2f} | {diffs['township_match_rate']:+.2f} |",
        f"| 평균 점수 | {total['A']['avg_score']:.1f} | {total['B']['avg_score']:.1f} | {diffs['avg_score']:+.1f} |",
        "",
        "## 해석 메모",
        "- 충족률이 같은 날에도 **작목 경험 일치율·읍면 일치율·평균 점수**가 다르면, 같은 인원을 배정해도 \"누가 어디로\" 가는지가 다르다는 뜻. 이 차이가 본 시스템이 측정으로 주장할 수 있는 효과.",
        "- 금액(인건비·이동시간)으로 환산하지 않는다 — 데이터 근거가 없는 수치는 발표에 쓰지 않는다.",
    ]
    return "\n".join(body) + "\n"


if __name__ == "__main__":
    print(run(_parse_date_args(sys.argv[1:])))
