# dashboard — 웹 대시보드 (유정환)

Vite + React(JavaScript) + recharts. 화면: ⓪ 로그인 ① 유휴 예보 ② 배정 보드 ③ 시나리오 비교

## 실행 방법

Node.js 20 이상 필요 (확인: `node -v`). API 서버(FastAPI, 8000)가 함께 떠 있어야 데이터가 보인다.

```bash
# 저장소 루트에서 — API(8000) + React(5173) 동시 실행
./run.sh

# 대시보드만 따로
cd dashboard
npm install        # 최초 1회
npm run dev        # http://localhost:5173
```

프로덕션 빌드 확인:

```bash
npm run build      # dist/ 생성
npm run preview    # 빌드 결과 미리보기
```

API 주소는 기본 `http://localhost:8000`. 바꾸려면 `dashboard/.env`에 `VITE_API_BASE=...` (`.env`는 커밋 금지).

## 로그인

- 서버 `POST /login` (engine/api_server.py) 으로 인증. 계정은 `engine/auth_mock.json` (해시+솔트), 비밀번호는 `engine/gen_auth.py` 참고.
- 토큰은 브라우저 `sessionStorage`에 보관하고 모든 요청에 `Authorization: Bearer` 로 붙인다.
- 서버 세션은 메모리 저장이라 **서버를 재시작하면 토큰이 무효**가 된다 → 다음 요청이 401 → 자동으로 로그인 화면으로 돌아간다.
- MCP(Claude 연동)는 로그인 밖에서 동작한다 (로컬 권한 기반, 의도된 설계).

## 구조

```
dashboard/
├─ index.html
├─ vite.config.js
└─ src/
   ├─ main.jsx                 진입점
   ├─ App.jsx                  로그인 게이트 + 상단 탭 (유휴 예보 / 배정 보드 / 시나리오 비교)
   ├─ index.css                전역 스타일 (라이트 기본, 다크 토큰, 375px 반응형)
   ├─ api/                     ★ 데이터 접근은 여기 한 곳에만 (화면은 JSON을 직접 다루지 않음)
   │  ├─ client.js             fetch 래퍼: API_BASE, Bearer 토큰, 401 → 로그인 복귀 이벤트
   │  ├─ auth.js               login(username, password) / logout()
   │  ├─ forecast.js           getForecast()          → GET /forecast      (interface.md §3)
   │  └─ assignments.js        getAssignments(date)   → GET /assignments   (interface.md §2)
   ├─ utils/
   │  ├─ forecast.js           핵심 문구 생성, 요일/만 원 포맷 등 순수 함수
   │  ├─ assignments.js        농가별 묶기, 요약 수치, 날짜 유틸
   │  └─ scenario.js           시나리오 임시 추정 (엔진 연결 전 화면 확인용)
   ├─ components/
   │  ├─ Tabs.jsx
   │  ├─ forecast/             Headline, SummaryCards, DemandSupplyChart, ForecastTable
   │  ├─ board/                BoardSummary, FarmCard
   │  └─ scenario/             ScenarioChart
   └─ pages/
      ├─ LoginPage.jsx         화면 0: 로그인
      ├─ ForecastPage.jsx      화면 1: 유휴 예보
      ├─ AssignmentBoardPage.jsx  화면 2: 배정 보드
      └─ ScenarioPage.jsx      화면 3: 시나리오 비교 (계산은 엔진 대기)
```

`src/mock/`과 `components/Placeholder.jsx`는 실데이터 연결 후 더 이상 참조하지 않는다 (삭제 예정).

## 색 체계 (팀 합의 — 바꾸지 말 것)

빨강 = 유휴·손실 / 파랑 = 강수 / 틸 = 수요 / 공급 = 윤곽선 빈 막대. 라이트 모드 기본, 다크는 헤더 토글.

## 화면 1: 유휴 예보

- **핵심 문구**는 `buildHeadline(forecast)`가 데이터에서 만든다.
  강수일(`weather`에 비/소나기/눈 포함)을 묶어 요일을 `·`로 잇고, 그 날들의 `idle`·`loss_krw`를 합산한다.
  예) `다음 주 월·화 강수 → 유휴 18인일 → 손실 180만 원`
  - 강수일이 없으면 `… 강수 없음 → 유휴 N인일 → 손실 …` 형태로 주간 합계를 보여준다.
- **요약 카드**: `week_total.idle`, `week_total.loss_krw`
- **차트**: 수요(틸) vs 공급(윤곽선) 막대, 강수일은 파랑 밴드, 막대 위 숫자 = 유휴
- **표**: 날짜(요일), 날씨, 수요, 공급, 유휴, 손실액(만 원)

## 화면 2: 배정 보드

- 날짜 선택(달력 + 오늘부터 7일 빠른 선택) → `getAssignments(date)`.
- 섹션 순서는 **요약 → 상세**: ① 배정 완료·미배정(빨강)·인력 부족(빨강) 타일 + 한 줄 결론
  ② 농가별 카드(근로자 이름·점수·사유 문장, 부족 인원 칩) ③ 미배정 근로자 ID·부족 요청 목록.
- 요청이 없는 날짜는 "농가 요청 없음 · 전원 미배정" 상태로 보여준다 (data/requests.csv 기준).

## 화면 3: 시나리오 비교

- 슬라이더 2개: 입국 인원(5~40명), 투입 시작일(예보 기간 내).
- 결과 영역: 현재 vs 시나리오 요약 타일(유휴·손실·부족) + 시나리오 문장 + 일별 유휴 비교 차트 + 표.
- **수치는 `utils/scenario.js`의 임시 추정**(투입일 이후 supply = 입국 인원, idle = max(supply − demand, 0)).
  성재의 `compare_scenario` 엔진이 올라오면 `ScenarioPage.jsx`의 `estimateScenario()` 호출 한 곳만 API로 바꾼다.
  응답 JSON 형식은 interface.md에 아직 없으므로 단톡 합의 후 추가.
