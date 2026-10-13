"""auth_mock.json 생성 스크립트 — 최초 1회 또는 비밀번호 변경 시 실행.

평문 비밀번호를 코드/저장소에 두지 않는다. 실행 방법:
    - 대화형:  python3 engine/gen_auth.py             (getpass 로 비번 2회 입력)
    - 파이프:  echo '…' | python3 engine/gen_auth.py  (stdin 1줄 — CI/스크립트용)

PBKDF2-HMAC-SHA256 260,000회 + 16바이트 솔트.
"""

import base64
import getpass
import hashlib
import json
import sys
from pathlib import Path

USERNAME = "baekseok_admin"
DISPLAY_NAME = "백석농협 공공형 담당자"
ITERATIONS = 260_000


def read_password() -> str:
    """TTY면 getpass 2회 입력(미스타이프 방지), 아니면 stdin 1줄."""
    if sys.stdin.isatty():
        first = getpass.getpass("새 비밀번호: ")
        second = getpass.getpass("확인: ")
        if first != second:
            sys.exit("두 입력이 다릅니다. 다시 실행하세요.")
        return first
    line = sys.stdin.readline().rstrip("\n")
    if not line:
        sys.exit("stdin 으로 비밀번호 1줄을 넘겨주세요. 예: echo '…' | python3 engine/gen_auth.py")
    return line


def main() -> None:
    password = read_password()
    if len(password) < 8:
        sys.exit("비밀번호는 8자 이상이어야 합니다.")
    salt = Path("/dev/urandom").open("rb").read(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    out = {
        "username": USERNAME,
        "salt": base64.b64encode(salt).decode(),
        "password_hash": dk.hex(),
        "display_name": DISPLAY_NAME,
    }
    out_path = Path(__file__).resolve().parent / "auth_mock.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"생성 완료: {out_path}")


if __name__ == "__main__":
    main()
