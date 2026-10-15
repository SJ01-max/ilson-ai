# 일손배정 AI — PRD (현행 반영판)

> 2026 양주시 미래인재 AI 공모전 4팀 (허성재·김새영·유정환)
> 최종 반영된 서비스 기준 — 원안과 달라진 지점은 결정 기록으로 표시.

## 1. 개요

양주시 공공형 계절근로 사업(백석농협)에서 **보유 인력 20명 대비 요청 인력이 날씨·시기에 따라 들쭉날쭉 변동**해, 농가 요청이 몰리면 인력이 모자라고 비 오면 전원이 노는 유휴가 반복된다. 담당자는 이 변동을 사전에 가늠할 지표 없이 매일 배분을 결정한다.

- **대상 사용자**: 농협 공공형 계절근로 담당자 1인 (백석농협 기준). 데모 로그인 계정은 `baekseok_admin`.
- **핵심 가치 제안**: **기상청 단기·중기 예보로 7일 유휴를 추정**(예보 생성 시각을 화면에 표시) + 작목·경력·한국어·거주 가중점수 기반 추천 배정 + 시나리오 비교를 **하나의 웹 대시보드**로 묶고, 담당자가 Claude에게 자연어로 질의할 수 있는 창구(MCP·웹 채팅)를 함께 제공한다. **계산은 로컬 엔진이라 API 비용 없음**; AI 채팅은 선택 기능이다.

## 2. 핵심 기능 (구현 완료 기준)

| 영역 | 구현물 | 수치·근거 |
|---|---|---|
| **유휴 예보** | `forecast/kma_api.py`가 단기(VilageFcst) + 중기(MidFcst)를 **병합**해 7일치 `weekly_rain.csv` 생성 → `forecast/idle.py`가 보정 수요와 결합해 `data/idle_forecast.json` 출력 | 10월 맑은 날 수요 **14명** / 비 오는 날 **8명**, 공급 20명 → **예보 생성 시점 기준 주간 유휴 N인일** (10/10 기준 시연 스냅샷: **42인일·환산액 420만 원**, 일당 10만 원 가정) |
| 수요 보정 모델 | 분모 **중복 집계 교정** + 보정계수 k 적용 | 4,277 × (845+167+422) / 3,039 ≈ **2,018** 농가 (`data/KOSIS/`), **k = 0.82** (시즌 가동률 79.3% → 목표 65% **가정**). 상세 산식은 `docs/calibration.md` |
| 용어 | "손실" 대신 **"유휴 인건비 환산액(예상)"** 통일, 뱃지로 "예보 생성 시각" 또는 "시연 데이터" 노출 | 원안의 "손실" 표현을 제거 — 손익 전체가 아닌 노는 인력 추정치임을 명시 (결정: 2026-10-12) |
| **추천 배정** | `engine/scorer.py` 가중점수 → `engine/assigner.py` **OR-Tools CP-SAT** 최적화 → 사유 문장 포함 | 가중치 (코드 L9~L14, L34~L45 그대로): 작목 일치 **+40**; 경력 **년당 +5**; 한국어는 `korean_level ≥ farm.comm_need`일 때 **+10** (농가 소통 필요도별 기준이 달라짐); 재입국 **+15**·운전 **+15** (단, **작목 무경험자는 두 보너스를 절반 7.5만 인정**); 거주 읍면 일치 **+15** (경험 여부와 무관하게 전액). 제약: 1인 1배정·요청 headcount 상한 |
| 라벨 | **"추천 배정"** (원안 "배정 완료" 아님), 점수에 **"배정 적합도 가중점수"** 툴팁 | 담당자 승인 전제를 UX로 명확히 함 (결정: 담당자가 수정·확정하는 워크플로는 로드맵 이연) |
| **시나리오 비교** | `GET /scenario?workers=&start=&mode=` — `engine/scenario.py`의 `compare()` | 응답 4지표: `idle` / `unmet` / `loss_krw` / `utilization`. workers 5~50, start 생략 시 주 전체 적용 (§5) |
| 기획 보강 | `unmet`(수요 미충족 인일) 필드 **추가** | 원안에는 유휴만. 함정 사례(workers=10 → utilization=1.00인데 unmet=28) 때문에 추가 (결정: 2026-10-12 §5 보완) |
| **AI 질의 — MCP** | `engine/mcp_server.py` stdio, Claude Desktop 등 개인 환경용. 도구 3개: `get_idle_forecast` / `get_assignments` / `compare_scenario` | 핸드셰이크 `protocol=2024-11-05` 확인 |
| **AI 질의 — 웹 채팅** | `engine/chat_server.py` 애드온, Anthropic **tool use**로 위 3개 엔진 도구를 호출. 시스템 프롬프트에 "오늘 날짜·요일 동적 주입" + "숫자는 반드시 도구로 조회" + "마크다운 금지" | `ANTHROPIC_API_KEY` 미설정 시 **/chat만 503**, 나머지 라우트 무영향. **질의당 약 1~2센트 실측** (평균 입력 4k·출력 500토큰, Claude Sonnet 4.6 표준 가격) |
| 결정 | 챗 도구는 시연 토글과 **무관**하게 항상 실데이터 참조 | mode 전달 경로를 모델에 노출하면 숫자 혼선 — 대시보드 전용으로 한정 |
| **보안·운영** | 저장소에는 PBKDF2 해시만 보관하고(260,000회·16B 솔트, `engine/auth_mock.json`), 해시 생성 시 비밀번호는 **실행 중에 입력**받는다(`engine/gen_auth.py` getpass/stdin). 토큰은 서버 메모리 세션. CORS는 `localhost:5173`만 허용 | `/forecast·/assignments·/scenario·/chat` 모두 Bearer 필수. MCP는 로컬 권한 기반(의도된 설계) |
| 기상 원자료 자동 적재 | `.github/workflows/weather-archive.yml` — **매일 KST 07시 예약 실행 + workflow_dispatch** | github-actions[bot]이 `data/weather_history/YYYY-MM-DD_HHMM.csv`에 단기+중기 병합 결과를 적재. **수동 실행으로 end-to-end 검증 완료**(`b3f8b08`). `idle_forecast.json`은 적재 대상에서 **명시적 제외**(시연 수치 42인일 고정) |
| **시연 지원** | 헤더 토글 **"시연: 강수 주간"** (멘토 피드백) | ON → 모든 GET에 `?mode=demo` 자동 부여 → `data/idle_forecast_demo.json`(**54인일·540만 원**) 참조. 뱃지도 "시연 데이터"로 전환. 메모리 전용(새로고침 꺼짐) |
| 데이터 기준 칩 | `generated_at` / `source` 두 필드 추가 (`forecast/idle.py`) | 메타 미보유 JSON에서는 **"10/10 기준 시연 스냅샷"** 폴백 — 기존 파일 재생성 금지 지시 반영 |

