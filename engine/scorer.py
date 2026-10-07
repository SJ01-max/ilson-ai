"""근로자 × 요청 점수화 — docs/interface.md 스키마 기준."""

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

CROP_MATCH = 40
EXP_YEAR = 5
KOREAN_OK = 10
REENTRY_BONUS = 15
DRIVE_BONUS = 15
TOWNSHIP_MATCH = 15

KOREAN_LABEL = {0: "없음", 1: "초급", 2: "중급", 3: "상급"}


def load_data():
    workers = pd.read_csv(DATA_DIR / "workers.csv")
    farms = pd.read_csv(DATA_DIR / "farms.csv")
    requests = pd.read_csv(DATA_DIR / "requests.csv")
    return workers, farms, requests


def score(worker, farm, request):
    crops_exp = str(worker["crops_exp"]).split(";")
    crop_match = request["crop"] in crops_exp

    # 작목 무경험자는 재입국·운전 보너스를 절반만 인정 (경험자 우위 보장)
    bonus_rate = 1.0 if crop_match else 0.5

    total = 0.0
    if crop_match:
        total += CROP_MATCH
    total += int(worker["exp_years"]) * EXP_YEAR
    if int(worker["korean_level"]) >= int(farm["comm_need"]):
        total += KOREAN_OK
    if worker["reentry"]:
        total += REENTRY_BONUS * bonus_rate
    if worker["can_drive"]:
        total += DRIVE_BONUS * bonus_rate
    # 거리 제약: 같은 읍면 가중치는 경험 여부와 무관하게 전액 인정
    if worker["home_base"] == farm["township"]:
        total += TOWNSHIP_MATCH
    return round(total)


def make_reason(worker, farm, request):
    crops_exp = str(worker["crops_exp"]).split(";")
    parts = []
    if request["crop"] in crops_exp:
        parts.append(f"{request['crop']} {request['task']} 경험 {int(worker['exp_years'])}년")
    else:
        parts.append(f"{request['crop']} 경험 없음")
    if int(worker["korean_level"]) >= int(farm["comm_need"]):
        parts.append(f"한국어 {KOREAN_LABEL[int(worker['korean_level'])]}")
    if worker["reentry"]:
        parts.append("재입국")
    if worker["can_drive"]:
        parts.append("운전 가능")
    if worker["home_base"] == farm["township"]:
        parts.append(f"{farm['township']} 거주")
    return "·".join(parts) + f" → {farm['name']} 우선"


def score_table(workers, farms, requests):
    rows = []
    for _, req in requests.iterrows():
        farm = farms[farms["farm_id"] == req["farm_id"]].iloc[0]
        for _, worker in workers.iterrows():
            rows.append(
                {
                    "req_id": req["req_id"],
                    "crop": req["crop"],
                    "worker_id": worker["worker_id"],
                    "name": worker["name"],
                    "score": score(worker, farm, req),
                    "reason": make_reason(worker, farm, req),
                }
            )
    df = pd.DataFrame(rows)
    return df.sort_values(["req_id", "score"], ascending=[True, False]).reset_index(drop=True)


if __name__ == "__main__":
    workers, farms, requests = load_data()
    table = score_table(workers, farms, requests)
    for req_id, group in table.groupby("req_id"):
        print(f"\n=== {req_id} ({group.iloc[0]['crop']}) ===")
        print(group[["worker_id", "name", "score", "reason"]].to_string(index=False))
