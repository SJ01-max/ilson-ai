# AI 활용 기록 (심사항목 ② 25점 — 매일 기록)

형식: AI에게 시킨 것 → 결과 → 우리가 검증·수정한 것. 스크린샷은 docs/ai-log-img/에 저장 후 링크.

| 날짜 | 이름 | AI에게 시킨 것 | 결과를 어떻게 검증·수정했나 | 증거 |
|---|---|---|---|---|
| 10/7 | (예시) 허성재 | OR-Tools 배정 제약 코드 초안 생성 | 연속배치 제약이 빠져 있어 직접 추가, 테스트 통과 확인 | img/1007-1.png |
| 10/7 | 허성재 | Claude Code로 scorer.py 생성 | R002에서 무경험자가 보너스만으로 경험자와 동점이 되는 문제를 발견, 경험 없을 시 보너스 절반 감액 규칙을 지시해 수정 | ai-log-img/1007-scorer.png |
| 10/7 | 허성재 | scorer.py 재작성 결과 검토 | Claude가 임의 재작성하며 읍면(거리) 가중치와 사유 문장 생성이 누락된 것을 interface.md와 대조해 발견, 보완 지시 | ai-log-img/1007-scorer2.png |
| 10/8 | 허성재 | Claude Code로 assigner.py 생성 | CP-SAT 결과를 전수 탐색(1024가지)과 대조해 최적값 일치 확인, 수요 초과 케이스를 직접 추가시켜 unmet_requests 동작 검증 | ai-log-img/1008-assigner.png |
| 10/8 | 허성재 | Claude Code로 Streamlit 제거·React 브랜치 머지 | 머지 전후 engine·data·docs 체크섬 대조를 지시해 손상 없음 확인, dashboard 충돌만 React 쪽 선택 | ai-log-img/1008-merge.png |
| 10/8 | 유정환 | 팀 깃 규칙 CLAUDE.md 작성·커밋·push, 규칙 학습 및 AI 로그 기록 자동화 | feature 브랜치 대신 main에 올라갔는지 git log로 확인, 스크린샷은 PowerShell 캡처로 저장 | img/1008-1.png |
| 10/8 | 유정환 | feature/dashboard 브랜치 삭제 요청 (팀 규칙: main 단일 브랜치) | 삭제 전 main에 미병합 커밋이 없는지 git log·--merged로 확인 후 로컬·원격 모두 삭제 | img/1008-2.png |
| 10/8 | 김새영 | forecast: Claude(웹)로 kma_api.py 초안 생성 → Claude Code로 코드 검토 | 격자좌표 미확인·중기예보 공백·저녁 강수 미반영 지적 확인 → 활용가이드 엑셀에서 백석읍 격자(60,132) 추출 적용, 중기예보 공백은 단기예보 우선 로직으로 처리 | (캡처 추가 예정) |
|  |  |  |  |  |
