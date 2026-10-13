/**
 * 웹 채팅 API — POST /chat (Bearer).
 * 서버는 engine/chat_server.py 가 Anthropic tool use로 engine 도구를 호출해 답한다.
 * ANTHROPIC_API_KEY 미설정 시 503 → 채팅 위젯에서 "AI 질의 기능이 설정되지 않았습니다"로 표시.
 */
import { apiFetch } from './client.js';

/**
 * @param {Array<{ role: 'user'|'assistant', content: string }>} messages
 * @param {{ mode?: 'demo'|null }} [opts]
 */
export function postChat(messages, { mode } = {}) {
  return apiFetch('/chat', { method: 'POST', body: { messages, mode: mode ?? null } });
}
