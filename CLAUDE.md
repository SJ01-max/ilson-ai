# ilson-ai 팀 규칙 (Claude Code 전원 공통)

## 폴더 담당
- engine/ → 허성재 (배정 로직, MCP)
- forecast/, data/ → 김새영 (유휴 예보, 데모 데이터)
- dashboard/ → 유정환 (웹 대시보드, 통합)
- 자기 담당이 아닌 폴더는 수정하지 말 것. 수정이 필요하면 수정 전에 보고하고 단톡 합의 후 진행.

## 깃 규칙
- 브랜치는 main 하나만 사용. feature 브랜치 만들지 말 것.
- push 전에 반드시 git pull. rejected 되면 pull 후 다시 push.
- 작업이 끝나면 커밋만 하지 말고 push까지 완료.
- 커밋은 사람이 결과를 확인한 뒤에만. 프롬프트에 "커밋해"가 명시될 때만 수행; 완료 후 "커밋해도 되나요?" 묻지 말 것.
- 한 커밋에 한 종류의 변경만: feat·fix·style·docs를 섞지 않는다. 스타일 작업 중 로직·src/api/ 수정 금지.
- 커밋 메시지 형식: 타입(영역): 한 일 요약 (한글 가능)
  - 타입: feat / fix / chore / docs / style
  - 영역: engine / forecast / dashboard / data
  - 예: feat(forecast): 기상청 API 연동 / fix(dashboard): 유휴 차트 색상 수정

## 절대 금지
- .env 파일 커밋 금지 (API 키 유출 방지)
- docs/interface.md 수정 금지 (셋이 합의한 데이터 약속. 단톡 합의 없이는 손대지 말 것)

## 데이터 약속
- 모든 데이터 입출력은 docs/interface.md의 §2(배정)·§3(예보) JSON 형식을 따를 것. 필드명 임의 변경 금지.
- 형식을 바꿔야 할 것 같으면 바꾸지 말고 보고만.
- 날짜 형식은 YYYY-MM-DD 고정.

## 작업 규칙 (모든 세션 공통)
- 검증은 실제 실행으로: 코드를 수정하면 반드시 실행해서 결과를 보여준다. "될 것이다"로 끝내지 않는다.
- 완료한 작업은 docs/ai-log.md 기록 대상임을 마지막에 상기시킨다.

## 프로젝트 핵심 사실 (헷갈리지 말 것)
- 계산 로직은 engine/에만 있고 FastAPI·MCP 서버는 호출만 한다. LLM은 서버에 내장하지 않는다 (비용 0 설계).
- /forecast는 data/idle_forecast.json을 읽는다 (idle.py 직접 호출 금지 — API 키 의존).
- /forecast·/assignments는 Bearer 토큰 인증 필요. MCP는 인증 밖 (로컬 권한 기반, 의도된 설계).
- 색 체계: 빨강=유휴·손실, 파랑=강수, 틸=수요, 공급=윤곽선. 라이트 모드 기본.
- 날짜·수치 데모 기준: 근로자 20명, 일당 10만 원, 주간 유휴 107인일(보정 전 초안).

## AI 활용 기록 (심사 항목)
- 의미 있는 작업을 마치면 docs/ai-log.md에 한 줄 기록하도록 사용자에게 상기시킬 것.
  (형식은 파일 안 예시 참고, 스크린샷은 docs/ai-log-img/)
