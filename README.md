# 일손배정 AI — 양주시 공공형 계절근로 유휴 예보·배정 플랫폼

2026 양주시 미래인재 AI 공모전 4팀 (허성재 · 김새영 · 유정환)

## 구조
```
/engine      배정 엔진 + MCP 서버 (성재)
/forecast    데이터 파이프라인 + 유휴 예보 (새영)
/dashboard   웹 대시보드 (정환)
/data        데모 데이터셋 (CSV)
/docs        인터페이스 합의안, AI 활용 기록
```

## 시작하기
1. `.env.example`을 복사해 `.env` 생성 후 기상청 API 키 입력
2. `pip install -r requirements.txt`
3. 각 트랙 폴더의 README 참고

## 인터페이스
`docs/interface.md` 참고 — 변경 시 반드시 단톡 공유 후 수정

## 일정
- 10/12 통합 / 10/13 시연 영상 / 10/15 발표자료 제출 / 10/17 본선
