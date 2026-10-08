#!/usr/bin/env bash
# API 서버(8000) + React dev 서버(5173) 동시 실행 — Ctrl+C 한 번에 둘 다 종료
set -e
cd "$(dirname "$0")"

uvicorn api_server:app --app-dir engine --port 8000 &
API_PID=$!

(cd dashboard && npm run dev) &
WEB_PID=$!

trap 'kill $API_PID $WEB_PID 2>/dev/null; wait $API_PID $WEB_PID 2>/dev/null' INT TERM
wait