## 3. 데이터

| 출처 | 용도 | 비고 |
|---|---|---|
| 기상청 공공데이터포털 (단기 VilageFcst + 중기 MidFcst) | 주간 강수 예보 | 양주시 백석읍 격자 nx=60·ny=132. 강수확률 ≥ 60% 를 "비 오는 날" |
| KOSIS 2025 농림어업총조사 | 양주시 농가 수 4,277 | `data/KOSIS/farm_size.csv` |
| KOSIS 2024 영농형태(주 작목) 표본조사 | 중복 없는 비중 (845/167/422/3,039) | `data/KOSIS/farm_types.csv` |
| KOSIS 2025 vegetable·facility·fruit | 읍면·작목별 면적 | 시설/노지 구분 |
| 작목별 월별 작업 강도 (`crop_calendar.csv`) | 월별 10a당 노동시간 | **가정값 — 출처 미확보**(농진청 자료 확보 실패), k=0.82는 전체 수준만 역산보정 |
| 백석농협 공공형 운영 실적 (**목표 가동률 65% 가정**) | k 역산 기준 | 외부 실증 자료 미확보 — `docs/calibration.md` §3·§5 참조 |

- **가상 인물 데이터 원칙**: `data/workers.csv`는 **가명 20명** (솜싹·분미·캄라 등). 개인정보 미사용. `data/farms.csv`도 "농가 A/B/C" 등 가명 10곳.
- **데모 체계**: `--demo` 모드는 `data/demo_rain.csv`(비 2일 포함 고정) → 54인일·540만 원. 기본 모드와 **별도 파일**로 분리해 시연 중 실데이터가 덮이지 않게 함.
- **민감도 메모**: 주요 가정(분모 2,018·k=0.82·공급 20명) 중 하나를 ±30% 변동시키면 주간 유휴는 대략 **7~70인일** 범위에서 움직인다. 발표 숫자는 "현재 가정 세트의 중간값(42인일, 10/10 기준)"으로 읽어야 한다.

## 4. 검증

### AI 산출물 검증 원칙과 기록

- `docs/ai-log.md`: AI에 시킨 것 → 결과 → **사람이 검증·수정한 것** 3열 포맷을 유지. 각 행에 커밋 해시(또는 이미지 경로)로 증거 연결.
- 10/7 이후 **40행** 기록 — 분모 중복집계 발견, 모델 날짜 오해(2024년) 교정, retire된 모델 교체, assigner 전수탐색 대조 등 **AI 산출물을 그대로 쓰지 않은 사례**가 중심.
- 수치 보고 금지 원칙: "데이터 근거 없는 수치는 발표에 쓰지 않는다"(`docs/baseline-comparison.md` 해석 메모).

