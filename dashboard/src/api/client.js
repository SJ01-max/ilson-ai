/**
 * API 공통 클라이언트 — 토큰 보관, Bearer 헤더, 오류 변환.
 * 서버: engine/api_server.py (FastAPI, 기본 http://localhost:8000, ./run.sh 로 기동)
 * 응답 형식은 docs/interface.md §2·§3 그대로 통과시킨다 (여기서 가공하지 않음).
 */

export const API_BASE = (import.meta.env.VITE_API_BASE ?? 'http://localhost:8000').replace(/\/$/, '');

const TOKEN_KEY = 'ilson.token';
const NAME_KEY = 'ilson.display_name';

/** 세션 만료(401) 시 App이 로그인 화면으로 돌리도록 알리는 이벤트 이름 */
export const UNAUTHORIZED_EVENT = 'ilson:unauthorized';

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

export function getToken() {
  try {
    return sessionStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function getDisplayName() {
  try {
    return sessionStorage.getItem(NAME_KEY);
  } catch {
    return null;
  }
}

export function setSession({ token, display_name }) {
  try {
    sessionStorage.setItem(TOKEN_KEY, token);
    sessionStorage.setItem(NAME_KEY, display_name ?? '');
  } catch {
    /* 저장소 불가 환경(시크릿 모드 등)에서는 메모리 상태만 유지 */
  }
}

export function clearSession() {
  try {
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(NAME_KEY);
  } catch {
    /* noop */
  }
}

/**
 * fetch 래퍼. 토큰이 있으면 Authorization 헤더를 붙이고, 오류는 ApiError로 통일한다.
 * - 네트워크 실패(서버 꺼짐): status 0
 * - 401: 세션을 지우고 UNAUTHORIZED_EVENT 발행 → App이 로그인 화면으로 전환
 * @param {string} path '/forecast' 처럼 슬래시로 시작
 * @param {{ method?: string, body?: object, auth?: boolean }} [opts]
 */
export async function apiFetch(path, { method = 'GET', body, auth = true } = {}) {
  const headers = {};
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  const token = auth ? getToken() : null;
  if (token) headers.Authorization = `Bearer ${token}`;

  let res;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(0, `API 서버(${API_BASE})에 연결할 수 없습니다. ./run.sh 실행 여부를 확인하세요.`);
  }

  if (res.status === 401 && auth) {
    clearSession();
    window.dispatchEvent(new CustomEvent(UNAUTHORIZED_EVENT));
  }

  if (!res.ok) {
    let detail = '';
    try {
      const data = await res.json();
      detail = typeof data?.detail === 'string' ? data.detail : JSON.stringify(data?.detail ?? data);
    } catch {
      /* 본문이 JSON이 아니면 상태 코드만 */
    }
    throw new ApiError(res.status, detail || `${method} ${path} → ${res.status}`);
  }

  return res.json();
}
