"""auth_mock.json 생성 스크립트 — 최초 1회 또는 비밀번호 변경 시 실행."""

import base64
import hashlib
import json
import os
from pathlib import Path

USERNAME = "baekseok_admin"
PASSWORD = "ilson2026!"
DISPLAY_NAME = "백석농협 공공형 담당자"
ITERATIONS = 260_000

salt = os.urandom(16)
dk = hashlib.pbkdf2_hmac("sha256", PASSWORD.encode(), salt, ITERATIONS)

out = {
    "username": USERNAME,
    "salt": base64.b64encode(salt).decode(),
    "password_hash": dk.hex(),
    "display_name": DISPLAY_NAME,
}

out_path = Path(__file__).resolve().parent / "auth_mock.json"
out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print("생성 완료:", out_path)