### 동일 조건 시뮬레이션 비교(합성 데이터 20명·10곳·4일)

`docs/baseline-comparison.md`의 10/13~16 4일 집계 (최신 수치):

| 지표 | A (단순) | B (CP-SAT 최적화) | 차이 |
|---|---|---|---|
| 요청 충족률 | 0.97 | 0.97 | **+0.00** |
| 작목 경험 일치율 | 0.48 | 0.95 | **+0.47** |
| 읍면 일치율 | 0.26 | 0.66 | **+0.40** |
| 평균 점수 (최대 ~110) | 50.8 | 79.8 | **+29.0** |

- **+29.0 의 해석**: 적합도 점수 규칙(작목+40·경력·한국어·재입국·운전·읍면)의 효과. CP-SAT는 **점수순 탐욕 배정 대비 +1.2점**(실측: 10/13 +0.71, 10/14 +3.25, 10/15·10/16은 양 알고리즘 결과 일치), 4일 모두 CP-SAT solver 의 `OPTIMAL` 상태로 **수학적 최적성 보장**. CP-SAT 를 쓰는 이유는 "최적 보장과 제약(형평성 등) 확장성" — 점수 규칙만 바뀌어도 탐욕은 깨지지만 CP-SAT 는 선언형이라 유지된다.
- 금액·시간 환산은 하지 않음 (근거 데이터 미보유).
- 상세 날짜별: `docs/baseline-comparison.md`.

### 검증 자동화

- 매 변경 후 **npm run build + headless Chrome DOM 측정 + MCP stdio 핸드셰이크 + curl 전구간**을 개발 기간 중 5회의 전 구간 점검으로 반복 통과.
- GitHub Actions 적재는 수동 트리거(`gh workflow run`)로 실제 KMA 호출 → bot 커밋(`b3f8b08`)까지 1회 end-to-end 통과. (정기 cron 실행 기록이 쌓이면 그때 갱신)

## 5. 의도적 범위 제외와 로드맵

**원칙**: 완성도 우선, 측정한 것만 주장. 상태 관리가 필요한 기능은 데모 범위에서 제외.

| 번호 | 로드맵 항목 | 이연 사유 |
|---|---|---|
| 1 | 배정 **검토→수정→확정** 워크플로 (확정본 저장·이력·CSV 출력) | 상태 관리와 담당자 UX 설계가 추가로 필요. 기획안 "담당자 최종 승인"의 완성형 |
| 2 | 결근·요청 취소 대응 **재배정** | 1번의 "확정본" 개념이 전제 |
| 3 | 농가 **요청 등록** 창 | 지금은 `requests.csv` CSV 수기 입력 — UI화하려면 역시 상태 저장 필요 |
| 4 | 예보→배정 **연결** (강수일 클릭 시 해당 날짜 배정 보드로) | 좋은 아이디어지만 데모 완성도에 밀림 |
| 5 | 기상 원자료 **적재 축적 → 예보-실황 대조 → 보정계수 재학습** | `data/weather_history/` 축적부터 시작 (자동 적재는 매일 예약 실행) |
| 6 | **부족 시 농가별 최소 1명 보장**(형평성 제약) | 현재 CP-SAT 는 점수 합만 최대화 — 수요 초과일(10/14·10/21)에는 특정 농가가 0명이 될 수 있음. 운영 피드백 받고 활성화 |

### 알려진 한계

- **형평성 제약은 1차 반영 — 0명 농가만 방지**: `engine/assigner.py` 에 `fair=False` 옵션 추가(`GET /assignments?fair=1`). 현재 구현은 "요청 농가에 최소 1명" 만 보장하므로 **0명 농가 발생은 막지만, 멘토가 지적한 고령 농가 낮은 충족률(예: 요청 3명에 1명만 배정) 은 해결하지 않는다**. 현 데이터셋(20명·10곳) 에서는 CP-SAT 가 점수 최대화만 해도 모든 요청 농가에 1명 이상 분배돼 `fair=True` 가 결과를 바꾸는 날이 11일 중 0일 — 가용 **15명·12명 스트레스 테스트의 10/14 에서만 각 1건 발동** (총점 손실 0). 상세: `docs/fairness-test.md`. UI 토글은 효과가 측정되지 않아 노출하지 않음. **남은 과제(고령 농가 충족률 하한 등)** 는 로드맵 6단계.
- **원단위 가정 의존**: `crop_calendar.csv` 가 바뀌면 월별 모양 전체가 바뀌어 k 재산정 필요.
- **1인 담당자 시나리오**: 다중 사용자·역할 분리는 범위 밖.

