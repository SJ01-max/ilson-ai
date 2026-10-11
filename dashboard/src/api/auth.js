/**
 * 로그인/로그아웃 API (성재 → 정환)
 * POST /login  { username, password } → { token, display_name }
 * POST /logout (Bearer)               → { message }
 * 서버 세션은 메모리 저장이라 서버를 재시작하면 토큰이 무효가 된다 → 401 → 로그인 화면으로 복귀.
 */
import { apiFetch, clearSession, setSession } from './client.js';

/**
 * @param {string} username
 * @param {string} password
 * @returns {Promise<{ token: string, display_name: string }>}
 */
export async function login(username, password) {
  const data = await apiFetch('/login', { method: 'POST', body: { username, password }, auth: false });
  setSession(data);
  return data;
}

export async function logout() {
  try {
    await apiFetch('/logout', { method: 'POST' });
  } finally {
    clearSession();
  }
}
