# 일손배정 AI — 데이터 스키마·API 인터페이스 합의안

> 4팀 (허성재·김새영·유정환) / 2026-10-07
> 목적: 트랙별 병렬 개발을 위한 인터페이스 사전 합의 (병목 방지)
> 회의에서 정할 것: ① 컬럼 추가·삭제 ② 점수 만점 기준(100점?) ③ 날짜 형식 YYYY-MM-DD 고정

---

## 1. 데이터 스키마 (새영 → 성재·정환)

### workers.csv — 근로자 (20명)

| 컬럼 | 타입 | 예시 | 비고 |
|---|---|---|---|
| worker_id | 문자 | W01 | |
| name | 문자 | 솜싹 | 가명 |
| crops_exp | 문자(;구분) | 배;사과 | 경험 작목 |
| exp_years | 숫자 | 2 | 경력 연수 |
| korean_level | 숫자 0~3 | 2 | 0 없음 ~ 3 상 |
| reentry | 불리언 | true | 재입국 여부 |
| can_drive | 불리언 | false | |
| home_base | 문자 | 백석읍 | 숙소 위치(읍면) |

### farms.csv — 농가 (10곳)

| 컬럼 | 타입 | 예시 | 비고 |
|---|---|---|---|
| farm_id | 문자 | F01 | |
| name | 문자 | 고령 농가 A | |
| township | 문자 | 남면 | 읍면 |
| crops | 문자(;구분) | 배 | 재배 작목 |
| area_10a | 숫자 | 15 | 면적(10a 단위) |
| owner_age_group | 문자 | 70대 | 고령 여부 판단용 |
| comm_need | 숫자 0~3 | 2 | 소통 필요도(높을수록 한국어 필요) |

### requests.csv — 요청 이력

| 컬럼 | 타입 | 예시 |
|---|---|---|
| req_id | 문자 | R001 |
| farm_id | 문자 | F01 |
| date | 날짜 | 2026-10-14 |
| task | 문자 | 수확 |
| crop | 문자 | 배 |
| headcount | 숫자 | 3 |

---

## 2. 배정 API 응답 JSON (성재 → 정환)

```json
{
  "date": "2026-10-14",
  "assignments": [
    {
      "worker_id": "W01",
      "worker_name": "솜싹",
      "farm_id": "F01",
      "farm_name": "고령 농가 A",
      "task": "수확",
      "score": 87,
      "reason": "배 수확 경험 2년·한국어 중급 → 고령 농가 A 우선"
    }
  ],
  "unassigned_workers": ["W07", "W12"],
  "unmet_requests": [{ "farm_id": "F09", "shortage": 1 }]
}
```

---

## 3. 유휴 예보 응답 JSON (새영 → 정환)

```json
{
  "week_start": "2026-10-12",
  "days": [
    { "date": "2026-10-13", "weather": "비", "demand": 2, "supply": 20, "idle": 18, "loss_krw": 1800000 },
    { "date": "2026-10-14", "weather": "맑음", "demand": 17, "supply": 20, "idle": 3, "loss_krw": 300000 }
  ],
  "week_total": { "idle": 21, "loss_krw": 2100000 }
}
```

---

## 4. 개발 착수용 Mock 샘플 (성재용)

```csv
# workers.csv
worker_id,name,crops_exp,exp_years,korean_level,reentry,can_drive,home_base
W01,솜싹,배;사과,2,2,true,false,백석읍
W02,분미,배추,1,1,false,false,백석읍
W03,캄라,배,3,2,true,true,남면
W04,톤칸,사과;배추,1,0,false,false,광적면
W05,완디,배,2,1,true,false,남면

# farms.csv
farm_id,name,township,crops,area_10a,owner_age_group,comm_need
F01,고령 농가 A,남면,배,15,70대,2
F02,농가 B,광적면,배추,8,50대,1
F03,농가 C,백석읍,사과,12,60대,1
```

---

## 5. 시나리오 비교 응답 JSON (성재 → 정환)

입국 인원·추가 투입 시기를 바꿨을 때의 주간 유휴·부족·유휴 인건비 환산액 변화를 비교.
수요는 §3 예보의 보정값(`data/idle_forecast.json`의 `days[].demand`)을 그대로 재사용 — 이중 계산 금지.

```json
{
  "base":     { "workers": 20, "start": null,         "idle": 42, "unmet": 0, "loss_krw": 4200000, "utilization": 0.70 },
  "scenario": { "workers": 30, "start": "2027-04-01", "idle": 42, "unmet": 0, "loss_krw": 4200000, "utilization": 0.70 },
  "diff":     { "idle": 0, "unmet": 0, "loss_krw": 0 }
}
```

- `base.workers`: 20명 고정 (현재 공공형 투입 인원). `base.start`: `null`.
- `scenario.workers`: 입국 인원(5~50 범위, 밖이면 ValueError). `scenario.start`: `YYYY-MM-DD` 또는 `null`.
  - `start`가 `null` 또는 주 시작(§3 `week_start`) 이전 → 주 전체 `supply = workers`.
  - `start`가 주 중간 → 그 날짜부터 `workers`, 이전 날짜는 `base`의 20명.
  - `start`가 주 끝(마지막 날짜) 이후 → 주 전체 영향 없음 (scenario = base).
- `idle` = 주간 `max(supply − demand, 0)` 합계 (유휴 인일).
- `unmet` = 주간 `max(demand − supply, 0)` 합계 (수요 미충족 인일). **`utilization`이 높아도 `unmet>0`이면 수요 미충족 상태** — 두 지표를 함께 봐야 한다.
- `utilization` = `투입인일 ÷ 공급인일` (주간 합계, 소수 둘째 자리). `투입인일 = min(supply, demand)`, `공급인일 = supply`.
- `loss_krw` = `idle × 100000` — **유휴 인건비 환산액**(일당 10만 원 가정). 실제 손익 전체가 아니라, 노는 인력에 지급되는 인건비 추정치.
- `diff = scenario − base` (`idle`·`unmet`·`loss_krw` 모두 음수면 개선 방향).

---

## 합의 후 각자 시작점

- **허성재:** 위 Mock으로 점수화 + OR-Tools 배정 로직 → 2번 JSON 형식으로 출력
- **김새영:** 1번 스키마대로 20명·10곳 생성 스크립트 + 기상청 API 연동 → 3번 JSON 출력
- **유정환:** 2·3번 JSON 하드코딩으로 대시보드 화면 즉시 착수
- **통합일: 10/12** — Mock을 실제 API로 교체
