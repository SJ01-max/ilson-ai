"""CP-SAT 날짜별 배정 최적화 — docs/interface.md 2번 JSON 출력."""

import json

from ortools.sat.python import cp_model
from scorer import load_data, score_table


def assign(date):
    workers, farms, requests = load_data()
    day_reqs = requests[requests["date"] == date].reset_index(drop=True)
    table = score_table(workers, farms, day_reqs)
    scores = {(r["worker_id"], r["req_id"]): r for _, r in table.iterrows()}

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

    # ③ 점수 합 최대화
    model.maximize(sum(int(scores[key]["score"]) * var for key, var in x.items()))

    solver = cp_model.CpSolver()
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
    return {
        "date": date,
        "assignments": assignments,
        "unassigned_workers": sorted(set(workers["worker_id"]) - assigned_workers),
        "unmet_requests": unmet,
    }


if __name__ == "__main__":
    print(json.dumps(assign("2026-10-14"), ensure_ascii=False, indent=2))
