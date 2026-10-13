"""CP-SAT 날짜별 배정 최적화 — docs/interface.md 2번 JSON 출력.

fair=True 옵션: 요청한 농가에 최소 1명 보장(멘토 QA-10). 가용 인원이 요청 농가 수보다
적어 불가능한 날은 제약을 적용하지 않고 응답의 fairness_applied=False 로 사실을 남긴다.
기본값(fair=False)에서는 기존 동작과 완전히 동일하다.
"""

import json

from ortools.sat.python import cp_model
from scorer import load_data, score_table, load_data as _reload  # noqa: F401


def assign(date, fair=False, workers_df=None):
    workers_src, farms, requests = load_data()
    workers = workers_src if workers_df is None else workers_df
    day_reqs = requests[requests["date"] == date].reset_index(drop=True)
    if day_reqs.empty:
        resp = {
            "date": date,
            "assignments": [],
            "unassigned_workers": sorted(workers["worker_id"]),
            "unmet_requests": [],
        }
        if fair:
            resp["fairness_applied"] = False
            resp["fairness_note"] = "요청 없음"
        return resp
    table = score_table(workers, farms, day_reqs)
    scores = {(r["worker_id"], r["req_id"]): r for _, r in table.iterrows()}

    # 요청 농가 수 vs 가용 인원 — fair 제약 적용 가능 여부 사전 판정
    farms_requesting = sorted(set(day_reqs["farm_id"]))
    fairness_applied = False
    fairness_note = ""
    if fair:
        if len(workers) >= len(farms_requesting):
            fairness_applied = True
        else:
            fairness_note = (
                f"가용 인원 {len(workers)}명이 요청 농가 {len(farms_requesting)}곳보다 적어 "
                "최소 1명 보장을 적용하지 않음"
            )

    model = cp_model.CpModel()
    x = {key: model.new_bool_var(f"x_{key[0]}_{key[1]}") for key in scores}

    # ① 한 근로자는 같은 날짜에 한 농가만
    for wid in workers["worker_id"]:
        model.add(sum(x[wid, rid] for rid in day_reqs["req_id"]) <= 1)

    # ② 요청 headcount 초과 배정 금지
    for _, req in day_reqs.iterrows():
        model.add(
            sum(x[wid, req["req_id"]] for wid in workers["worker_id"]) <= int(req["headcount"])
        )

    # ③ (옵션) 형평성 — 요청 농가는 최소 1명 (가용 인원 ≥ 요청 농가 수일 때만)
    if fairness_applied:
        for fid in farms_requesting:
            farm_reqs = day_reqs[day_reqs["farm_id"] == fid]["req_id"]
            model.add(
                sum(x[wid, rid] for wid in workers["worker_id"] for rid in farm_reqs) >= 1
            )

    # ③ 점수 합 최대화 + 결정성 보장용 타이브레이커
    # 동점 해가 "어느 농가가 부족한가"만 다를 때(근로자 전원 배정) worker_id 만으로는 안
    # 가려져 OS·CPU 에 따라 부족 농가가 달라진다 (환경 간 결정성 — 멘토 QA-05 보강).
    # worker_id 사전순(1차) + 요청 순서(2차)로 완전 정렬. 가중 최대 N*R ≈ 80 ≪ SCALE 라
    # 점수 1점 차이가 뒤집히지 않는다 (10^-4 영향).
    SCALE = 10_000
    wid_rank = {wid: idx for idx, wid in enumerate(sorted(workers["worker_id"]))}
    rid_rank = {rid: idx for idx, rid in enumerate(sorted(day_reqs["req_id"]))}
    N = len(wid_rank)
    R = len(rid_rank)
    model.maximize(
        sum(
            (int(scores[key]["score"]) * SCALE
             + (N - wid_rank[key[0]]) * R
             + (R - rid_rank[key[1]])) * var
            for key, var in x.items()
        )
    )

    solver = cp_model.CpSolver()
    # 결정성 — 같은 입력엔 항상 같은 배정 (멘토 QA P0-5)
    solver.parameters.random_seed = 1
    solver.parameters.num_search_workers = 1
    status = solver.solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(f"배정 실패: solver status={solver.status_name(status)}")

    assignments = []
    assigned_workers = set()
    assigned_count = {rid: 0 for rid in day_reqs["req_id"]}
    for (wid, rid), var in x.items():
        if not solver.value(var):
            continue
        row = scores[wid, rid]
        req = day_reqs[day_reqs["req_id"] == rid].iloc[0]
        farm = farms[farms["farm_id"] == req["farm_id"]].iloc[0]
        assignments.append(
            {
                "worker_id": wid,
                "worker_name": row["name"],
                "farm_id": farm["farm_id"],
                "farm_name": farm["name"],
                "task": req["task"],
                "score": int(row["score"]),
                "reason": row["reason"],
            }
        )
        assigned_workers.add(wid)
        assigned_count[rid] += 1

    assignments.sort(key=lambda a: (a["farm_id"], -a["score"]))
    unmet = [
        {"farm_id": req["farm_id"], "shortage": int(req["headcount"]) - assigned_count[req["req_id"]]}
        for _, req in day_reqs.iterrows()
        if int(req["headcount"]) > assigned_count[req["req_id"]]
    ]
    resp = {
        "date": date,
        "assignments": assignments,
        "unassigned_workers": sorted(set(workers["worker_id"]) - assigned_workers),
        "unmet_requests": unmet,
    }
    # fair 옵션을 명시적으로 요청한 경우에만 메타 필드를 노출 — 기본 응답은 바뀌지 않는다.
    if fair:
        resp["fairness_applied"] = fairness_applied
        if fairness_note:
            resp["fairness_note"] = fairness_note
    return resp


if __name__ == "__main__":
    print(json.dumps(assign("2026-10-14"), ensure_ascii=False, indent=2))
