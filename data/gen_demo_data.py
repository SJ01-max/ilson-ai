"""데모 데이터 생성 — 근로자 20명·농가 10곳·요청 10/13~16.

새영 합의 완료 (10/12). forecast/는 손대지 않는다 — 수요 보정값은 그대로 재사용.

생성 규칙:
- workers W01~W05: 기존 CSV 그대로 (하위호환).
- workers W06~W20: 라오스 기준 가명, 작목 체계는 기존(배/사과/배추)에서 조합, 경력 1~3, 한국어 1~3,
  재입국 ~40%, 운전 ~25%, 읍면 기존 분포(백석읍·남면·광적면).
- farms F01~F03: 기존 CSV 그대로.
- farms F04~F10: 읍면·작목·comm_need 다양. 고령 농가(70대 이상) 총 2곳 유지(F01이 기존 고령 1곳이므로 F04~F10에 추가 1곳).
- requests 10/13~16: 맑은 날 수요 14명에 맞춰 일별 합계 설계. 10/14는 수요 초과(20명 초과)로 unmet 발생을 유도.
- random.seed(2026)로 재현 가능.
"""

import csv
import random
from pathlib import Path

SEED = 2026
DATA_DIR = Path(__file__).resolve().parent

TOWNSHIP_POOL = ["백석읍", "남면", "광적면"]
CROP_POOL = ["배", "사과", "배추"]

# W06~W20: 라오스 가명 (중복 없는 15개)
LAO_NAMES = [
    "수디", "티다", "매이", "노이", "파이",
    "다우", "씨림", "분탄", "싸이", "껭",
    "툭따", "본레", "펜", "씨엠", "말라",
]

EXISTING_WORKERS = [
    # (worker_id, name, crops_exp, exp_years, korean_level, reentry, can_drive, home_base)
    ("W01", "솜싹", "배;사과", 2, 2, True, False, "백석읍"),
    ("W02", "분미", "배추",     1, 1, False, False, "백석읍"),
    ("W03", "캄라", "배",       3, 2, True,  True,  "남면"),
    ("W04", "톤칸", "사과;배추", 1, 0, False, False, "광적면"),
    ("W05", "완디", "배",       2, 1, True,  False, "남면"),
]

EXISTING_FARMS = [
    # (farm_id, name, township, crops, area_10a, owner_age_group, comm_need)
    ("F01", "고령 농가 A", "남면",   "배",   15, "70대", 2),
    ("F02", "농가 B",      "광적면", "배추",  8, "50대", 1),
    ("F03", "농가 C",      "백석읍", "사과", 12, "60대", 1),
]


def gen_workers(rng: random.Random) -> list[tuple]:
    rows = list(EXISTING_WORKERS)
    for i, name in enumerate(LAO_NAMES, start=6):
        wid = f"W{i:02d}"
        # 작목: 1~2개 조합
        exp_count = rng.choice([1, 1, 2])  # 단일 작목 우세
        crops_exp = ";".join(rng.sample(CROP_POOL, exp_count))
        exp_years = rng.randint(1, 3)
        korean_level = rng.randint(1, 3)
        reentry = rng.random() < 0.40
        can_drive = rng.random() < 0.25
        home_base = rng.choice(TOWNSHIP_POOL)
        rows.append((wid, name, crops_exp, exp_years, korean_level, reentry, can_drive, home_base))
    return rows


def gen_farms(rng: random.Random) -> list[tuple]:
    rows = list(EXISTING_FARMS)
    # F04~F10 = 7곳 추가. 고령 농가 1곳 추가(F01이 기존 고령, 총 2곳 되도록 F04~F10 중 1곳 70대 이상).
    # 다양성: 읍면·작목·comm_need 섞어서 배정
    plans = [
        # (name, township, crops, area_10a, owner_age_group, comm_need)
        ("농가 D",     "남면",   "사과",     10, "40대", 1),
        ("고령 농가 E","백석읍", "배",       18, "80대", 3),  # 추가 고령 (총 2곳 확보)
        ("농가 F",     "광적면", "배;사과",   6, "50대", 2),
        ("농가 G",     "남면",   "배추",     14, "60대", 2),
        ("농가 H",     "백석읍", "배추;사과", 20, "60대", 1),
        ("농가 I",     "광적면", "배",        9, "50대", 1),
        ("농가 J",     "남면",   "사과",     11, "60대", 2),
    ]
    for i, p in enumerate(plans, start=4):
        rows.append((f"F{i:02d}",) + p)
    return rows


