# 일손배정 AI — 양주시 공공형 계절근로 유휴 예보·배정 플랫폼

2026 양주시 미래인재 AI 공모전 4팀 (허성재 · 김새영 · 유정환)

> 서비스 전체 설명과 설계 결정은 [PRD.md](PRD.md) 를 보세요. 이 문서는 **실행 방법만** 다룹니다.

## 사전 준비

| 항목 | 필요 버전 | 비고 |
|---|---|---|
| Python | 3.11+ | OR-Tools·FastAPI 호환 |
| Node.js | 18+ | Vite 6 요구 |
| macOS/Linux | — | `./run.sh` 는 Bash |

### `.env` 작성 — 루트에 생성

```ini
# 기상청 공공데이터포털에서 발급 (단기·중기 예보)
KMA_API_KEY=발급받은_인증키(Decoding)

# 선택: 웹 채팅 기능용. 설정 안 하면 /chat 만 503, 나머지 기능은 그대로 동작
ANTHROPIC_API_KEY=sk-ant-...
```

### 의존성 설치

```bash
pip install -r requirements.txt
cd dashboard && npm install && cd ..
```

### 로그인 계정 초기화 (최초 1회)

```bash
echo '선택한_비밀번호' | python3 engine/gen_auth.py
# → engine/auth_mock.json 에 PBKDF2 해시만 저장 (평문 미보관)
# username 은 코드 상수 baekseok_admin 고정
```

## 실행

```bash
./run.sh    # uvicorn(127.0.0.1:8000) + vite([::1]:5173) 동시 기동, Ctrl+C 한 번에 종료
```

- **접속: `http://localhost:5173`** — `127.0.0.1:5173` 로 접속하면 서버 CORS 가 `localhost:5173` 만 허용하도록 설정돼 있어 `/login` 호출이 CORS 로 막힙니다.
- 로그인 후 상단에 세 가지 기준점이 뜹니다:
  - **예보 기준 칩**: "예보 생성: M/D HH시 · 기상청 단기·중기예보" 또는 폴백 "10/10 기준 시연 스냅샷"
  - **시연 토글** "시연: 강수 주간" — 켜면 54인일 데모 데이터로 전환
  - **연동 안내** 버튼 — MCP 등록 방법 안내

## 데이터 재생성

```bash
# 당일 아침 운영 — 실 KMA 데이터 반영
python3 forecast/kma_api.py && python3 forecast/idle.py
#   → data/weekly_rain.csv (단기+중기 병합)
#   → data/weather_history/YYYY-MM-DD_HHMM.csv (원자료 스냅샷)
#   → data/idle_forecast.json (유휴 예보, generated_at·source 포함)

# 시연용 고정 데이터 (강수 2일 포함, 54인일)
python3 forecast/idle.py --demo
#   → data/idle_forecast_demo.json  (기본 json 은 덮지 않음)
```

## MCP 등록 (선택)

Claude Desktop 설정 파일에 추가하면 세 가지 도구가 로드됩니다.

```json
{
  "mcpServers": {
    "ilson-ai": {
      "command": "python3",
      "args": ["/절대/경로/ilson-ai/engine/mcp_server.py"]
    }
  }
}
```

도구: `get_idle_forecast` / `get_assignments` / `compare_scenario`. 로컬 권한으로 동작 — 서버 로그인(Bearer) 과 별개.

## 폴더 구조

```
engine/      배정·시나리오 엔진 + API 서버 + MCP (허성재)
forecast/    기상 수집 + 수요 보정 + 유휴 예보 생성 (김새영)
dashboard/   웹 대시보드 React (유정환)
data/        데모 데이터셋·KMA 원자료 적재 디렉터리
docs/        PRD·인터페이스 합의안·보정 근거·AI 활용 기록
.github/     기상 원자료 자동 적재 workflow (KST 07시 cron)
```

## 트러블슈팅

| 증상 | 원인·조치 |
|---|---|
| `/forecast` 503 "forecast 미생성" | `python3 forecast/idle.py` 를 아직 안 돌림. 재생성 섹션 참조. |
| 로그인 "유효하지 않은 토큰" | 서버를 재시작하면 메모리 세션이 날아갑니다. 다시 로그인하세요. |
| 채팅 /chat 503 | `.env` 에 `ANTHROPIC_API_KEY` 가 없음. 설정 후 서버 재기동. |
| KMA 호출 403 `SERVICE_KEY_IS_NOT_REGISTERED_ERROR` | `.env` 의 `KMA_API_KEY` 가 공백·개행 포함이거나 Encoding 키일 수 있음. `forecast/kma_api.py` 는 자동으로 `.strip()` 처리하지만, 공공데이터포털에서 "Decoding" 키인지 확인하세요. |
| 5173 포트 충돌 (다른 프로젝트 Vite) | `lsof -i :5173` 으로 확인하고 종료. Vite 가 다른 포트로 fallback 하면 접속 주소가 바뀝니다. |

## 라이선스·심사용 참고

- `docs/ai-log.md` — 심사 항목 ② (AI 활용 기록). 각 행에 커밋 해시로 증거 연결.
- `docs/calibration.md` — 수요 보정 산식과 한계.
- `docs/baseline-comparison.md` — 단순 배정 vs CP-SAT 최적화 비교.
- `docs/feedback-roadmap.md` — 멘토 피드백 수용 결정과 미반영 사유.
