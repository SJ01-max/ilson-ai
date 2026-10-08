# ilson-ai 팀 규칙 (Claude Code 전원 공통)

## 폴더 담당
- engine/ → 허성재 (배정 로직, MCP)
- forecast/, data/ → 김새영 (유휴 예보, 데모 데이터)
- dashboard/ → 유정환 (웹 대시보드, 통합)
- 내 담당이 아닌 폴더는 수정하지 말 것. 꼭 필요하면 사용자에게 먼저 알리고 단톡 합의 후 진행.

## 깃 규칙
- 브랜치는 main 하나만 사용. feature 브랜치 만들지 말 것.
- push 전에 반드시 git pull. rejected 되면 pull 후 다시 push.
- 작업이 끝나면 커밋만 하지 말고 push까지 완료.
- 커밋 메시지 형식: 타입(영역): 한 일 요약 (한글 가능)
  - 타입: feat / fix / chore / docs
  - 영역: engine / forecast / dashboard / data
  - 예: feat(forecast): 기상청 API 연동 / fix(dashboard): 유휴 차트 색상 수정

## 절대 금지
- .env 파일 커밋 금지 (API 키 유출 방지)
- docs/interface.md 수정 금지 (셋이 합의한 데이터 약속. 단톡 합의 없이는 손대지 말 것)

## 데이터 약속
- 데이터 스키마와 API JSON 형식은 docs/interface.md를 따를 것. 필드명 임의 변경 금지.
- 날짜 형식은 YYYY-MM-DD 고정.

## AI 활용 기록 (심사 항목)
- 의미 있는 작업을 마치면 docs/ai-log.md에 한 줄 기록하도록 사용자에게 상기시킬 것.
  (형식은 파일 안 예시 참고, 스크린샷은 docs/ai-log-img/)