def gen_requests() -> list[tuple]:
    """일별 요청 (req_id, farm_id, date, task, crop, headcount).

    맑은 날 수요=14명. 10/13·15·16·17·18·19·20·22·23은 14명 합계,
    10/14·10/21는 수요 초과(20 공급 초과 → unmet 유도). 총 29건 (10/13~23).
    기존 10/13~16 (R001~R014) 는 그대로 — 기준선 비교 소수점까지 보존.
    고령 농가(F01/F05) 는 여러 날에 걸쳐 등장.
    """
    plans = [
        # ── 기존 10/13~16 (R001~R014) 절대 변경 금지 ──
        ("F01", "2026-10-13", "수확", "배",   4),
        ("F03", "2026-10-13", "수확", "사과", 4),
        ("F05", "2026-10-13", "수확", "배",   3),
        ("F07", "2026-10-13", "정리", "배추", 3),
        ("F01", "2026-10-14", "수확", "배",   5),
        ("F02", "2026-10-14", "정리", "배추", 5),
        ("F04", "2026-10-14", "수확", "사과", 6),
        ("F10", "2026-10-14", "수확", "사과", 6),
        ("F03", "2026-10-15", "수확", "사과", 5),
        ("F06", "2026-10-15", "수확", "배",   5),
        ("F08", "2026-10-15", "정리", "배추", 4),
        ("F05", "2026-10-16", "수확", "배",   6),
        ("F09", "2026-10-16", "수확", "배",   4),
        ("F02", "2026-10-16", "정리", "배추", 4),

        # ── 신규 10/17~23 (R015~R029) 본선 당일 보드 공백 방지 ──
        # 10/17 토 (수요 14) ─ 고령 F01 포함
        ("F01", "2026-10-17", "수확", "배",   4),  # 고령 A
        ("F08", "2026-10-17", "정리", "배추", 5),
        ("F09", "2026-10-17", "수확", "배",   5),

        # 10/18 일 (수요 14)
        ("F02", "2026-10-18", "정리", "배추", 4),
        ("F06", "2026-10-18", "수확", "배",   5),
        ("F10", "2026-10-18", "수확", "사과", 5),

        # 10/19 월 (수요 14) ─ 고령 F05 포함
        ("F04", "2026-10-19", "수확", "사과", 5),
        ("F05", "2026-10-19", "수확", "배",   4),  # 고령 E
        ("F07", "2026-10-19", "정리", "배추", 5),

        # 10/20 화 (수요 14) ─ 고령 F01 재등장
        ("F01", "2026-10-20", "수확", "배",   5),  # 고령 A
        ("F03", "2026-10-20", "수확", "사과", 4),
        ("F10", "2026-10-20", "수확", "사과", 5),

        # 10/21 수 (수요 초과 → unmet, 공급 20에 요청 합계 22)
        ("F02", "2026-10-21", "정리", "배추", 6),
        ("F05", "2026-10-21", "수확", "배",   6),  # 고령 E
        ("F04", "2026-10-21", "수확", "사과", 5),
        ("F08", "2026-10-21", "정리", "배추", 5),

        # 10/22 목 (수요 14)
        ("F06", "2026-10-22", "수확", "사과", 4),
        ("F09", "2026-10-22", "수확", "배",   5),
        ("F07", "2026-10-22", "정리", "배추", 5),

        # 10/23 금 (수요 14)
        ("F03", "2026-10-23", "수확", "사과", 5),
        ("F10", "2026-10-23", "수확", "사과", 4),
        ("F02", "2026-10-23", "정리", "배추", 5),
    ]
    return [
        (f"R{i:03d}", farm, date, task, crop, hc)
        for i, (farm, date, task, crop, hc) in enumerate(plans, start=1)
    ]


def write_csv(path: Path, header: list[str], rows: list[tuple]) -> None:
    def fmt(v):
        if isinstance(v, bool):
            return "true" if v else "false"
        return v

    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow([fmt(x) for x in r])


def main() -> None:
    rng = random.Random(SEED)
    workers = gen_workers(rng)
    farms = gen_farms(rng)
    requests = gen_requests()

    write_csv(
        DATA_DIR / "workers.csv",
        ["worker_id", "name", "crops_exp", "exp_years", "korean_level", "reentry", "can_drive", "home_base"],
        workers,
    )
    write_csv(
        DATA_DIR / "farms.csv",
        ["farm_id", "name", "township", "crops", "area_10a", "owner_age_group", "comm_need"],
        farms,
    )
    write_csv(
        DATA_DIR / "requests.csv",
        ["req_id", "farm_id", "date", "task", "crop", "headcount"],
        requests,
    )

    # 요약
    print(f"workers.csv: {len(workers)}명")
    print(f"farms.csv: {len(farms)}곳 (고령 70대+ : {sum(1 for r in farms if r[5] in ('70대','80대'))}곳)")
    by_date: dict[str, int] = {}
    for _, _, date, _, _, hc in requests:
        by_date[date] = by_date.get(date, 0) + hc
    print(f"requests.csv: {len(requests)}건")
    for d, total in sorted(by_date.items()):
        print(f"  {d}: 요청 합계 {total}명")


if __name__ == "__main__":
    main()
