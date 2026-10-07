# dashboard — 웹 대시보드 (유정환)

Vite + React(JavaScript) + recharts. 화면: ① 유휴 예보 ② 배정 보드 ③ 시나리오 비교

## 실행 방법

Node.js 20 이상 필요 (확인: `node -v`).

```bash
cd dashboard
npm install        # 최초 1회
npm run dev        # http://localhost:5173
```

프로덕션 빌드 확인:

```bash
npm run build      # dist/ 생성
npm run preview    # 빌드 결과 미리보기
```

## 구조

```
dashboard/
├─ index.html
├─ vite.config.js
└─ src/
   ├─ main.jsx                 진입점
   ├─ App.jsx                  상단 탭 (유휴 예보 / 배정 보드 / 시나리오 비교)
   ├─ index.css                전역 스타일 (라이트/다크 토큰)
   ├─ api/                     ★ 데이터 접근은 여기 한 곳에만
   │  ├─ forecast.js           getForecast()          → 지금은 mock/forecast.json
   │  └─ assignments.js        getAssignments(date)   → 지금은 mock/assignments.json
   ├─ mock/                    docs/interface.md §2·§3 JSON 그대로 (필드명 변경 금지)
   │  ├─ forecast.json
   │  └─ assignments.json
   ├─ utils/forecast.js        핵심 문구 생성, 요일/만 원 포맷 등 순수 함수
   ├─ components/
   │  ├─ Tabs.jsx, Placeholder.jsx
   │  └─ forecast/             Headline, SummaryCards, DemandSupplyChart, ForecastTable
   └─ pages/
      ├─ ForecastPage.jsx      화면 1: 유휴 예보 (완성)
      ├─ AssignmentBoardPage.jsx  화면 2: 자리표시 (10/10 구현 예정)
      └─ ScenarioPage.jsx      화면 3: 자리표시 (10/10 구현 예정)
```

## 10/12 통합 시 Mock → 실제 API 교체

화면 컴포넌트는 JSON을 직접 import하지 않고 `src/api/*.js` 함수만 호출한다.
따라서 아래 두 파일의 함수 본문만 `fetch()`로 바꾸면 된다.

```js
// src/api/forecast.js
export async function getForecast() {
  const res = await fetch(`${import.meta.env.VITE_API_BASE}/forecast`);
  if (!res.ok) throw new Error(`forecast ${res.status}`);
  return res.json();
}

// src/api/assignments.js
export async function getAssignments(date) {
  const res = await fetch(`${import.meta.env.VITE_API_BASE}/assignments?date=${date}`);
  if (!res.ok) throw new Error(`assignments ${res.status}`);
  return res.json();
}
```

`VITE_API_BASE`는 `dashboard/.env`에 넣는다 (예: `VITE_API_BASE=http://localhost:8000`).
같은 출처로 프록시하려면 `vite.config.js`의 `server.proxy` 주석을 푼다.

## 화면 1: 유휴 예보 동작

- **핵심 문구**는 하드코딩이 아니라 `buildHeadline(forecast)`가 데이터에서 만든다.
  강수일(`weather`에 비/소나기/눈 포함)을 묶어 요일을 `·`로 잇고, 그 날들의 `idle`·`loss_krw`를 합산한다.
  예) `다음 주 월·화 강수 → 유휴 18인일 → 손실 180만 원`
  - "다음 주/이번 주" 라벨은 `week_start`와 오늘 날짜의 주 차이로 결정된다.
  - 강수일이 없으면 `… 강수 없음 → 유휴 N인일 → 손실 …` 형태로 주간 합계를 보여준다.
- **요약 카드**: `week_total.idle`, `week_total.loss_krw`
- **차트**: 수요(파랑) vs 공급(주황) 막대, 강수일은 배경 밴드 + ☔ 표시
- **표**: 날짜(요일), 날씨, 수요, 공급, 유휴, 손실액(만 원)