- 상세: `docs/feedback-roadmap.md`.
- 측정 가능한 효과만 발표 — 읍면 일치율을 이동시간 절감으로, 작목 일치율을 작업 효율로 **환산하지 않는다** (`docs/baseline-comparison.md` 명시).

## 6. 기술 구성

### 아키텍처 한 눈에

```
┌─ dashboard/ (React 18, Vite)           ─ 웹 UI, http://localhost:5173
│    ├─ api/client.js : Bearer + mode=demo 자동 쿼리
│    ├─ 유휴 예보 / 배정 보드 / 시나리오 비교 3탭
│    └─ 상단 .chat-inline (Claude 창)
│
├─ engine/ (FastAPI, Python 3.11)         ─ 127.0.0.1:8000
│    ├─ api_server.py : /login /forecast /assignments /scenario /chat
│    ├─ scorer.py + assigner.py (OR-Tools CP-SAT, random_seed=1)
│    ├─ scenario.py : §5 compare()
│    ├─ chat_server.py : Anthropic tool use (애드온, 503 분리)
│    └─ mcp_server.py : stdio, Claude Desktop용 도구 3개
│
├─ forecast/ (배치 파이프라인)
│    ├─ kma_api.py : 단기+중기 병합 → weekly_rain.csv + 원자료 스냅샷
│    ├─ demand.py : 작목 면적 × 월별 노동 × k=0.82
│    └─ idle.py : 7일 공급-수요 → idle_forecast(.json / _demo.json)
│
└─ .github/workflows/weather-archive.yml ─ KST 07시 매일 적재 bot 커밋
```

### 로컬 중심 설계 이유

| 결정 | 이유 |
|---|---|
| 계산 서버(FastAPI·엔진)와 LLM 분리 | 질의 트래픽이 늘어도 **배정·예보 응답에 외부 API 비용 없음**. LLM은 "조회 UX" 레이어로만. |
| MCP를 서버에 내장하지 않음 | 담당자 개인 Claude에서 로컬 권한으로 직접 호출. 서버 인증 밖(의도된 설계) |
| 챗 애드온 분리 | `ANTHROPIC_API_KEY` 설정 안 된 환경(심사·시연 Wi-Fi 불안 시)도 **나머지 전부 로컬 동작** |
| 로그인 세션 메모리 저장 | 데모 범위 고정 — 서버 재시작 시 재로그인(의도) |
| `idle_forecast.json`을 CI 봇이 못 건드리게 분리 | 시연 수치 42인일을 **고정** — 매일 자동 갱신으로 발표 전날 숫자가 바뀌는 사고 방지 |

### 실행 방법

```bash
# 사전: .env 파일에 KMA_API_KEY (단기+중기 수집용)과 ANTHROPIC_API_KEY(선택) 입력
pip install -r requirements.txt
cd dashboard && npm install && cd ..

./run.sh    # uvicorn(8000) + vite(5173) 동시 기동, Ctrl+C 한 번에 종료
```

- **접속 주소: `http://localhost:5173`** — `127.0.0.1:5173` 로 접속하면 CORS 가 `localhost:5173` 만 허용하도록 설정돼 있어 /login 호출이 막힌다.
- 데모 데이터 생성: `python3 forecast/idle.py --demo` → `data/idle_forecast_demo.json` (54인일, 토글용)
- 실데이터 재생성: `python3 forecast/kma_api.py && python3 forecast/idle.py` → `data/idle_forecast.json` (당일 아침 운영)
- 로그인: `baekseok_admin` / 비밀번호는 팀 내부 공유(저장소에는 PBKDF2 해시만 존재)
- MCP 등록: Claude Desktop 설정에 `{"mcpServers": {"ilson-ai": {"command": "python3", "args": ["engine/mcp_server.py"]}}}` 추가하면 세 도구가 로드된다.

---

**부속 문서**
- `docs/interface.md` — 데이터 스키마·API 계약 (§2 배정 / §3 예보 / §5 시나리오)
- `docs/calibration.md` — 수요 보정 산식 1페이지
- `docs/baseline-comparison.md` — 단순 배정 vs 최적화 비교 집계
- `docs/feedback-roadmap.md` — 피드백 수용 결정과 로드맵, 멘토 QA 40건 처리 현황
- `docs/demo-checklist.md` — 시연·본선 당일 체크리스트
- `docs/ai-log.md` — AI 활용 기록 (심사 항목 ②, 40행)
